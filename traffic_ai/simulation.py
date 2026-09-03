"""
Traffic Simulation Engine with accident-prevention collision avoidance,
junction conflict locking, and automated traffic violation (E-Challan) detection.
"""

import random
import time
from typing import Dict, List, Optional
from traffic_ai.challan_manager import ChallanManager
from traffic_ai.controller import ControlMode, TrafficController
from traffic_ai.intersection import Intersection, LightState
from traffic_ai.vehicle import Direction, Vehicle, VehicleType
from traffic_ai.vision_detector import VisionDetector


class TrafficSimulation:
    """
    Coordinates vehicle spawning, accident-free car-following kinematics,
    vision sensing, and automated e-challan traffic violation logging.
    """

    def __init__(
        self,
        intersection: Intersection,
        controller: TrafficController,
        vision_detector: VisionDetector,
        challan_manager: Optional[ChallanManager] = None,
        spawn_rate: float = 0.45,
    ):
        self.intersection = intersection
        self.controller = controller
        self.vision = vision_detector
        self.challan_manager = challan_manager or ChallanManager()
        self.spawn_rate = spawn_rate
        
        self.vehicles: Dict[Direction, List[Vehicle]] = {
            Direction.NORTH: [],
            Direction.SOUTH: [],
            Direction.EAST: [],
            Direction.WEST: [],
        }
        
        self.vehicle_id_counter = 1
        self.is_paused = False
        
        # Metrics
        self.total_spawned = 0
        self.total_passed = 0
        self.completed_wait_times: List[float] = []
        self.start_time = time.time()
        self.sim_elapsed = 0.0

    def is_perpendicular_box_occupied(self, current_dir: Direction) -> bool:
        """
        Anti-Collision Lock:
        Checks if any perpendicular vehicle is inside the central junction box.
        """
        curr_axis = "NS" if current_dir in (Direction.NORTH, Direction.SOUTH) else "EW"
        for d, lane in self.vehicles.items():
            d_axis = "NS" if d in (Direction.NORTH, Direction.SOUTH) else "EW"
            if d_axis != curr_axis:
                for v in lane:
                    if self.intersection.is_in_conflict_zone(d, v.position):
                        return True
        return False

    def spawn_vehicle(self, direction: Direction, vehicle_type: VehicleType = None) -> bool:
        """Attempts to spawn a vehicle if spawn area is clear."""
        lane_vehicles = self.vehicles[direction]
        spawn_pos = 0.0 if direction in (Direction.NORTH, Direction.WEST) else (
            self.intersection.height if direction == Direction.SOUTH else self.intersection.width
        )
        
        # Prevent spawn overlap
        for v in lane_vehicles:
            dist = abs(v.position - spawn_pos)
            if dist < 55.0:
                return False

        if vehicle_type is None:
            r = random.random()
            if r < 0.68:
                vehicle_type = VehicleType.CAR
            elif r < 0.80:
                vehicle_type = VehicleType.BUS
            elif r < 0.90:
                vehicle_type = VehicleType.TRUCK
            elif r < 0.98:
                vehicle_type = VehicleType.BIKE
            else:
                vehicle_type = VehicleType.EMERGENCY

        v = Vehicle(self.vehicle_id_counter, vehicle_type, direction, spawn_pos)
        self.vehicle_id_counter += 1
        self.vehicles[direction].append(v)
        self.total_spawned += 1

        # Register in Challan DB for ANPR lookups
        self.challan_manager.register_or_get_vehicle(v.plate_number, v.type.value)
        return True

    def trigger_emergency_vehicle(self, direction: Direction = None):
        """Forces an emergency vehicle spawn in the specified direction or random lane."""
        if direction is None:
            direction = random.choice(list(Direction))
        self.spawn_vehicle(direction, VehicleType.EMERGENCY)

    def update(self, dt: float = 0.1):
        """Advances simulation by dt seconds with multi-tier collision avoidance."""
        if self.is_paused:
            return

        self.sim_elapsed += dt

        # 1. Spawning
        for d in Direction:
            if random.random() < (self.spawn_rate * dt * 2.0):
                self.spawn_vehicle(d)

        # 2. Vision Sensing
        telemetry = self.vision.get_intersection_snapshot(
            self.vehicles, self.intersection.stop_positions
        )

        # 3. AI Controller Step
        self.controller.step(dt, telemetry)

        # 4. Kinematics & Collision-Free Motion Update
        for direction, lane in self.vehicles.items():
            light = self.intersection.get_light(direction)
            stop_pos = self.intersection.stop_positions[direction]

            # Sort vehicles by progression towards intersection
            if direction in (Direction.NORTH, Direction.WEST):
                lane.sort(key=lambda v: v.position, reverse=True)
            else:
                lane.sort(key=lambda v: v.position, reverse=False)

            perp_occupied = self.is_perpendicular_box_occupied(direction)

            for i, v in enumerate(lane):
                lead_vehicle = lane[i - 1] if i > 0 else None
                target_speed = v.max_speed
                
                # A. Car-Following Safety Headway (Prevent Rear-End Collisions)
                if lead_vehicle is not None:
                    gap = abs(lead_vehicle.position - v.position) - lead_vehicle.length
                    min_safe_gap = 18.0 + (v.speed * 3.5)

                    if gap < 12.0:
                        target_speed = 0.0
                    elif gap < min_safe_gap:
                        target_speed = min(target_speed, lead_vehicle.speed * 0.5)
                    elif gap < min_safe_gap * 1.8:
                        target_speed = min(target_speed, lead_vehicle.speed * 0.85)

                # B. Stop Line & Signal Management
                has_crossed = self.intersection.has_passed_stop_line(direction, v.position)
                dist_to_stop = abs(stop_pos - v.position)

                if not has_crossed:
                    # Approaching stop line
                    if light in (LightState.RED, LightState.YELLOW, LightState.ALL_RED):
                        # Safe deceleration to a complete stop
                        if dist_to_stop < 6.0:
                            target_speed = 0.0
                        elif dist_to_stop < 65.0:
                            target_speed = min(target_speed, (dist_to_stop / 65.0) * v.max_speed * 0.6)
                    else:
                        # Light is GREEN:
                        # Anti-Collision Lock: If cross traffic is clearing inside intersection, yield!
                        if dist_to_stop < 50.0 and perp_occupied and not v.is_emergency:
                            target_speed = min(target_speed, (dist_to_stop / 50.0) * v.max_speed * 0.4)
                            if dist_to_stop < 8.0:
                                target_speed = 0.0
                        else:
                            target_speed = max(target_speed, v.max_speed * 0.95)

                else:
                    # Vehicle has crossed the stop line
                    if not v.has_crossed:
                        v.has_crossed = True
                        # Check for Red Light Jumping violation!
                        if light in (LightState.RED, LightState.ALL_RED) and not v.is_emergency:
                            if not v.challan_issued:
                                v.has_jumped_red_light = True
                                v.challan_issued = True
                                self.challan_manager.issue_challan(
                                    plate_number=v.plate_number,
                                    violation_type="Red Light Jumping",
                                    location=f"{direction.value} Approach Stop Line",
                                    vehicle_type=v.type.value
                                )

                    # In junction or clearing: maintain steady forward speed
                    target_speed = v.max_speed

                # C. Check Overspeeding Violation
                if v.speed > 4.6 and not v.is_emergency and not v.speed_violation:
                    v.speed_violation = True
                    self.challan_manager.issue_challan(
                        plate_number=v.plate_number,
                        violation_type="Overspeeding",
                        location=f"{direction.value} Corridor Speed Trap",
                        vehicle_type=v.type.value
                    )

                # D. Update Motion with Collision Clamp
                dt_scale = dt * 10.0
                old_pos = v.position
                v.update_motion(target_speed, dt_scale)

                # Clamp position to strictly prevent overlapping lead vehicle
                if lead_vehicle is not None:
                    min_distance = (v.length / 2.0) + (lead_vehicle.length / 2.0) + 6.0
                    if direction in (Direction.NORTH, Direction.WEST):
                        max_allowed = lead_vehicle.position - min_distance
                        if v.position > max_allowed:
                            v.position = max_allowed
                            v.speed = min(v.speed, lead_vehicle.speed)
                    else:
                        min_allowed = lead_vehicle.position + min_distance
                        if v.position < min_allowed:
                            v.position = min_allowed
                            v.speed = min(v.speed, lead_vehicle.speed)

            # 5. Remove exited vehicles
            remaining = []
            for v in lane:
                exited = False
                if direction == Direction.NORTH and v.position > self.intersection.height + 40:
                    exited = True
                elif direction == Direction.SOUTH and v.position < -40:
                    exited = True
                elif direction == Direction.WEST and v.position > self.intersection.width + 40:
                    exited = True
                elif direction == Direction.EAST and v.position < -40:
                    exited = True

                if exited:
                    self.total_passed += 1
                    self.completed_wait_times.append(v.wait_time)
                else:
                    remaining.append(v)
            self.vehicles[direction] = remaining

    def get_average_wait_time(self) -> float:
        """Returns average wait time in seconds across completed journeys."""
        if not self.completed_wait_times:
            return 0.0
        return sum(self.completed_wait_times) / len(self.completed_wait_times)

    def get_throughput_rate(self) -> float:
        """Returns vehicles passed per minute."""
        minutes = max(0.1, self.sim_elapsed / 60.0)
        return self.total_passed / minutes
