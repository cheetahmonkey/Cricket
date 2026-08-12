import tempfile
import unittest
from pathlib import Path

from cricket import report
from cricket.models import Listing, SourceResult


class ReportTest(unittest.TestCase):
    def test_top_picks_use_full_pool_budget_color_and_newest_date(self):
        pricing = {
            "sales_tax_rate": 0.11,
            "dealer_doc_fee": 200,
            "wa_registration_estimate": 700,
        }
        config = {
            "max_out_the_door": 30000,
            "excluded_color_families": ["black", "gray", "grey", "silver", "white"],
            "included_color_exceptions": ["cool gray khaki"],
            "require_known_color": True,
        }

        older_blue_pearl = Listing(
            listing_id="blue",
            exterior_color="Geyser Blue Pearl",
            price=25000,
            first_seen_date="2026-07-10",
        )
        newer_red_pearl_watchlist = Listing(
            listing_id="red",
            exterior_color="Lithium Red Pearl",
            price=24000,
            first_seen_date="2026-07-12",
            reject_reason="missing required safety evidence",
        )
        same_day_lower_otd = Listing(
            listing_id="green",
            exterior_color="Alpine Green",
            price=23000,
            first_seen_date="2026-07-12",
        )
        newest_cool_gray_khaki = Listing(
            listing_id="cool-khaki",
            exterior_color="Cool Gray Khaki",
            price=22000,
            first_seen_date="2026-07-13",
        )
        excluded = [
            Listing(listing_id="white", exterior_color="Crystal White Pearl", price=22000, first_seen_date="2026-07-13"),
            Listing(listing_id="black", exterior_color="Crystal Black Silica", price=22000, first_seen_date="2026-07-13"),
            Listing(listing_id="grey", exterior_color="Cool Grey Khaki", price=22000, first_seen_date="2026-07-13"),
            Listing(listing_id="silver", exterior_color="Ice Silver Metallic", price=22000, first_seen_date="2026-07-13"),
            Listing(listing_id="unknown", exterior_color="", price=22000, first_seen_date="2026-07-13"),
            # This rounds to exactly $30,000 OTD, so it does not satisfy "less than".
            Listing(listing_id="boundary", exterior_color="Sapphire Blue", price=26216, first_seen_date="2026-07-13"),
        ]

        picks = report.select_top_picks_for_mom(
            [older_blue_pearl, same_day_lower_otd, newest_cool_gray_khaki],
            [newer_red_pearl_watchlist] + excluded,
            pricing,
            config,
        )

        self.assertEqual(
            [listing.listing_id for listing in picks],
            ["cool-khaki", "green", "red", "blue"],
        )

    def test_top_picks_table_keeps_watchlist_concern_visible(self):
        watchlist = Listing(
            listing_id="watch",
            source_url="https://example.test/watch",
            dealer_name="Example Subaru",
            year=2021,
            trim="Sport",
            exterior_color="Lithium Red Pearl",
            price=24000,
            mileage=51058,
            first_seen_date="2026-07-30",
            reject_reason="over mileage limit",
        )
        original_reports_dir = report.REPORTS_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            report.REPORTS_DIR = Path(tmpdir)
            try:
                path = report.generate_report(
                    "2026-08-02",
                    [],
                    [watchlist],
                    [],
                    [],
                    [],
                    {},
                    pricing={
                        "sales_tax_rate": 0.11,
                        "dealer_doc_fee": 200,
                        "wa_registration_estimate": 700,
                    },
                    top_picks_config={
                        "max_out_the_door": 30000,
                        "excluded_color_families": ["black", "gray", "grey", "silver", "white"],
                        "included_color_exceptions": ["cool gray khaki"],
                        "require_known_color": True,
                    },
                )
            finally:
                report.REPORTS_DIR = original_reports_dir

            text = path.read_text(encoding="utf-8")

        self.assertIn("| # | Date Added | Color |", text)
        self.assertIn(
            "| 1 | 2026-07-30 | [Lithium Red Pearl](https://example.test/watch) | 2021 | Sport | None confirmed | unknown | 51,058 | $24,000 | $27,540 | Example Subaru | over mileage limit | Verify RAB + Review history + Final OTD |",
            text,
        )
        self.assertEqual(text.count("[Lithium Red Pearl](https://example.test/watch)"), 2)

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
        self.assertIn("## Top Picks for Mom: under $30k + Color", text)
        self.assertIn("No current listings meet Mom's budget and color requirements.", text)
        self.assertLess(
            text.index("## Top Picks for Mom: under $30k + Color"),
            text.index("## Top Opportunities"),
        )
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
        self.assertEqual(
            report.safe_evidence_text('<div id="detailed-specs">Blind spot detection</div>'),
            "confirmed in dealer specifications",
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
