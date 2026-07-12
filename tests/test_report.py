import tempfile
import unittest
from pathlib import Path

from cricket import report
from cricket.models import Listing


class ReportTest(unittest.TestCase):
    def test_report_shows_rear_package_safety_and_rejected_links(self):
        qualified = Listing(
            listing_id="good",
            year=2025,
            make="Subaru",
            model="Crosstrek",
            trim="Limited",
            mileage=11196,
            price=31080,
            exterior_color="Magnetite Gray Metallic",
            dealer_name="Carter Subaru Shoreline",
            source_url="https://example.test/good",
            reverse_automatic_braking="yes",
            blind_spot_detection="yes",
            rear_cross_traffic_alert="yes",
            feature_confidence="confirmed",
            safety_evidence={
                "RAB": "Automatic emergency braking (rear)",
                "BSD": "Blind spot safety (sensor/alert)",
                "RCTA": "Cross traffic alert (rear)",
            },
            score=73,
        )
        rejected = Listing(
            listing_id="reject",
            year=2025,
            make="Subaru",
            model="Crosstrek",
            trim="Premium",
            mileage=7845,
            dealer_name="Carter Subaru Shoreline",
            source_url="https://example.test/reject",
            reject_reason="missing required safety evidence",
        )

        original_reports_dir = report.REPORTS_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            report.REPORTS_DIR = Path(tmpdir)
            try:
                path = report.generate_report(
                    "2026-07-11",
                    [qualified],
                    [rejected],
                    [],
                    [],
                    [],
                    {},
                )
            finally:
                report.REPORTS_DIR = original_reports_dir

            text = path.read_text(encoding="utf-8")

        self.assertIn("| Rank | Score | Year | Trim | Safety | Feature Confidence | Miles | Price | Color | Seller | Distance |", text)
        self.assertIn(
            "| 1 | 73 | 2025 | Limited | RAB, BSD, RCTA | confirmed | 11,196 | $31,080 | [Magnetite Gray Metallic](https://example.test/good) | Carter Shoreline | Unknown |",
            text,
        )
        self.assertIn(
            "Safety evidence: RAB: Automatic emergency braking (rear); BSD: Blind spot safety (sensor/alert); RCTA: Cross traffic alert (rear)",
            text,
        )
        self.assertIn("Rejected listings: 1\n\n| # | Reason | Year | Trim | Safety | Feature Confidence | Miles | Price | Color | Seller | Distance |", text)
        self.assertIn("| ---: | ------ | ---- | ---- | ------ | ------------------ | ----: | ----: | ----- | ------ | -------: |", text)
        self.assertIn(
            "| 1 | missing required safety evidence | 2025 | Premium | None confirmed | unknown | 7,845 | Unknown | [Unknown](https://example.test/reject) | Carter Shoreline | Unknown |",
            text,
        )


if __name__ == "__main__":
    unittest.main()
