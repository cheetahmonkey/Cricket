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
                normalized_items = unique_items
                if self.config.get("normalize_only_enriched"):
                    normalized_items = [item for item in unique_items if item.get("detail_text_fetched")]
                result.listings.extend(normalize_items(normalized_items, self.source_defaults(sitemap_url)))
            except (ET.ParseError, OSError) as exc:
                result.errors.append("%s: %s" % (sitemap_url, exc))

        if not result.raw_items and (self.config.get("urls") or self.config.get("url")):
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
        if "<urlset" in xml_text or "<sitemapindex" in xml_text:
            root = ET.fromstring(xml_text)
            candidate_urls = [(loc.text or "").strip() for loc in root.findall(".//{*}loc")]
        else:
            # The text mirror renders public sitemaps as Markdown links.
            candidate_urls = re.findall(r"\]\((https?://[^)]+)\)", xml_text)
        urls: List[Dict] = []
        for url in candidate_urls:
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


class LocalSubaruSource(CarterSource):
    """Read standard dealer eProcess inventory sitemaps conservatively.

    These dealers publish individual inventory URLs in their sitemaps, but use a
    different URL layout than Carter.  Detail enrichment is intentionally capped
    in configuration so the daily search is not a page crawl.
    """

    def parse_sitemap(self, xml_text: str, sitemap_url: str) -> List[Dict]:
        if "<urlset" in xml_text or "<sitemapindex" in xml_text:
            root = ET.fromstring(xml_text)
            candidate_urls = [(loc.text or "").strip() for loc in root.findall(".//{*}loc")]
        else:
            # The text mirror renders public sitemaps as Markdown links.
            candidate_urls = re.findall(r"\]\((https?://[^)]+)\)", xml_text)
        urls: List[Dict] = []
        for url in candidate_urls:
            lower = url.lower()
            if "subaru-crosstrek" not in lower:
                continue
            if not re.search(r"/(used|certified)/subaru/", lower):
                continue
            raw = self.raw_from_vehicle_url(url)
            raw["sitemap_url"] = sitemap_url
            urls.append(raw)
        return urls

    def raw_from_vehicle_url(self, url: str) -> Dict:
        match = re.search(
            r"/(used|certified)/subaru/(\d{4})-subaru-crosstrek-for-sale-[^/]*-([a-f0-9]{16,})\.htm$",
            url,
            re.I,
        )
        raw: Dict = {
            "url": url,
            "title": url.rstrip("/").split("/")[-1].replace(".htm", "").replace("-", " "),
            "description": "Dealer-advertised inventory sitemap candidate. Detail page is needed for price, mileage, color, and safety-feature evidence.",
            "source_kind": "dealer_standard_inventory_sitemap",
        }
        if match:
            raw["condition"] = match.group(1)
            raw["year"] = int(match.group(2))
            raw["make"] = "Subaru"
            raw["model"] = "Crosstrek"
            raw["listing_id"] = match.group(3)
            raw["cpo"] = match.group(1).lower() == "certified"
        return raw

    def enrich_from_detail_text(self, raw: Dict, enriched_count: int = 0) -> Dict:
        minimum_year = self.config.get("minimum_detail_year")
        if isinstance(minimum_year, int) and isinstance(raw.get("year"), int) and raw["year"] < minimum_year:
            return raw
        return super().enrich_from_detail_text(raw, enriched_count)


def parse_carter_detail_text(text: str) -> Dict:
    lines = [unescape(line).strip() for line in text.splitlines()]
    if "<html" in text.lower():
        # A few standard dealer pages expose their vehicle overview only in
        # server-rendered HTML and embedded JSON rather than visible text.
        lines.append(unescape(re.sub(r"<[^>]+>", " ", text)).strip())
    non_empty = [line for line in lines if line]
    parsed: Dict = {}

    html_title = re.search(r"<title[^>]*>\s*(.*?)\s*</title>", text, re.I | re.S)
    if html_title:
        title_text = unescape(re.sub(r"<[^>]+>", " ", html_title.group(1))).strip()
        title_match = re.search(
            r"(?:Used|Certified(?: Pre-Owned)?)\s+(\d{4})\s+Subaru\s+Crosstrek\s+(.+?)\s+(?:in|for)\b",
            title_text,
            re.I,
        )
        if title_match:
            parsed["year"] = int(title_match.group(1))
            parsed["make"] = "Subaru"
            parsed["model"] = "Crosstrek"
            parsed["trim"] = clean_trim(title_match.group(2))
            parsed["cpo"] = "certified" in title_text.lower()

    title = first_match(non_empty, r"^#\s*(Certified|Used|Used Certified).*?(\d{4})\s+Subaru\s+Crosstrek\s+(.+?)\s+(near|in)\b")
    if title:
        parsed["year"] = int(title.group(2))
        parsed["make"] = "Subaru"
        parsed["model"] = "Crosstrek"
        parsed["trim"] = clean_trim(title.group(3))
        parsed["cpo"] = "certified" in title.group(1).lower()

    standard_title = first_match(non_empty, r"^#{0,2}\s*(\d{4})\s+Subaru\s+Crosstrek\s+(.+?)\s*$")
    if standard_title:
        parsed.setdefault("year", int(standard_title.group(1)))
        parsed.setdefault("make", "Subaru")
        parsed.setdefault("model", "Crosstrek")
        parsed.setdefault("trim", clean_trim(standard_title.group(2)))

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
            if key == "mileage":
                mileage = parse_mileage(value)
                if mileage is not None:
                    parsed[key] = mileage
            else:
                parsed[key] = value

    # Standard eProcess dealer detail pages expose the overview in compact
    # prose rather than Carter's label/value lines.
    detail_text = " ".join(non_empty)
    standard_price = parse_standard_dealer_price(detail_text)
    if price is None and standard_price is not None:
        parsed["price"] = standard_price
    standard_mileage = re.search(r"\bOdometer\s+([\d,]+)\s+miles?\b", detail_text, re.I)
    if "mileage" not in parsed and standard_mileage:
        parsed["mileage"] = int(standard_mileage.group(1).replace(",", ""))
    standard_color = re.search(r"\bExterior Color\s+(.+?)\s+Interior Color\b", detail_text, re.I)
    if "exterior_color" not in parsed and standard_color:
        parsed["exterior_color"] = standard_color.group(1).strip()
    standard_interior = re.search(r"\bInterior Color\s+(.+?)\s+Odometer\b", detail_text, re.I)
    if "interior_color" not in parsed and standard_interior:
        parsed["interior_color"] = standard_interior.group(1).strip()
    standard_overview = re.search(
        r"\bTransmission\s+(.+?)\s+Drivetrain\s+(.+?)\s+Engine\s+(.+?)\s+VIN\s+([A-HJ-NPR-Z0-9]{17})\s+Stock Number\s+(\S+)",
        detail_text,
        re.I,
    )
    if standard_overview:
        parsed.setdefault("transmission", standard_overview.group(1).strip())
        parsed.setdefault("drivetrain", standard_overview.group(2).strip())
        parsed.setdefault("vin", standard_overview.group(4).upper())
        parsed.setdefault("stock_number", standard_overview.group(5).strip())

    if any("subaru certified" in line.lower() for line in non_empty):
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
    rear_camera_line = first_line_containing(non_empty, ["camera system (rearview)"]) or first_line_containing(non_empty, ["reverse camera"]) or first_line_containing(non_empty, ["parking camera rear"])

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


def parse_standard_dealer_price(text: str):
    """Use the advertised asking price before dealer documentation fees."""
    match = re.search(r"\$\s*([\d,]{5,})\s+Asking Price\b", text, re.I)
    if match:
        return int(match.group(1).replace(",", ""))
    match = re.search(r"\bAsking Price\s*\$?\s*([\d,]{5,})", text, re.I)
    if match:
        return int(match.group(1).replace(",", ""))
    match = re.search(r'"internetPrice"\s*:\s*"?([\d,]{5,})', text, re.I)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def price_from_text(value: str):
    match = re.search(r"\$?\s*([\d,]{5,})", value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def parse_mileage(value: str):
    """Return a mileage only when the dealer's value is a numeric field."""
    compact = value.replace(",", "").strip()
    if not compact.isdigit():
        return None
    return int(compact)


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
