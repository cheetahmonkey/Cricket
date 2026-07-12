import unittest

from cricket.cli import apply_manual_overrides
from cricket.models import Listing


class CliTest(unittest.TestCase):
    def test_manual_price_override_accepts_quoted_yaml_keys(self):
        listing = Listing(listing_id="122828072", price=None)
        apply_manual_overrides(listing, {"manual_listing_overrides": {"prices": {'"122828072"': 31300}}})
        self.assertEqual(listing.price, 31300)
        self.assertEqual(listing.price_confidence, "user_verified")
        self.assertEqual(listing.raw["manual_price_override"], 31300)


if __name__ == "__main__":
    unittest.main()
