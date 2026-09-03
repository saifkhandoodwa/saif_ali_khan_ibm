"""
Intersection geometry and traffic light state tracking.
"""

from enum import Enum
from typing import Dict
from traffic_ai.vehicle import Direction


class LightState(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class TrafficPhase(Enum):
    NORTH_SOUTH = "NS"
    EAST_WEST = "EW"

    @property
    def alternate(self):
        return TrafficPhase.EAST_WEST if self == TrafficPhase.NORTH_SOUTH else TrafficPhase.NORTH_SOUTH


class Intersection:
    """
    Manages 4-way intersection layout, boundaries, stop lines, and traffic lights.
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
        
        # Stop line positions along lane axis (0 is spawn point, stop_pos is before boundary)
        # For NORTH: travels y from 0 to height. Stop line at top_boundary - 10
        # For SOUTH: travels y from height to 0. Stop line at bottom_boundary + 10
        # For WEST: travels x from 0 to width. Stop line at left_boundary - 10
        # For EAST: travels x from width to 0. Stop line at right_boundary + 10
        self.stop_positions: Dict[Direction, float] = {
            Direction.NORTH: self.top_boundary - 12,
            Direction.SOUTH: self.bottom_boundary + 12,
            Direction.WEST: self.left_boundary - 12,
            Direction.EAST: self.right_boundary + 12,
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

    def set_emergency_corridor(self, priority_dir: Direction, state: LightState):
        """Preempts all signals, giving green corridor to the priority direction and its opposite."""
        for d in Direction:
            self.lights[d] = LightState.RED
        self.lights[priority_dir] = state
        self.lights[priority_dir.opposite] = state

    def get_light(self, direction: Direction) -> LightState:
        return self.lights[direction]

    def has_passed_stop_line(self, direction: Direction, position: float) -> bool:
        """Determines if a vehicle coordinate has crossed the stop line."""
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

    def is_past_intersection(self, direction: Direction, position: float) -> bool:
        """Determines if a vehicle has cleared the center junction box."""
        if direction == Direction.NORTH:
            return position > self.bottom_boundary
        elif direction == Direction.SOUTH:
            return position < self.top_boundary
        elif direction == Direction.WEST:
            return position > self.right_boundary
        elif direction == Direction.EAST:
            return position < self.left_boundary
        return False
