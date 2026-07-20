import tempfile
import unittest
from pathlib import Path

from cricket import storage
from cricket.models import Listing


class StorageTest(unittest.TestCase):
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
