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

    @property
    def is_vertical(self):
        return self in (Direction.NORTH, Direction.SOUTH)


def generate_license_plate() -> str:
    """Generates realistic Indian vehicle registration number."""
    states = ["DL", "MH", "KA", "UP", "RJ", "HR", "MP", "GJ", "TS", "TN"]
    rto = random.randint(1, 20)
    series = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=2))
    num = random.randint(1000, 9999)
    return f"{random.choice(states)}-{rto:02d}-{series}-{num}"


class Vehicle:
    """Represents a simulated vehicle approaching and crossing an intersection."""

    TYPE_CONFIGS = {
        VehicleType.CAR: {
            "length": 28,
            "width": 14,
            "max_speed": 4.2,
            "weight": 1.0,
            "colors": ["#38bdf8", "#3b82f6", "#8b5cf6", "#06b6d4", "#64748b"]
        },
        VehicleType.BUS: {
            "length": 46,
            "width": 16,
            "max_speed": 3.0,
            "weight": 2.5,
            "colors": ["#f59e0b", "#d97706", "#ea580c"]
        },
        VehicleType.TRUCK: {
            "length": 50,
            "width": 17,
            "max_speed": 2.8,
            "weight": 3.0,
            "colors": ["#94a3b8", "#475569"]
        },
        VehicleType.BIKE: {
            "length": 16,
            "width": 8,
            "max_speed": 4.8,
            "weight": 0.5,
            "colors": ["#22c55e", "#10b981", "#14b8a6"]
        },
        VehicleType.EMERGENCY: {
            "length": 34,
            "width": 16,
            "max_speed": 5.5,
            "weight": 10.0,
            "colors": ["#ef4444"]
        },
    }

    def __init__(
        self,
        vehicle_id: int,
        vehicle_type: VehicleType,
        direction: Direction,
        position: float,
        plate_number: str = None
    ):
        self.id = vehicle_id
        self.type = vehicle_type
        self.direction = direction
        self.position = position  # 1D coordinate along lane axis
        
        cfg = self.TYPE_CONFIGS[vehicle_type]
        self.length = cfg["length"]
        self.width = cfg["width"]
        self.max_speed = cfg["max_speed"]
        self.weight = cfg["weight"]
        self.color = random.choice(cfg["colors"])
        
        self.speed = self.max_speed * 0.75
        self.acceleration = 0.25
        self.deceleration = 0.55  # strong, reliable braking to prevent collisions
        
        self.spawn_time = time.time()
        self.wait_time = 0.0
        self.has_crossed = False
        self.siren_phase = 0.0
        
        # ANPR and Violation tracking
        self.plate_number = plate_number or generate_license_plate()
        self.has_jumped_red_light = False
        self.speed_violation = False
        self.challan_issued = False

    @property
    def is_emergency(self) -> bool:
        return self.type == VehicleType.EMERGENCY

    def update_motion(self, target_speed: float, dt: float = 1.0):
        """Smoothly adjusts velocity and updates position along direction vector."""
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
            self.wait_time += (dt / 10.0)

        if self.is_emergency:
            self.siren_phase += dt * 0.25
