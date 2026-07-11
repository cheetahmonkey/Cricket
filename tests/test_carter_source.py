import unittest

from cricket.sources.carter import CarterSource


class CarterSourceTest(unittest.TestCase):
    def test_parse_sitemap_used_crosstrek_urls(self):
        source = CarterSource({"name": "Carter Subaru Shoreline used inventory"})
        xml = """<?xml version="1.0"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://www.cartersubarushoreline.com/auto/new-2026-subaru-crosstrek-limited-near-edmonds-wa/1/</loc></url>
          <url><loc>https://www.cartersubarushoreline.com/auto/used-2023-subaru-crosstrek-sport-near-edmonds-wa/122620058/</loc></url>
          <url><loc>https://www.cartersubarushoreline.com/auto/used-2023-subaru-forester-premium-near-edmonds-wa/119734886/</loc></url>
        </urlset>
        """
        items = source.parse_sitemap(xml, "https://example.test/sitemap")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["listing_id"], "122620058")
        self.assertEqual(items[0]["year"], 2023)
        self.assertEqual(items[0]["trim"], "Sport")
        self.assertEqual(items[0]["model"], "Crosstrek")


if __name__ == "__main__":
    unittest.main()
