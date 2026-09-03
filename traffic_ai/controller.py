"""
AI Traffic Signal Controller.
Implements Dynamic Green Phase Allocation, Density-Based Scheduling,
and Emergency Vehicle Preemption.
"""

from enum import Enum
from typing import Dict
from traffic_ai.intersection import Intersection, LightState, TrafficPhase
from traffic_ai.vehicle import Direction
from traffic_ai.vision_detector import LaneTelemetry


class ControlMode(Enum):
    AI_ADAPTIVE = "AI Adaptive (Smart)"
    FIXED_TIMER = "Fixed Timer (Classic)"
    EMERGENCY_PREEMPTION = "Emergency Corridor"


class TrafficController:
    """
    Intelligent Agent controlling traffic signals based on vision telemetry.
    """

    def __init__(
        self,
        intersection: Intersection,
        mode: ControlMode = ControlMode.AI_ADAPTIVE,
        min_green: float = 6.0,
        max_green: float = 28.0,
        yellow_time: float = 3.0,
        fixed_green: float = 14.0,
    ):
        self.intersection = intersection
        self.mode = mode
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        self.fixed_green = fixed_green

        # Current phase state
        self.active_phase: TrafficPhase = TrafficPhase.NORTH_SOUTH
        self.light_state: LightState = LightState.GREEN
        self.phase_time_elapsed: float = 0.0
        self.current_green_target: float = min_green
        
        # Emergency preemption state
        self.emergency_phase: bool = False
        self.emergency_direction: Direction = None

        # Statistics & telemetry logs
        self.total_phase_switches: int = 0
        self.ai_decisions_log: list = []
        
        # Apply initial lights
        self.intersection.set_phase_lights(self.active_phase, self.light_state)

    def calculate_phase_demand(self, telemetry: Dict[Direction, LaneTelemetry], phase: TrafficPhase) -> float:
        """
        Calculates the urgency/demand score for a phase (combined load + wait penalties).
        Formula: Demand = sum(load * 1.5 + avg_wait * 1.8 + waiting_count * 2.0)
        """
        dirs = [Direction.NORTH, Direction.SOUTH] if phase == TrafficPhase.NORTH_SOUTH else [Direction.EAST, Direction.WEST]
        demand = 0.0
        for d in dirs:
            t = telemetry[d]
            demand += (t.weighted_load * 1.5) + (t.avg_wait_time * 1.8) + (t.waiting_count * 2.5)
        return demand

    def calculate_optimal_green_duration(self, telemetry: Dict[Direction, LaneTelemetry], phase: TrafficPhase) -> float:
        """
        AI algorithm to allocate green time based on real-time vehicle density.
        """
        dirs = [Direction.NORTH, Direction.SOUTH] if phase == TrafficPhase.NORTH_SOUTH else [Direction.EAST, Direction.WEST]
        max_vehicles_in_lane = max(telemetry[dirs[0]].vehicle_count, telemetry[dirs[1]].vehicle_count)
        max_wait = max(telemetry[dirs[0]].avg_wait_time, telemetry[dirs[1]].avg_wait_time)
        
        # Base formula: 2.2 seconds per queued vehicle + penalty for long waiting
        extra_time = (max_vehicles_in_lane * 2.0) + (max_wait * 0.8)
        optimal = self.min_green + extra_time
        return max(self.min_green, min(self.max_green, optimal))

    def step(self, dt: float, telemetry: Dict[Direction, LaneTelemetry]):
        """
        Simulation tick logic. Updates timers and executes signal transitions.
        """
        self.phase_time_elapsed += dt

        # 1. Check for Emergency Preemption
        emergency_dir = None
        for d, t in telemetry.items():
            if t.emergency_present:
                emergency_dir = d
                break

        if emergency_dir:
            self._handle_emergency(emergency_dir, dt)
            return

        # If emergency was active but cleared, return to adaptive control
        if self.emergency_phase:
            self.emergency_phase = False
            self.emergency_direction = None
            self.mode = ControlMode.AI_ADAPTIVE
            self._log_decision("Emergency vehicle cleared. Restoring AI Adaptive control.")
            self._transition_to_yellow()
            return

        # 2. Normal Phase Execution (AI or Fixed)
        if self.light_state == LightState.GREEN:
            # Determine green target time
            if self.mode == ControlMode.AI_ADAPTIVE:
                # Early termination condition:
                # If minimum green is met, current phase has 0 waiting vehicles, and alternate has high demand -> switch early!
                current_dirs = [Direction.NORTH, Direction.SOUTH] if self.active_phase == TrafficPhase.NORTH_SOUTH else [Direction.EAST, Direction.WEST]
                curr_vehicles = sum(telemetry[d].vehicle_count for d in current_dirs)
                alt_demand = self.calculate_phase_demand(telemetry, self.active_phase.alternate)

                if self.phase_time_elapsed >= self.min_green:
                    if curr_vehicles == 0 and alt_demand > 0:
                        self._log_decision(f"AI Early Clear: {self.active_phase.value} empty -> Triggering switch to {self.active_phase.alternate.value}")
                        self._transition_to_yellow()
                        return

                if self.phase_time_elapsed >= self.current_green_target:
                    self._transition_to_yellow()
                    return
            else:
                # Fixed timer mode
                if self.phase_time_elapsed >= self.fixed_green:
                    self._transition_to_yellow()
                    return

        elif self.light_state == LightState.YELLOW:
            if self.phase_time_elapsed >= self.yellow_time:
                self._switch_phase(telemetry)

    def _handle_emergency(self, priority_dir: Direction, dt: float):
        """Preempts signals to clear passage for emergency vehicle."""
        target_phase = TrafficPhase.NORTH_SOUTH if priority_dir in (Direction.NORTH, Direction.SOUTH) else TrafficPhase.EAST_WEST

        if not self.emergency_phase:
            self.emergency_phase = True
            self.emergency_direction = priority_dir
            self._log_decision(f"[!] EMERGENCY OVERRIDE: Siren detected in {priority_dir.value}. Preempting signals.")

        # If we are not in the emergency vehicle's phase, cycle through yellow immediately
        if self.active_phase != target_phase:
            if self.light_state == LightState.GREEN:
                self._transition_to_yellow()
            elif self.light_state == LightState.YELLOW and self.phase_time_elapsed >= self.yellow_time:
                self.active_phase = target_phase
                self.light_state = LightState.GREEN
                self.phase_time_elapsed = 0.0
                self.current_green_target = self.max_green
                self.intersection.set_phase_lights(self.active_phase, LightState.GREEN)
        else:
            # Already in emergency phase: keep green
            self.light_state = LightState.GREEN
            self.intersection.set_phase_lights(self.active_phase, LightState.GREEN)

    def _transition_to_yellow(self):
        """Moves current active phase into yellow transition."""
        self.light_state = LightState.YELLOW
        self.phase_time_elapsed = 0.0
        self.intersection.set_phase_lights(self.active_phase, LightState.YELLOW)

    def _switch_phase(self, telemetry: Dict[Direction, LaneTelemetry]):
        """Switches active phase to alternate corridor and computes new green duration."""
        self.active_phase = self.active_phase.alternate
        self.light_state = LightState.GREEN
        self.phase_time_elapsed = 0.0
        self.total_phase_switches += 1

        if self.mode == ControlMode.AI_ADAPTIVE:
            self.current_green_target = self.calculate_optimal_green_duration(telemetry, self.active_phase)
            alt_demand = self.calculate_phase_demand(telemetry, self.active_phase)
            self._log_decision(
                f"AI Assigned {self.active_phase.value} GREEN for {self.current_green_target:.1f}s (Demand Score: {alt_demand:.1f})"
            )
        else:
            self.current_green_target = self.fixed_green

        self.intersection.set_phase_lights(self.active_phase, LightState.GREEN)

    def _log_decision(self, message: str):
        self.ai_decisions_log.append(message)
        if len(self.ai_decisions_log) > 50:
            self.ai_decisions_log.pop(0)

    def get_remaining_time(self) -> float:
        """Returns countdown seconds remaining for the current light state."""
        if self.light_state == LightState.GREEN:
            return max(0.0, self.current_green_target - self.phase_time_elapsed)
        elif self.light_state == LightState.YELLOW:
            return max(0.0, self.yellow_time - self.phase_time_elapsed)
        return 0.0
