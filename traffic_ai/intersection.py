"""
Intersection geometry, conflict zone boundaries, and traffic light state tracking.
"""

from enum import Enum
from typing import Dict
from traffic_ai.vehicle import Direction


class LightState(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    ALL_RED = "ALL_RED"


class TrafficPhase(Enum):
    NORTH_SOUTH = "NS"
    EAST_WEST = "EW"

    @property
    def alternate(self):
        return TrafficPhase.EAST_WEST if self == TrafficPhase.NORTH_SOUTH else TrafficPhase.NORTH_SOUTH


class Intersection:
    """
    Manages 4-way intersection layout, boundaries, stop lines,
    collision conflict zones, and traffic lights.
    """

    def __init__(self, width: int = 800, height: int = 800, road_width: int = 160):
        self.width = width
        self.height = height
        self.road_width = road_width
        self.cx = width / 2.0
        self.cy = height / 2.0
        
        # Intersection boundaries
        self.left_boundary = self.cx - self.road_width / 2.0
        self.right_boundary = self.cx + self.road_width / 2.0
        self.top_boundary = self.cy - self.road_width / 2.0
        self.bottom_boundary = self.cy + self.road_width / 2.0
        
        # Stop line positions along lane axis (before crosswalk)
        self.stop_positions: Dict[Direction, float] = {
            Direction.NORTH: self.top_boundary - 16,
            Direction.SOUTH: self.bottom_boundary + 16,
            Direction.WEST: self.left_boundary - 16,
            Direction.EAST: self.right_boundary + 16,
        }
        
        # Current active lights for each direction
        self.lights: Dict[Direction, LightState] = {
            Direction.NORTH: LightState.RED,
            Direction.SOUTH: LightState.RED,
            Direction.EAST: LightState.RED,
            Direction.WEST: LightState.RED,
        }

    def set_phase_lights(self, active_phase: TrafficPhase, state: LightState):
        """Sets light states according to active phase pair."""
        if state == LightState.ALL_RED:
            self.set_all_red()
            return

        if active_phase == TrafficPhase.NORTH_SOUTH:
            self.lights[Direction.NORTH] = state
            self.lights[Direction.SOUTH] = state
            self.lights[Direction.EAST] = LightState.RED
            self.lights[Direction.WEST] = LightState.RED
        else:
            self.lights[Direction.EAST] = state
            self.lights[Direction.WEST] = state
            self.lights[Direction.NORTH] = LightState.RED
            self.lights[Direction.SOUTH] = LightState.RED

    def set_all_red(self):
        """Standard All-Red clearance: stops all incoming traffic so clearing cars can exit."""
        for d in Direction:
            self.lights[d] = LightState.RED

    def set_emergency_corridor(self, priority_dir: Direction, state: LightState):
        """Preempts all signals, giving green corridor to priority corridor."""
        for d in Direction:
            self.lights[d] = LightState.RED
        self.lights[priority_dir] = state
        self.lights[priority_dir.opposite] = state

    def get_light(self, direction: Direction) -> LightState:
        return self.lights[direction]

    def has_passed_stop_line(self, direction: Direction, position: float) -> bool:
        """Determines if a vehicle has crossed the stop line."""
        stop_pos = self.stop_positions[direction]
        if direction == Direction.NORTH:
            return position >= stop_pos
        elif direction == Direction.SOUTH:
            return position <= stop_pos
        elif direction == Direction.WEST:
            return position >= stop_pos
        elif direction == Direction.EAST:
            return position <= stop_pos
        return False

    def is_in_conflict_zone(self, direction: Direction, position: float) -> bool:
        """
        Critical Anti-Collision check:
        Determines if a vehicle is physically inside the central junction conflict box.
        """
        margin = 10.0
        if direction == Direction.NORTH:
            return (self.top_boundary - margin) <= position <= (self.bottom_boundary + margin)
        elif direction == Direction.SOUTH:
            return (self.top_boundary - margin) <= position <= (self.bottom_boundary + margin)
        elif direction == Direction.WEST:
            return (self.left_boundary - margin) <= position <= (self.right_boundary + margin)
        elif direction == Direction.EAST:
            return (self.left_boundary - margin) <= position <= (self.right_boundary + margin)
        return False

    def is_past_intersection(self, direction: Direction, position: float) -> bool:
        """Determines if a vehicle has completely cleared the center junction box."""
        if direction == Direction.NORTH:
            return position > self.bottom_boundary + 15
        elif direction == Direction.SOUTH:
            return position < self.top_boundary - 15
        elif direction == Direction.WEST:
            return position > self.right_boundary + 15
        elif direction == Direction.EAST:
            return position < self.left_boundary - 15
        return False
