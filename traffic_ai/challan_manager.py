"""
E-Challan and Automatic Number Plate Recognition (ANPR) Database Manager.
Tracks vehicle violations, pending fines, and payment records.
"""

from dataclasses import dataclass, field
import datetime
import random
from typing import Dict, List, Optional


@dataclass
class VehicleRecord:
    plate_number: str
    owner_name: str
    vehicle_type: str
    vehicle_model: str
    registered_city: str
    contact_number: str
    insurance_valid: bool = True


@dataclass
class Challan:
    challan_id: str
    plate_number: str
    owner_name: str
    vehicle_type: str
    violation_type: str
    fine_amount: int
    timestamp: str
    location: str
    status: str = "PENDING"  # PENDING or PAID
    payment_id: Optional[str] = None
    payment_date: Optional[str] = None


class ChallanManager:
    """Manages traffic violation records, vehicle owner registry, and fine collections."""

    COMMON_NAMES = [
        "Aarav Sharma", "Saif Ali Khan", "Priya Verma", "Vikram Singh",
        "Ananya Gupta", "Rohan Mehta", "Deepak Patel", "Neha Joshi",
        "Amit Kumar", "Kavita Reddy", "Zaid Qureshi", "Sunil Rao"
    ]

    CITIES = ["Delhi", "Mumbai", "Bangalore", "Jaipur", "Lucknow", "Hyderabad", "Chandigarh"]

    VEHICLE_MODELS = {
        "car": ["Hyundai Creta", "Maruti Swift", "Tata Nexon", "Honda City", "Mahindra Thar"],
        "bus": ["Tata Starbus", "Ashok Leyland Viking", "Volvo 9600"],
        "truck": ["Tata Prima", "BharatBenz 2823", "Eicher Pro 3019"],
        "bike": ["Royal Enfield Classic", "Honda Activa", "Yamaha MT-15", "TVS Apache"],
        "emergency": ["Force Traveller Ambulance", "Tata Winger EMS"]
    }

    VIOLATION_FINES = {
        "Red Light Jumping": 1000,
        "Overspeeding": 2000,
        "Stop Line Intrusion": 500,
        "Dangerous Driving": 2500,
    }

    def __init__(self):
        self.challans: Dict[str, Challan] = {}
        self.vehicle_registry: Dict[str, VehicleRecord] = {}
        self.challan_counter = 1001

        # Seed some initial demo records
        self._seed_initial_data()

    def _seed_initial_data(self):
        """Pre-populates a few vehicles and historical challans for demonstration."""
        demo_plates = [
            ("DL-01-AB-1234", "car", "Saif Ali Khan", "Hyundai Creta", "Delhi"),
            ("MH-02-CP-8921", "car", "Rohan Mehta", "Tata Nexon", "Mumbai"),
            ("UP-14-EA-4521", "bike", "Aarav Sharma", "Royal Enfield Classic", "Lucknow"),
            ("KA-03-MK-7821", "truck", "Vikram Singh", "Tata Prima", "Bangalore"),
            ("RJ-14-GH-6721", "car", "Priya Verma", "Honda City", "Jaipur"),
        ]

        for plate, vtype, owner, model, city in demo_plates:
            record = VehicleRecord(
                plate_number=plate,
                owner_name=owner,
                vehicle_type=vtype,
                vehicle_model=model,
                registered_city=city,
                contact_number=f"+91 98{random.randint(10000000, 99999999)}"
            )
            self.vehicle_registry[plate] = record

        # Add initial sample challan
        self.issue_challan(
            plate_number="DL-01-AB-1234",
            violation_type="Overspeeding",
            location="North-South Highway, Speed Camera 02",
            custom_time="2026-09-02 14:22:10"
        )
        self.issue_challan(
            plate_number="MH-02-CP-8921",
            violation_type="Red Light Jumping",
            location="Central 4-Way Junction, Lane 01",
            custom_time="2026-09-03 09:15:45"
        )

    def register_or_get_vehicle(self, plate_number: str, vehicle_type: str = "car") -> VehicleRecord:
        """Finds or dynamically generates registered owner details for a vehicle."""
        if plate_number in self.vehicle_registry:
            return self.vehicle_registry[plate_number]

        vtype_key = vehicle_type.lower()
        models = self.VEHICLE_MODELS.get(vtype_key, self.VEHICLE_MODELS["car"])
        record = VehicleRecord(
            plate_number=plate_number,
            owner_name=random.choice(self.COMMON_NAMES),
            vehicle_type=vehicle_type,
            vehicle_model=random.choice(models),
            registered_city=random.choice(self.CITIES),
            contact_number=f"+91 98{random.randint(10000000, 99999999)}"
        )
        self.vehicle_registry[plate_number] = record
        return record

    def issue_challan(
        self,
        plate_number: str,
        violation_type: str,
        location: str = "Central 4-Way Junction",
        vehicle_type: str = "car",
        custom_time: Optional[str] = None
    ) -> Challan:
        """Creates and logs a traffic e-challan."""
        record = self.register_or_get_vehicle(plate_number, vehicle_type)
        
        cid = f"CH-{datetime.datetime.now().year}-{self.challan_counter}"
        self.challan_counter += 1

        now_str = custom_time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fine = self.VIOLATION_FINES.get(violation_type, 1000)

        challan = Challan(
            challan_id=cid,
            plate_number=plate_number,
            owner_name=record.owner_name,
            vehicle_type=record.vehicle_type,
            violation_type=violation_type,
            fine_amount=fine,
            timestamp=now_str,
            location=location,
            status="PENDING"
        )
        self.challans[cid] = challan
        return challan

    def search_by_plate(self, plate_number: str) -> Dict:
        """Searches vehicle record and all associated challans."""
        clean_plate = plate_number.strip().upper().replace(" ", "-")
        record = self.vehicle_registry.get(clean_plate)
        if not record:
            # Check without hyphens match
            for p, r in self.vehicle_registry.items():
                if p.replace("-", "") == clean_plate.replace("-", ""):
                    record = r
                    clean_plate = p
                    break

        matching_challans = [
            c for c in self.challans.values() if c.plate_number == clean_plate
        ]

        total_pending_fine = sum(c.fine_amount for c in matching_challans if c.status == "PENDING")

        return {
            "found": record is not None,
            "vehicle": record,
            "challans": sorted(matching_challans, key=lambda x: x.timestamp, reverse=True),
            "total_pending_fine": total_pending_fine
        }

    def pay_challan(self, challan_id: str) -> bool:
        """Simulates payment of an e-challan."""
        if challan_id in self.challans:
            c = self.challans[challan_id]
            if c.status == "PENDING":
                c.status = "PAID"
                c.payment_id = f"PAY-ONLINE-{random.randint(100000, 999999)}"
                c.payment_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return True
        return False

    def get_recent_challans(self, limit: int = 15) -> List[Challan]:
        """Returns the most recent violations logged."""
        all_list = list(self.challans.values())
        all_list.sort(key=lambda x: x.timestamp, reverse=True)
        return all_list[:limit]

    def get_summary_stats(self) -> Dict:
        """Returns overall e-challan telemetry."""
        total_issued = len(self.challans)
        paid_count = sum(1 for c in self.challans.values() if c.status == "PAID")
        pending_count = total_issued - paid_count
        total_fine_amount = sum(c.fine_amount for c in self.challans.values())
        collected_fine = sum(c.fine_amount for c in self.challans.values() if c.status == "PAID")

        return {
            "total_issued": total_issued,
            "paid_count": paid_count,
            "pending_count": pending_count,
            "total_fine_amount": total_fine_amount,
            "collected_fine": collected_fine,
        }
