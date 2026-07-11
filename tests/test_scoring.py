import unittest

from cricket.models import Listing
from cricket.scoring import apply_hard_filters, infer_features, score_listing


CONFIG = {
    "vehicle": {"years_min": 2020, "max_mileage": 45000},
    "color_preferences": {
        "highest": ["blue", "teal"],
        "med_high": ["burgundy", "green"],
        "med": ["white"],
        "low": ["black", "silver", "gray"],
    },
}


class ScoringTest(unittest.TestCase):
    def test_limited_likely_rab_scores_and_passes_filters(self):
        listing = Listing(
            source="test",
            dealer_name="Carter Subaru Shoreline",
            dealer_type="Subaru dealer",
            distance_miles=7,
            year=2023,
            make="Subaru",
            model="Crosstrek",
            trim="Limited",
            mileage=31200,
            price=26900,
            exterior_color="Blue",
            notes=["Blind Spot Detection and Rear Cross Traffic Alert"],
        )
        infer_features(listing)
        score_listing(listing, CONFIG)
        ok, reason = apply_hard_filters(listing, CONFIG)
        self.assertTrue(ok)
        self.assertEqual(reason, "")
        self.assertEqual(listing.feature_confidence, "likely")
        self.assertEqual(listing.color_score, "highest")
        self.assertGreater(listing.score, 70)


if __name__ == "__main__":
    unittest.main()
