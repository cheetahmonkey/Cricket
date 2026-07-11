import time
import urllib.error
import urllib.request
from typing import Dict, List

from ..models import SourceResult
from ..normalize import extract_crosstrek_text_blocks, extract_json_ld, normalize_items


class SourceAdapter:
    user_agent = "CricketSubaruSearch/0.1 (+local manual buyer research)"

    def __init__(self, source_config: Dict):
        self.config = source_config

    @property
    def name(self) -> str:
        return self.config.get("name", self.__class__.__name__)

    def urls(self) -> List[str]:
        if self.config.get("urls"):
            return self.config["urls"]
        return [self.config["url"]]

    def source_defaults(self, url: str) -> Dict:
        distance = self.config.get("distance_miles")
        if not isinstance(distance, (int, float)):
            distance = None
        return {
            "source": self.name,
            "url": url,
            "dealer_name": self.config.get("dealer_name", ""),
            "dealer_type": self.config.get("dealer_type", ""),
            "location": self.config.get("location", ""),
            "distance_miles": distance,
        }

    def fetch(self, url: str) -> str:
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")

    def parse_html(self, html_text: str, url: str) -> List[Dict]:
        raw_items: List[Dict] = []
        for item in extract_json_ld(html_text):
            text = str(item).lower()
            item_type = str(item.get("@type", "")).lower()
            if "vehicle" in item_type or "car" in item_type or "crosstrek" in text:
                item.setdefault("url", item.get("url") or url)
                raw_items.append(item)
        raw_items.extend(extract_crosstrek_text_blocks(html_text, url))
        return raw_items

    def search(self) -> SourceResult:
        result = SourceResult(source_name=self.name)
        for url in self.urls():
            try:
                html_text = self.fetch(url)
                raw_items = self.parse_html(html_text, url)
                result.raw_items.extend(raw_items)
                result.listings.extend(normalize_items(raw_items, self.source_defaults(url)))
                time.sleep(0.5)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                result.errors.append("%s: %s" % (url, exc))
        return result
