"""
Vehicle models and kinematics for traffic simulation.
"""

from enum import Enum
import random
import time

class VehicleType(Enum):
    CAR = "car"
    BUS = "bus"
    TRUCK = "truck"
    BIKE = "bike"
    EMERGENCY = "emergency"


class Direction(Enum):
    NORTH = "NORTH"  # Moving Southbound (from top to bottom)
    SOUTH = "SOUTH"  # Moving Northbound (from bottom to top)
    EAST = "EAST"    # Moving Westbound (from right to left)
    WEST = "WEST"    # Moving Eastbound (from left to right)

    @property
    def opposite(self):
        opposites = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }
        return opposites[self]


class Vehicle:
    """Represents a simulated vehicle approaching and crossing an intersection."""

    TYPE_CONFIGS = {
        VehicleType.CAR: {
            "length": 26,
            "width": 14,
            "max_speed": 4.5,
            "weight": 1.0,
            "colors": ["#3498db", "#2980b9", "#9b59b6", "#1abc9c", "#95a5a6"]
        },
        VehicleType.BUS: {
            "length": 42,
            "width": 16,
            "max_speed": 3.2,
            "weight": 2.5,
            "colors": ["#f39c12", "#e67e22", "#d35400"]
        },
        VehicleType.TRUCK: {
            "length": 46,
            "width": 17,
            "max_speed": 3.0,
            "weight": 3.0,
            "colors": ["#7f8c8d", "#34495e"]
        },
        VehicleType.BIKE: {
            "length": 16,
            "width": 8,
            "max_speed": 5.0,
            "weight": 0.5,
            "colors": ["#2ecc71", "#27ae60", "#16a085"]
        },
        VehicleType.EMERGENCY: {
            "length": 32,
            "width": 16,
            "max_speed": 6.0,
            "weight": 10.0,
            "colors": ["#e74c3c"]
        },
    }

    def __init__(self, vehicle_id: int, vehicle_type: VehicleType, direction: Direction, position: float):
        self.id = vehicle_id
        self.type = vehicle_type
        self.direction = direction
        self.position = position  # 1D coordinate along the lane axis
        
        cfg = self.TYPE_CONFIGS[vehicle_type]
        self.length = cfg["length"]
        self.width = cfg["width"]
        self.max_speed = cfg["max_speed"]
        self.weight = cfg["weight"]
        self.color = random.choice(cfg["colors"])
        
        self.speed = self.max_speed * 0.8
        self.acceleration = 0.2
        self.deceleration = 0.4
        
        self.spawn_time = time.time()
        self.wait_time = 0.0  # seconds spent stationary (speed < 0.2)
        self.has_crossed = False
        self.siren_phase = 0.0  # for emergency vehicle flash animation

    @property
    def is_emergency(self) -> bool:
        return self.type == VehicleType.EMERGENCY

    def update_motion(self, target_speed: float, dt: float = 1.0):
        """Update vehicle velocity and position smoothly towards target_speed."""
        if self.speed < target_speed:
            self.speed = min(self.speed + self.acceleration * dt, target_speed)
        elif self.speed > target_speed:
            self.speed = max(self.speed - self.deceleration * dt, target_speed)
            
        delta = self.speed * dt
        if self.direction in (Direction.NORTH, Direction.WEST):
            self.position += delta
        else:
            self.position -= delta
        
        if self.speed < 0.2:
            self.wait_time += (dt / 10.0)  # normalized wait time counter

        if self.is_emergency:
            self.siren_phase += dt * 0.2
