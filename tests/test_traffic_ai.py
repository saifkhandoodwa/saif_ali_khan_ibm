"""
Unit and Integration Tests for AI Traffic Light, ANPR, and E-Challan System.
"""

import unittest
from traffic_ai.challan_manager import ChallanManager
from traffic_ai.controller import ControlMode, TrafficController
from traffic_ai.intersection import Intersection, LightState, TrafficPhase
from traffic_ai.reality_detector import RealityDetector
from traffic_ai.simulation import TrafficSimulation
from traffic_ai.vehicle import Direction, Vehicle, VehicleType
from traffic_ai.vision_detector import VisionDetector


class TestTrafficAI(unittest.TestCase):

    def setUp(self):
        self.intersection = Intersection(800, 800, 160)
        self.controller = TrafficController(self.intersection, mode=ControlMode.AI_ADAPTIVE)
        self.vision = VisionDetector()
        self.challan_manager = ChallanManager()
        self.simulation = TrafficSimulation(
            self.intersection, self.controller, self.vision,
            challan_manager=self.challan_manager, spawn_rate=0.0
        )

    def test_intersection_initialization(self):
        """Check initial light states and boundaries."""
        self.assertEqual(self.intersection.get_light(Direction.NORTH), LightState.GREEN)
        self.assertEqual(self.intersection.get_light(Direction.SOUTH), LightState.GREEN)
        self.assertEqual(self.intersection.get_light(Direction.EAST), LightState.RED)
        self.assertEqual(self.intersection.get_light(Direction.WEST), LightState.RED)

    def test_all_red_clearance(self):
        """Verify All-Red transition occurs between phases."""
        self.controller.light_state = LightState.YELLOW
        self.controller.phase_time_elapsed = 3.5
        telemetry = self.vision.get_intersection_snapshot(
            self.simulation.vehicles, self.intersection.stop_positions
        )
        self.controller.step(0.1, telemetry)
        self.assertEqual(self.controller.light_state, LightState.ALL_RED)
        self.assertEqual(self.intersection.get_light(Direction.NORTH), LightState.RED)
        self.assertEqual(self.intersection.get_light(Direction.EAST), LightState.RED)

    def test_conflict_zone_detection(self):
        """Test junction box conflict detection."""
        cx, cy = 400, 400
        # Position in center box for North vehicle
        self.assertTrue(self.intersection.is_in_conflict_zone(Direction.NORTH, cy))
        # Position far upstream
        self.assertFalse(self.intersection.is_in_conflict_zone(Direction.NORTH, 50.0))

    def test_no_vehicle_overlap_headway(self):
        """Test car-following clamps position to strictly prevent overlapping."""
        v1 = Vehicle(1, VehicleType.CAR, Direction.NORTH, position=200.0)
        v2 = Vehicle(2, VehicleType.CAR, Direction.NORTH, position=160.0)
        self.simulation.vehicles[Direction.NORTH] = [v1, v2]

        # Stop v1
        v1.speed = 0.0
        # Push simulation updates
        for _ in range(20):
            self.simulation.update(dt=0.1)

        # Gap between centers must exceed sum of half-lengths
        center_distance = v1.position - v2.position
        min_allowed = (v1.length / 2.0) + (v2.length / 2.0)
        self.assertGreater(center_distance, min_allowed)

    def test_echallan_search_and_payment(self):
        """Test searching plate and settling e-challan."""
        plate = "DL-01-AB-1234"
        res = self.challan_manager.search_by_plate(plate)
        self.assertTrue(res["found"])
        self.assertGreater(len(res["challans"]), 0)

        cid = res["challans"][0].challan_id
        paid = self.challan_manager.pay_challan(cid)
        self.assertTrue(paid)

        # Verify status changed to PAID
        c = self.challan_manager.challans[cid]
        self.assertEqual(c.status, "PAID")
        self.assertIsNotNone(c.payment_id)

    def test_reality_detector_frame(self):
        """Test OpenCV RealityDetector reads and processes frames with AI annotations."""
        detector = RealityDetector(self.challan_manager)
        frame, tele = detector.read_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape[0], 480)
        self.assertEqual(frame.shape[1], 720)
        self.assertIn("fps", tele)
        self.assertIn("detected_count", tele)
        detector.release()


if __name__ == "__main__":
    unittest.main()
