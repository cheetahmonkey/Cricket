import unittest

from cricket.sources.carter import CarterSource, parse_carter_detail_text


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

    def test_parse_detail_text_extracts_scoring_fields(self):
        text = """
        # Certified 2025 Subaru Crosstrek Limited near Edmonds, WA
        Carter Price  $31,080
        Mileage
        11,196
        Trim
        Limited
        Stock #
        1527SLR
        VIN
        4S4GUHM67S3721610
        Exterior Color
        Magnetite Gray Metallic
        Interior Color
        Black
        Transmission
        Lineartronic CVT
        Drivetrain
        AWD
        Automatic emergency braking (rear)
        Blind spot safety (sensor/alert)
        Camera system (rearview)
        Cross traffic alert (rear)
        Driver seat (heated)
        Push-button start
        Subaru Certified Pre-Owned vehicle
        [![Image 31: Show Me the CARFAX 1-Owner Badge](https://partnerstatic.carfax.com/img/valuebadge/1own.svg)](https://www.carfax.com/vehiclehistory/ar20/example-token)
        """
        parsed = parse_carter_detail_text(text)
        self.assertEqual(parsed["price"], 31080)
        self.assertEqual(parsed["mileage"], 11196)
        self.assertEqual(parsed["trim"], "Limited")
        self.assertEqual(parsed["stock_number"], "1527SLR")
        self.assertEqual(parsed["vin"], "4S4GUHM67S3721610")
        self.assertEqual(parsed["exterior_color"], "Magnetite Gray Metallic")
        self.assertEqual(parsed["transmission"], "Lineartronic CVT")
        self.assertEqual(parsed["drivetrain"], "AWD")
        self.assertTrue(parsed["cpo"])
        self.assertEqual(parsed["owners"], 1)
        self.assertEqual(parsed["history_report_url"], "https://www.carfax.com/vehiclehistory/ar20/example-token")
        self.assertEqual(parsed["reverse_automatic_braking"], "yes")
        self.assertEqual(parsed["blind_spot_detection"], "yes")
        self.assertEqual(parsed["rear_camera"], "yes")
        self.assertEqual(parsed["rear_cross_traffic_alert"], "yes")
        self.assertEqual(parsed["safety_evidence"]["RAB"], "Automatic emergency braking (rear)")
        self.assertEqual(parsed["safety_evidence"]["BSD"], "Blind spot safety (sensor/alert)")
        self.assertEqual(parsed["safety_evidence"]["RCTA"], "Cross traffic alert (rear)")

    def test_parse_detail_text_accepts_ballard_in_city_title(self):
        text = """
        # Used Certified One-Owner 2025 Subaru Crosstrek Limited in Seattle, WA
        Carter Price  $31,995
        Mileage
        4,575
        Automatic emergency braking (rear)
        Blind spot safety (sensor/alert)
        Camera system (rearview)
        Cross traffic alert (rear)
        """
        parsed = parse_carter_detail_text(text)
        self.assertEqual(parsed["year"], 2025)
        self.assertEqual(parsed["trim"], "Limited")
        self.assertEqual(parsed["mileage"], 4575)
        self.assertEqual(parsed["reverse_automatic_braking"], "yes")
        self.assertEqual(parsed["safety_evidence"]["RAB"], "Automatic emergency braking (rear)")

    def test_parse_detail_text_accepts_multiline_ballard_price(self):
        text = """
        # Used Certified One-Owner 2025 Subaru Crosstrek Limited in Seattle, WA
        Price
        $31,111
        Doc Fee
        +$200
        Carter Price
        QUALIFIES FOR THE IRS TAX CREDIT TRANSFER REBATE. SEE DEALER FOR DETAILS
        $31,311
        Mileage
        4,575
        """
        parsed = parse_carter_detail_text(text)
        self.assertEqual(parsed["price"], 31311)
        self.assertEqual(parsed["mileage"], 4575)

    def test_search_tries_direct_detail_when_text_mirror_has_no_price(self):
        sitemap = """<?xml version="1.0"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://www.cartersubaruballard.com/auto/used-2025-subaru-crosstrek-premium-seattle-wa/122828078/</loc></url>
        </urlset>
        """
        mirror_detail = """
        # Certified 2025 Subaru Crosstrek Premium in Seattle, WA
        Mileage
        3,363
        """
        direct_detail = """
        # Certified 2025 Subaru Crosstrek Premium in Seattle, WA
        Carter Price QUALIFIES FOR THE IRS TAX CREDIT TRANSFER REBATE $28,795
        Mileage
        3,363
        """

        class FixtureCarterSource(CarterSource):
            def __init__(self):
                super().__init__(
                    {
                        "name": "Carter Subaru Ballard",
                        "sitemap_urls": ["https://example.test/sitemap.xml"],
                        "detail_text_url_template": "https://details.example/{url}",
                        "detail_direct_fallback_on_missing_price": True,
                        "dealer_name": "Carter Subaru Ballard",
                    }
                )

            def fetch(self, url):
                if url == "https://example.test/sitemap.xml":
                    return sitemap
                if url.startswith("https://details.example/"):
                    return mirror_detail
                return direct_detail

        source = FixtureCarterSource()
        result = source.search()
        self.assertEqual(result.raw_items[0]["price"], 28795)
        self.assertEqual(result.raw_items[0]["detail_direct_url"], "https://www.cartersubaruballard.com/auto/used-2025-subaru-crosstrek-premium-seattle-wa/122828078/")

    def test_search_deduplicates_city_slug_variants_by_listing_id(self):
        sitemap = """<?xml version="1.0"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url><loc>https://www.cartersubarushoreline.com/auto/used-2025-subaru-crosstrek-limited-near-edmonds-wa/122778458/</loc></url>
          <url><loc>https://www.cartersubarushoreline.com/auto/used-2025-subaru-crosstrek-limited-seattle-wa/122778458/</loc></url>
        </urlset>
        """
        detail = """
        # Certified 2025 Subaru Crosstrek Limited near Edmonds, WA
        Carter Price  $31,080
        Mileage
        11,196
        VIN
        4S4GUHM67S3721610
        Automatic emergency braking (rear)
        Blind spot safety (sensor/alert)
        Camera system (rearview)
        Cross traffic alert (rear)
        [![Image 31: Show Me the CARFAX 1-Owner Badge](https://partnerstatic.carfax.com/img/valuebadge/1own.svg)](https://www.carfax.com/vehiclehistory/ar20/example-token)
        """

        class FixtureCarterSource(CarterSource):
            def __init__(self):
                super().__init__(
                    {
                        "name": "Carter Subaru Shoreline used inventory",
                        "sitemap_urls": ["https://example.test/sitemap.xml"],
                        "detail_text_url_template": "https://details.example/{url}",
                        "max_detail_enrichments": 12,
                        "dealer_name": "Carter Subaru Shoreline",
                    }
                )
                self.detail_fetches = 0

            def fetch(self, url):
                if url == "https://example.test/sitemap.xml":
                    return sitemap
                self.detail_fetches += 1
                return detail

        source = FixtureCarterSource()
        result = source.search()
        self.assertEqual(len(result.raw_items), 1)
        self.assertEqual(source.detail_fetches, 1)
        self.assertEqual(result.raw_items[0]["listing_id"], "122778458")
        self.assertEqual(result.listings[0].mileage, 11196)
        self.assertEqual(result.listings[0].owners, 1)
        self.assertEqual(result.listings[0].history_report_url, "https://www.carfax.com/vehiclehistory/ar20/example-token")
        self.assertEqual(result.listings[0].safety_evidence["RAB"], "Automatic emergency braking (rear)")


if __name__ == "__main__":
    unittest.main()
