import tempfile
import unittest
from pathlib import Path

from cricket import report
from cricket.models import Listing, SourceResult


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
            history_report_url="https://example.test/carfax",
            reverse_automatic_braking="yes",
            blind_spot_detection="yes",
            rear_cross_traffic_alert="yes",
            feature_confidence="confirmed",
            safety_evidence={
                "RAB": "Automatic emergency braking (rear)",
                "BSD": "Blind spot safety (sensor/alert)",
                "RCTA": "Cross traffic alert (rear)",
            },
            first_seen_date="2026-07-09",
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
            first_seen_date="2026-07-10",
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
                    [
                        SourceResult(
                            source_name="Carter Subaru Shoreline used inventory",
                            raw_items=[{"detail_text_fetched": True}, {}],
                        ),
                        SourceResult(
                            source_name="Renton Subaru used inventory",
                            errors=["inventory feed timed out"],
                        ),
                        SourceResult(source_name="Subaru certified pre-owned inventory"),
                    ],
                    [],
                    [],
                    {},
                    {
                        "previous_date": "2026-07-10",
                        "new_qualified": [qualified],
                        "removed_qualified": [],
                        "new_rejected": [rejected],
                        "removed_rejected": [
                            {
                                "year": 2024,
                                "trim": "Premium",
                                "mileage": 28368,
                                "price": 26080,
                                "dealer_name": "Carter Subaru Shoreline",
                                "source_url": "https://example.test/removed",
                            }
                        ],
                    },
                )
            finally:
                report.REPORTS_DIR = original_reports_dir

            text = path.read_text(encoding="utf-8")

        self.assertIn("Top opportunities since 2026-07-10: +1 new, -0 removed.", text)
        self.assertIn("Watchlist changes: +1 added, -1 removed.", text)
        self.assertIn("New top opportunity: [2025 Limited, 11,196 mi, $31,080, Carter Shoreline](https://example.test/good)", text)
        self.assertIn("Removed watchlist: [2024 Premium, 28,368 mi, $26,080, Carter Shoreline](https://example.test/removed)", text)
        self.assertIn("## Cricket's Morning Note", text)
        self.assertIn("Top opportunities changed: 1 added and 0 removed.", text)
        self.assertIn("| Rank | Score | Color | Year | Trim | Safety | Feature Confidence | Miles | Price | Est. OTD | Seller | Check Before Visiting | Date Added |", text)
        self.assertIn(
            "| 1 | 73 | [Magnetite Gray Metallic](https://example.test/good) | 2025 | Limited | RAB, BSD, RCTA | confirmed | 11,196 | $31,080 | $35,399 | Carter Shoreline | [Open CARFAX](https://example.test/carfax) + Final OTD | 2026-07-09 |",
            text,
        )
        self.assertIn(
            "Safety evidence: RAB: Automatic emergency braking (rear); BSD: Blind spot safety (sensor/alert); RCTA: Cross traffic alert (rear)",
            text,
        )
        self.assertIn("CARFAX report: https://example.test/carfax", text)
        self.assertNotIn("Vehicle history:", text)
        self.assertIn("Cricket is keeping 1 listing visible for comparison", text)
        self.assertIn("| # | Main Concern | Color | Year | Trim | Safety | Feature Confidence | Miles | Price | Est. OTD | Seller | Check Before Visiting | Date Added |", text)
        self.assertIn("| ---: | ------------ | ----- | ---- | ---- | ------ | ------------------ | ----: | ----: | -------: | ------ | --------------------- | ---------- |", text)
        self.assertIn(
            "| 1 | missing required safety evidence | [Unknown](https://example.test/reject) | 2025 | Premium | None confirmed | unknown | 7,845 | Unknown | Unknown | Carter Shoreline | Verify RAB + Review history + Final OTD | 2026-07-10 |",
            text,
        )
        self.assertIn("Estimated OTD = listed price + 11% estimated Washington sales tax + $200 Carter document fee + $700 estimated Washington registration/licensing.", text)
        self.assertIn("## Dealership Sourcing Status", text)
        self.assertIn("| Carter Subaru Shoreline | Active | 2 | 1 |", text)
        self.assertIn("| Renton Subaru | Access issue | 0 | 0 |", text)
        self.assertNotIn("| subaru certified pre-owned |", text.lower())
        self.assertIn("## Scoring Key", text)
        self.assertIn("| Required safety features | 25 |", text)
        self.assertIn("10 points are used when market value is unavailable", text)
        self.assertTrue(text.rstrip().endswith("| **Total** | **100** | Higher scores indicate a stronger overall fit after safety screening |"))
        note = report.morning_note([qualified], {}, {qualified.key(): -223}, {})
        self.assertIn("[2025 Limited](https://example.test/good)", note[0])


if __name__ == "__main__":
    unittest.main()
