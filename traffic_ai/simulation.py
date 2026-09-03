"""
Traffic Simulation Engine with car-following physics and metrics tracking.
"""

import random
import time
from typing import Dict, List
from traffic_ai.controller import ControlMode, TrafficController
from traffic_ai.intersection import Intersection, LightState
from traffic_ai.vehicle import Direction, Vehicle, VehicleType
from traffic_ai.vision_detector import VisionDetector


class TrafficSimulation:
    """
    Coordinates vehicle spawning, car-following physics, vision sensing, and metrics.
    """

    def __init__(
        self,
        intersection: Intersection,
        controller: TrafficController,
        vision_detector: VisionDetector,
        spawn_rate: float = 0.5,  # probability per tick to attempt spawn
    ):
        self.intersection = intersection
        self.controller = controller
        self.vision = vision_detector
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

    def spawn_vehicle(self, direction: Direction, vehicle_type: VehicleType = None) -> bool:
        """Attempts to spawn a vehicle if spawn area is clear."""
        # Safe spawn distance check
        lane_vehicles = self.vehicles[direction]
        spawn_pos = 0.0 if direction in (Direction.NORTH, Direction.WEST) else (
            self.intersection.height if direction == Direction.SOUTH else self.intersection.width
        )
        
        # Check if any vehicle is too close to spawn point
        for v in lane_vehicles:
            dist = abs(v.position - spawn_pos)
            if dist < 45.0:
                return False  # lane entrance blocked

        # Determine vehicle type
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
        return True

    def trigger_emergency_vehicle(self, direction: Direction = None):
        """Forces an emergency vehicle spawn in the specified direction or busiest lane."""
        if direction is None:
            # pick random direction
            direction = random.choice(list(Direction))
        
        # If lane is blocked at spawn, clear a small opening or push ahead
        self.spawn_vehicle(direction, VehicleType.EMERGENCY)

    def update(self, dt: float = 0.1):
        """Advances simulation by dt seconds."""
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

        # 4. Kinematics & Car-Following Update
        for direction, lane in self.vehicles.items():
            light = self.intersection.get_light(direction)
            stop_pos = self.intersection.stop_positions[direction]

            # Sort vehicles by distance traveled (vehicles closest to intersection are evaluated first)
            if direction in (Direction.NORTH, Direction.WEST):
                lane.sort(key=lambda v: v.position, reverse=True)
            else:
                lane.sort(key=lambda v: v.position, reverse=False)

            for i, v in enumerate(lane):
                # Calculate vehicle ahead
                lead_vehicle = lane[i - 1] if i > 0 else None
                
                # Default target speed
                target_speed = v.max_speed
                
                # Check distance to vehicle ahead
                if lead_vehicle is not None:
                    gap = abs(lead_vehicle.position - v.position) - lead_vehicle.length
                    if gap < 12.0:
                        target_speed = 0.0
                    elif gap < 35.0:
                        target_speed = min(target_speed, lead_vehicle.speed * 0.7)
                    elif gap < 65.0:
                        target_speed = min(target_speed, lead_vehicle.speed)

                # Check traffic light and stop line
                has_crossed = self.intersection.has_passed_stop_line(direction, v.position)
                
                if not has_crossed:
                    # Calculate distance to stop line
                    dist_to_stop = abs(stop_pos - v.position)
                    
                    if light in (LightState.RED, LightState.YELLOW):
                        # Approaching a red/yellow light
                        if dist_to_stop < 8.0:
                            target_speed = 0.0
                        elif dist_to_stop < 50.0:
                            target_speed = min(target_speed, (dist_to_stop / 50.0) * v.max_speed * 0.7)
                    else:
                        # Light is GREEN: clear ahead
                        target_speed = max(target_speed, v.max_speed * 0.9)
                else:
                    v.has_crossed = True
                    # In intersection or leaving: maintain safe speed
                    target_speed = v.max_speed

                # Update motion
                # Adjust position sign depending on direction
                dt_scale = dt * 10.0  # normalize step speed
                v.update_motion(target_speed, dt_scale)

            # 5. Remove vehicles that have exited canvas bounds
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
