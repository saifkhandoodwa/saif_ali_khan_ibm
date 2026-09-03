"""
Unit and Integration Tests for AI Traffic Light System.
"""

import unittest
from traffic_ai.controller import ControlMode, TrafficController
from traffic_ai.intersection import Intersection, LightState, TrafficPhase
from traffic_ai.simulation import TrafficSimulation
from traffic_ai.vehicle import Direction, Vehicle, VehicleType
from traffic_ai.vision_detector import VisionDetector


class TestTrafficAI(unittest.TestCase):

    def setUp(self):
        self.intersection = Intersection(800, 800, 160)
        self.controller = TrafficController(self.intersection, mode=ControlMode.AI_ADAPTIVE)
        self.vision = VisionDetector()
        self.simulation = TrafficSimulation(
            self.intersection, self.controller, self.vision, spawn_rate=0.0
        )

    def test_intersection_initialization(self):
        """Check initial light states and boundaries."""
        self.assertEqual(self.intersection.get_light(Direction.NORTH), LightState.GREEN)
        self.assertEqual(self.intersection.get_light(Direction.SOUTH), LightState.GREEN)
        self.assertEqual(self.intersection.get_light(Direction.EAST), LightState.RED)
        self.assertEqual(self.intersection.get_light(Direction.WEST), LightState.RED)

    def test_vehicle_spawning_and_motion(self):
        """Check vehicle kinematics and position updates."""
        v = Vehicle(1, VehicleType.CAR, Direction.NORTH, position=100.0)
        initial_pos = v.position
        v.update_motion(target_speed=4.0, dt=1.0)
        self.assertGreater(v.position, initial_pos)

        # South vehicle should move upwards (position decreasing)
        v_south = Vehicle(2, VehicleType.CAR, Direction.SOUTH, position=700.0)
        initial_south_pos = v_south.position
        v_south.update_motion(target_speed=4.0, dt=1.0)
        self.assertLess(v_south.position, initial_south_pos)

    def test_vision_detector_emergency(self):
        """Check computer vision telemetry detects emergency vehicle."""
        v_em = Vehicle(10, VehicleType.EMERGENCY, Direction.EAST, position=600.0)
        telemetry = self.vision.analyze_lane(
            Direction.EAST, [v_em], self.intersection.stop_positions[Direction.EAST]
        )
        self.assertTrue(telemetry.emergency_present)
        self.assertEqual(telemetry.vehicle_count, 1)

    def test_controller_emergency_preemption(self):
        """Verify that emergency vehicle triggers preemption."""
        # Initial phase is NORTH_SOUTH
        self.assertEqual(self.controller.active_phase, TrafficPhase.NORTH_SOUTH)

        # Spawn emergency vehicle on WEST
        self.simulation.spawn_vehicle(Direction.WEST, VehicleType.EMERGENCY)

        # Run simulation steps
        for _ in range(35):
            self.simulation.update(dt=0.1)

        # Signal should switch or transition towards EAST_WEST corridor
        self.assertTrue(
            self.controller.emergency_phase
            or self.controller.active_phase == TrafficPhase.EAST_WEST
        )

    def test_adaptive_green_calculation(self):
        """Check AI calculates longer green duration for heavy queues."""
        telemetry = self.vision.get_intersection_snapshot(
            self.simulation.vehicles, self.intersection.stop_positions
        )
        base_green = self.controller.calculate_optimal_green_duration(
            telemetry, TrafficPhase.NORTH_SOUTH
        )

        # Add 5 vehicles to North lane
        for i in range(5):
            self.simulation.vehicles[Direction.NORTH].append(
                Vehicle(100 + i, VehicleType.CAR, Direction.NORTH, position=100.0 + i * 20)
            )

        telemetry_heavy = self.vision.get_intersection_snapshot(
            self.simulation.vehicles, self.intersection.stop_positions
        )
        heavy_green = self.controller.calculate_optimal_green_duration(
            telemetry_heavy, TrafficPhase.NORTH_SOUTH
        )

        self.assertGreater(heavy_green, base_green)


if __name__ == "__main__":
    unittest.main()
