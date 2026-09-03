"""
Unit and Integration Tests for Real AI Traffic Vision, ANPR, and E-Challan System.
"""

import unittest
from traffic_ai.anpr_engine import ANPREngine
from traffic_ai.challan_manager import ChallanManager
from traffic_ai.vision_pipeline import VisionPipeline


class TestRealTrafficAI(unittest.TestCase):

    def setUp(self):
        self.challan_manager = ChallanManager()
        self.anpr = ANPREngine(self.challan_manager)
        self.pipeline = VisionPipeline(self.challan_manager)

    def test_anpr_plate_generation_and_scan(self):
        """Verify license plate generation and scanning registration."""
        plate = "DL-01-AB-1234"
        event = self.anpr.register_scan(plate, vehicle_type="car", speed=48.0)
        self.assertEqual(event["plate_number"], plate)
        self.assertEqual(self.anpr.last_scanned_plate, plate)
        self.assertGreater(len(self.anpr.scanned_history), 0)

    def test_challan_search_and_payment(self):
        """Verify searching plate records and paying e-challans."""
        plate = "DL-01-AB-1234"
        res = self.challan_manager.search_by_plate(plate)
        self.assertTrue(res["found"])
        self.assertGreater(len(res["challans"]), 0)

        # Settle first pending challan
        cid = res["challans"][0].challan_id
        paid = self.challan_manager.pay_challan(cid)
        self.assertTrue(paid)

        c = self.challan_manager.challans[cid]
        self.assertEqual(c.status, "PAID")
        self.assertIsNotNone(c.payment_id)

    def test_vision_pipeline_frame_processing(self):
        """Test video frame AI processing, HUD annotation, and telemetry."""
        frame, tele = self.pipeline.process_next_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape[0], 500)
        self.assertEqual(frame.shape[1], 760)
        self.assertIn("fps", tele)
        self.assertIn("signal_state", tele)
        self.assertIn(tele["signal_state"], ("GREEN", "YELLOW", "RED"))

    def test_smart_camera_signal_adaptation(self):
        """Verify signal controller adapts to camera vehicle density."""
        initial_timer = self.pipeline.signal_timer
        # High traffic detected
        self.pipeline.update_signal_controller(detected_vehicle_count=5, dt=1.0)
        self.assertIsNotNone(self.pipeline.signal_state)

    def test_emergency_preemption(self):
        """Verify emergency override forces green wave."""
        self.pipeline.signal_state = "RED"
        self.pipeline.trigger_emergency_preemption()
        self.assertEqual(self.pipeline.signal_state, "GREEN")
        self.assertTrue(self.pipeline.is_emergency_active)


if __name__ == "__main__":
    unittest.main()
