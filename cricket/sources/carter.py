import re
import xml.etree.ElementTree as ET
from html import unescape
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
        enriched_count = 0
        for sitemap_url in self.sitemap_urls():
            try:
                xml_text = self.fetch(sitemap_url)
                raw_items = self.parse_sitemap(xml_text, sitemap_url)
                unique_items = []
                for item in raw_items:
                    key = item.get("listing_id") or item["url"]
                    if key in seen:
                        continue
                    seen.add(key)
                    enriched = self.enrich_from_detail_text(item, enriched_count)
                    if enriched.get("detail_text_fetched"):
                        enriched_count += 1
                    unique_items.append(enriched)
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

    def detail_text_url(self, vehicle_url: str) -> str:
        template = self.config.get("detail_text_url_template")
        if not template:
            return vehicle_url
        return template.format(url=vehicle_url)

    def enrich_from_detail_text(self, raw: Dict, enriched_count: int = 0) -> Dict:
        max_enrichments = self.config.get("max_detail_enrichments")
        if isinstance(max_enrichments, int) and enriched_count >= max_enrichments:
            return raw

        detail_url = self.detail_text_url(raw["url"])
        try:
            detail_text = self.fetch(detail_url)
        except OSError as exc:
            raw.setdefault("detail_errors", []).append("%s: %s" % (detail_url, exc))
            return raw

        raw["detail_text_url"] = detail_url
        raw["detail_text_fetched"] = True
        parsed = parse_carter_detail_text(detail_text)
        if parsed.get("price") is None and self.config.get("detail_direct_fallback_on_missing_price") and detail_url != raw["url"]:
            try:
                direct_text = self.fetch(raw["url"])
                raw["detail_direct_url"] = raw["url"]
                direct_parsed = parse_carter_detail_text(direct_text)
                parsed.update({key: value for key, value in direct_parsed.items() if value not in (None, "", [])})
            except OSError as exc:
                raw.setdefault("detail_errors", []).append("%s: %s" % (raw["url"], exc))
        raw.update({key: value for key, value in parsed.items() if value not in (None, "", [])})
        return raw

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


def parse_carter_detail_text(text: str) -> Dict:
    lines = [unescape(line).strip() for line in text.splitlines()]
    non_empty = [line for line in lines if line]
    parsed: Dict = {}

    title = first_match(non_empty, r"^#\s*(Certified|Used|Used Certified).*?(\d{4})\s+Subaru\s+Crosstrek\s+(.+?)\s+(near|in)\b")
    if title:
        parsed["year"] = int(title.group(2))
        parsed["make"] = "Subaru"
        parsed["model"] = "Crosstrek"
        parsed["trim"] = clean_trim(title.group(3))
        parsed["cpo"] = "certified" in title.group(1).lower()

    price = parse_price(non_empty, text)
    if price is not None:
        parsed["price"] = price

    field_map = {
        "Mileage": "mileage",
        "Trim": "trim",
        "Stock #": "stock_number",
        "VIN": "vin",
        "Exterior Color": "exterior_color",
        "Interior Color": "interior_color",
        "Transmission": "transmission",
        "Drivetrain": "drivetrain",
    }
    for label, key in field_map.items():
        value = value_after_label(non_empty, label)
        if value:
            parsed[key] = int(value.replace(",", "")) if key == "mileage" else value

    if any("subaru certified pre-owned" in line.lower() for line in non_empty):
        parsed["cpo"] = True
    if any("one-owner" in line.lower() or "1-owner" in line.lower() for line in non_empty):
        parsed["owners"] = 1
    history_url = first_match(non_empty, r"\]\((https://www\.carfax\.com/vehiclehistory/[^)]+)\)")
    if history_url:
        parsed["history_report_url"] = history_url.group(1)
    evidence = {}
    rab_line = first_line_containing(non_empty, ["automatic emergency braking (rear)"])
    bsd_line = first_line_containing(non_empty, ["blind spot"])
    rcta_line = first_line_containing(non_empty, ["cross traffic alert (rear)"]) or first_line_containing(non_empty, ["rear cross-traffic alert"])
    rear_camera_line = first_line_containing(non_empty, ["camera system (rearview)"]) or first_line_containing(non_empty, ["reverse camera"])

    if rab_line:
        parsed["reverse_automatic_braking"] = "yes"
        evidence["RAB"] = rab_line
    if bsd_line:
        parsed["blind_spot_detection"] = "yes"
        evidence["BSD"] = bsd_line
    if rcta_line:
        parsed["rear_cross_traffic_alert"] = "yes"
        evidence["RCTA"] = rcta_line
    if rear_camera_line:
        parsed["rear_camera"] = "yes"
        evidence["rear_camera"] = rear_camera_line
    if evidence:
        parsed["safety_evidence"] = evidence

    notes = detail_notes(non_empty)
    if notes:
        parsed["description"] = " ".join(notes)
    return parsed


def first_match(lines: List[str], pattern: str):
    for line in lines:
        match = re.search(pattern, line, re.I)
        if match:
            return match
    return None


def first_line_containing(lines: List[str], tokens: List[str]):
    for line in lines:
        lower = line.lower()
        if any(token in lower for token in tokens):
            return line
    return ""


def parse_price(lines: List[str], full_text: str = ""):
    inline_price = first_match(lines, r"Carter Price\s+\$?([\d,]+)")
    if inline_price:
        return int(inline_price.group(1).replace(",", ""))
    text_price = re.search(r"Carter Price\b.{0,500}?\$?\s*([\d,]{5,})", full_text, re.I | re.S)
    if text_price:
        return int(text_price.group(1).replace(",", ""))
    label_price = value_after_label(lines, "Carter Price")
    if label_price:
        parsed = price_from_text(label_price)
        if parsed is not None:
            return parsed
    for index, line in enumerate(lines):
        if line.lower() == "carter price":
            for candidate in lines[index + 1 : index + 6]:
                parsed = price_from_text(candidate)
                if parsed is not None:
                    return parsed
    return None


def price_from_text(value: str):
    match = re.search(r"\$?\s*([\d,]{5,})", value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def value_after_label(lines: List[str], label: str):
    for index, line in enumerate(lines):
        if line.strip().lower() == label.lower() and index + 1 < len(lines):
            return lines[index + 1].strip()
    return None


def clean_trim(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\s+(near|in)\s+.*$", "", value, flags=re.I)
    return value


def detail_notes(lines: List[str]) -> List[str]:
    wanted = []
    for line in lines:
        lower = line.lower()
        if any(token in lower for token in [
            "heated seat",
            "keyless",
            "push-button",
            "blind-spot detection",
            "rear cross-traffic alert",
            "power moonroof",
            "subaru certified pre-owned",
            "automatic emergency braking",
        ]):
            wanted.append(line)
    return wanted[:30]
