"""
Vision & AI Detection Module.
Simulates and exposes computer vision sensing for real-time traffic detection,
queue density analysis, and emergency vehicle identification.
"""

from typing import Dict, List, Tuple
from traffic_ai.vehicle import Direction, Vehicle, VehicleType


class LaneTelemetry:
    """Telemetry data extracted by computer vision cameras per lane."""
    def __init__(self, direction: Direction):
        self.direction = direction
        self.vehicle_count = 0
        self.waiting_count = 0
        self.density_score = 0.0      # 0.0 (empty) to 1.0 (gridlock)
        self.emergency_present = False
        self.avg_wait_time = 0.0
        self.weighted_load = 0.0      # account for heavy vehicles (buses/trucks)


class VisionDetector:
    """
    AI Vision Processor simulating neural-network-based traffic camera sensors.
    Supports real-time lane density parsing and emergency siren/beacon recognition.
    """

    def __init__(self, camera_fps: int = 30):
        self.fps = camera_fps
        self.confidence_threshold = 0.85

    def analyze_lane(self, direction: Direction, vehicles: List[Vehicle], stop_line_pos: float) -> LaneTelemetry:
        """
        Runs simulated detection inference on the lane camera feed.
        Extracts counts, classifications, density, and detects emergency priority.
        """
        telemetry = LaneTelemetry(direction)
        
        waiting_times: List[float] = []
        total_weight = 0.0
        
        for v in vehicles:
            # Check if vehicle is approaching or queued before stop line
            is_approaching = False
            if direction == Direction.NORTH and v.position <= stop_line_pos:
                is_approaching = True
            elif direction == Direction.SOUTH and v.position >= stop_line_pos:
                is_approaching = True
            elif direction == Direction.WEST and v.position <= stop_line_pos:
                is_approaching = True
            elif direction == Direction.EAST and v.position >= stop_line_pos:
                is_approaching = True
                
            if is_approaching:
                telemetry.vehicle_count += 1
                total_weight += v.weight
                
                if v.is_emergency:
                    telemetry.emergency_present = True
                    
                if v.speed < 0.5:
                    telemetry.waiting_count += 1
                    waiting_times.append(v.wait_time)

        # Compute average wait time
        if waiting_times:
            telemetry.avg_wait_time = sum(waiting_times) / len(waiting_times)
        else:
            telemetry.avg_wait_time = 0.0

        # Compute normalized lane density (assuming max capacity ~10 vehicles per approach lane)
        max_capacity = 10.0
        telemetry.density_score = min(1.0, telemetry.vehicle_count / max_capacity)
        telemetry.weighted_load = total_weight
        
        return telemetry

    def get_intersection_snapshot(
        self,
        vehicles_by_dir: Dict[Direction, List[Vehicle]],
        stop_positions: Dict[Direction, float]
    ) -> Dict[Direction, LaneTelemetry]:
        """Runs full 4-camera detection inference across all approaches."""
        snapshot = {}
        for direction, vehicles in vehicles_by_dir.items():
            snapshot[direction] = self.analyze_lane(direction, vehicles, stop_positions[direction])
        return snapshot
