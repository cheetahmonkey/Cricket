import json
import tempfile
import unittest
from pathlib import Path

from cricket import storage
from cricket.models import Listing


class StorageTest(unittest.TestCase):
    def test_blocked_listing_restores_dated_known_details(self):
        original_normalized_dir = storage.NORMALIZED_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            storage.NORMALIZED_DIR = root
            try:
                prior = Listing(
                    listing_id="carter-1",
                    source="Carter source",
                    price=28168,
                    mileage=32356,
                    exterior_color="Crystal Black Silica",
                    vin="JF2GUADC8R8221844",
                    blind_spot_detection="yes",
                ).to_dict()
                (root / "2026-08-12.json").write_text(
                    json.dumps({"qualified": [], "rejected": [prior]}), encoding="utf-8"
                )
                blocked = Listing(
                    listing_id="carter-1",
                    source="Carter source",
                    raw={"detail_access_blocked": True},
                )
                restored = storage.restore_blocked_listing_details("2026-08-15", [blocked])
            finally:
                storage.NORMALIZED_DIR = original_normalized_dir

        self.assertEqual(restored, 1)
        self.assertEqual(blocked.price, 28168)
        self.assertEqual(blocked.mileage, 32356)
        self.assertEqual(blocked.exterior_color, "Crystal Black Silica")
        self.assertEqual(blocked.vin, "JF2GUADC8R8221844")
        self.assertEqual(blocked.blind_spot_detection, "yes")
        self.assertEqual(blocked.raw["historical_fallback"]["last_verified_date"], "2026-08-12")
        self.assertEqual(
            blocked.raw["historical_fallback"]["field_dates"]["price"], "2026-08-12"
        )

    def test_fallback_keeps_original_verification_date_on_later_runs(self):
        original_normalized_dir = storage.NORMALIZED_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            storage.NORMALIZED_DIR = root
            try:
                carried = Listing(
                    listing_id="carter-1",
                    source="Carter source",
                    price=28168,
                    raw={
                        "historical_fallback": {
                            "fields": ["price"],
                            "field_dates": {"price": "2026-08-12"},
                            "last_verified_date": "2026-08-12",
                        }
                    },
                ).to_dict()
                (root / "2026-08-15.json").write_text(
                    json.dumps({"qualified": [], "rejected": [carried]}), encoding="utf-8"
                )
                blocked = Listing(
                    listing_id="carter-1",
                    source="Carter source",
                    raw={"detail_access_blocked": True},
                )
                storage.restore_blocked_listing_details("2026-08-16", [blocked])
            finally:
                storage.NORMALIZED_DIR = original_normalized_dir

        self.assertEqual(blocked.price, 28168)
        self.assertEqual(
            blocked.raw["historical_fallback"]["field_dates"]["price"], "2026-08-12"
        )

    def test_rejected_listing_keeps_its_first_seen_date(self):
        original_data_dir = storage.DATA_DIR
        original_raw_dir = storage.RAW_DIR
        original_normalized_dir = storage.NORMALIZED_DIR
        original_db_path = storage.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            storage.DATA_DIR = root
            storage.RAW_DIR = root / "listings_raw"
            storage.NORMALIZED_DIR = root / "listings_normalized"
            storage.DB_PATH = root / "history.sqlite"
            try:
                first = Listing(listing_id="watch", source="dealer", reject_reason="missing RAB")
                storage.save_history("2026-07-10", [], [first])
                second = Listing(listing_id="watch", source="dealer", reject_reason="missing RAB")
                storage.save_history("2026-07-19", [], [second])
            finally:
                storage.DATA_DIR = original_data_dir
                storage.RAW_DIR = original_raw_dir
                storage.NORMALIZED_DIR = original_normalized_dir
                storage.DB_PATH = original_db_path

        self.assertEqual(first.first_seen_date, "2026-07-10")
        self.assertEqual(second.first_seen_date, "2026-07-10")
        self.assertEqual(second.last_seen_date, "2026-07-19")


if __name__ == "__main__":
    unittest.main()
