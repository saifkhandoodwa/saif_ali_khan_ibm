"""
Real AI Traffic Vision, ANPR Number Plate Detection & Smart Signal System.
Directly launches the Real AI Camera Detection & E-Challan Enforcement Application.
"""

import argparse
import sys
import tkinter as tk

from traffic_ai.challan_manager import ChallanManager
from traffic_ai.vision_pipeline import VisionPipeline
from gui.real_app import RealTrafficApp


def main():
    parser = argparse.ArgumentParser(description="Real AI Traffic Vision & E-Challan System")
    parser.add_argument("--webcam", action="store_true", help="Start directly with physical webcam")
    parser.add_argument("--video", type=str, help="Path to traffic video file")
    parser.add_argument("--image", type=str, help="Path to traffic image file")
    args = parser.parse_args()

    # Initialize Real AI Vision Engine & E-Challan Manager
    challan_manager = ChallanManager()
    pipeline = VisionPipeline(challan_manager=challan_manager)

    if args.webcam:
        pipeline.set_source_webcam(0)
    elif args.video:
        pipeline.set_source_video_file(args.video)
    elif args.image:
        pipeline.set_source_image(args.image)
    else:
        pipeline.set_source_synthetic()

    # Launch Desktop Application
    root = tk.Tk()
    app = RealTrafficApp(root, pipeline=pipeline)
    root.mainloop()


if __name__ == "__main__":
    main()
