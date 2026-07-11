import re
import xml.etree.ElementTree as ET
from typing import Dict, List

from ..models import SourceResult
from ..normalize import normalize_items
from .base import SourceAdapter


class CarterSource(SourceAdapter):
    def sitemap_urls(self) -> List[str]:
        return self.config.get("sitemap_urls") or []

    def search(self) -> SourceResult:
        if not self.sitemap_urls():
            return super().search()

        result = SourceResult(source_name=self.name)
        seen = set()
        for sitemap_url in self.sitemap_urls():
            try:
                xml_text = self.fetch(sitemap_url)
                raw_items = self.parse_sitemap(xml_text, sitemap_url)
                unique_items = []
                for item in raw_items:
                    if item["url"] in seen:
                        continue
                    seen.add(item["url"])
                    unique_items.append(item)
                result.raw_items.extend(unique_items)
                result.listings.extend(normalize_items(unique_items, self.source_defaults(sitemap_url)))
            except (ET.ParseError, OSError) as exc:
                result.errors.append("%s: %s" % (sitemap_url, exc))

        if not result.raw_items:
            fallback = super().search()
            result.errors.extend(fallback.errors)
            result.raw_items.extend(fallback.raw_items)
            result.listings.extend(fallback.listings)
        return result

    def parse_sitemap(self, xml_text: str, sitemap_url: str) -> List[Dict]:
        root = ET.fromstring(xml_text)
        urls: List[Dict] = []
        for loc in root.findall(".//{*}loc"):
            url = (loc.text or "").strip()
            lower = url.lower()
            if "/auto/used-" not in lower:
                continue
            if "subaru-crosstrek" not in lower:
                continue
            raw = self.raw_from_vehicle_url(url)
            raw["sitemap_url"] = sitemap_url
            urls.append(raw)
        return urls

    def raw_from_vehicle_url(self, url: str) -> Dict:
        match = re.search(r"/auto/(used)-(\d{4})-subaru-crosstrek-([^/]+)/(\d+)/?", url, re.I)
        title = url.rstrip("/").split("/")[-2].replace("-", " ")
        raw: Dict = {
            "url": url,
            "title": title,
            "description": "Carter robots-advertised inventory sitemap candidate. Detail page is needed for price, mileage, VIN, color, and safety-feature evidence.",
            "source_kind": "dealer_eprocess_inventory_sitemap",
        }
        if match:
            raw["condition"] = match.group(1)
            raw["year"] = int(match.group(2))
            raw["make"] = "Subaru"
            raw["model"] = "Crosstrek"
            raw["listing_id"] = match.group(4)
            trim_tokens = match.group(3).split("-near-", 1)[0].split("-seattle-", 1)[0].split("-edmonds-", 1)[0]
            trim = " ".join(token.capitalize() for token in trim_tokens.split("-") if token)
            raw["trim"] = trim
        return raw


class LocalSubaruSource(SourceAdapter):
    pass
