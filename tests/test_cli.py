import unittest

from cricket.cli import apply_manual_overrides, dataset_quality_issues, ensure_dataset_quality
from cricket.models import Listing, SourceResult


class CliTest(unittest.TestCase):
    def test_dataset_quality_rejects_empty_active_source(self):
        result = SourceResult(source_name="Renton Subaru used inventory")
        self.assertIn("discovered no inventory candidates", dataset_quality_issues([result])[0])
        with self.assertRaises(RuntimeError):
            ensure_dataset_quality([result])

    def test_dataset_quality_accepts_majority_historical_coverage(self):
        result = SourceResult(
            source_name="Carter Subaru Ballard used inventory",
            raw_items=[
                {"historical_fallback": {"last_verified_date": "2026-08-31"}},
                {"detail_text_fetched": True},
                {},
            ],
        )
        self.assertEqual(dataset_quality_issues([result]), [])

    def test_dataset_quality_ignores_empty_supplemental_cpo_source(self):
        result = SourceResult(source_name="Subaru certified pre-owned inventory")
        self.assertEqual(dataset_quality_issues([result]), [])

    def test_manual_price_override_accepts_quoted_yaml_keys(self):
        listing = Listing(listing_id="122828072", price=None)
        apply_manual_overrides(listing, {"manual_listing_overrides": {"prices": {'"122828072"': 31300}}})
        self.assertEqual(listing.price, 31300)
        self.assertEqual(listing.price_confidence, "user_verified")
        self.assertEqual(listing.raw["manual_price_override"], 31300)


if __name__ == "__main__":
    unittest.main()
