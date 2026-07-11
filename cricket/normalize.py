import hashlib
import html
import json
import re
from typing import Any, Dict, Iterable, List, Optional

from .models import Listing


VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value)
    match = re.search(r"[\d,]+", text)
    if not match:
        return None
    return int(match.group(0).replace(",", ""))


def parse_year(text: str) -> Optional[int]:
    match = re.search(r"\b(202[0-6])\b", text)
    return int(match.group(1)) if match else None


def parse_trim(text: str) -> str:
    lower = text.lower()
    for trim in ("Limited", "Sport", "Premium", "Base"):
        if trim.lower() in lower:
            return trim
    return ""


def parse_color(text: str) -> str:
    for color in ["blue", "teal", "burgundy", "green", "white", "black", "silver", "gray", "grey", "red"]:
        if color in text.lower():
            return "gray" if color == "grey" else color.title()
    return ""


def listing_id_from_url(url: str, fallback_text: str) -> str:
    seed = "%s|%s" % (url, fallback_text)
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def listing_from_raw(raw: Dict[str, Any], source_defaults: Dict[str, Any]) -> Listing:
    title = clean_text(raw.get("title") or raw.get("name") or raw.get("vehicle") or "")
    description = clean_text(raw.get("description") or raw.get("text") or "")
    combined = " ".join([title, description, clean_text(raw)])
    url = raw.get("url") or raw.get("@id") or raw.get("source_url") or source_defaults.get("url") or ""
    vin_match = VIN_RE.search(combined)

    year = parse_int(raw.get("year")) or parse_year(combined)
    price_source = raw.get("price")
    if price_source is None and isinstance(raw.get("offers"), dict):
        price_source = raw.get("offers", {}).get("price")
    price = parse_int(price_source)
    mileage = parse_int(raw.get("mileage") or raw.get("vehicleMileage") or raw.get("odometer"))

    make = clean_text(raw.get("make") or ("Subaru" if "subaru" in combined.lower() else ""))
    model = clean_text(raw.get("model") or ("Crosstrek" if "crosstrek" in combined.lower() else ""))
    trim = clean_text(raw.get("trim") or parse_trim(combined))

    listing = Listing(
        listing_id=clean_text(raw.get("listing_id") or raw.get("sku") or raw.get("stockNumber") or listing_id_from_url(url, combined)),
        source=source_defaults.get("source", ""),
        source_url=clean_text(url),
        dealer_name=clean_text(raw.get("dealer_name") or source_defaults.get("dealer_name", "")),
        dealer_type=clean_text(source_defaults.get("dealer_type", "")),
        location=clean_text(raw.get("location") or source_defaults.get("location", "")),
        distance_miles=source_defaults.get("distance_miles"),
        year=year,
        make=make,
        model=model,
        trim=trim,
        price=price,
        mileage=mileage,
        exterior_color=clean_text(raw.get("exterior_color") or raw.get("color") or parse_color(combined)),
        interior_color=clean_text(raw.get("interior_color") or ""),
        drivetrain=clean_text(raw.get("drivetrain") or ("AWD" if "awd" in combined.lower() or "all-wheel" in combined.lower() else "")),
        transmission=clean_text(raw.get("transmission") or ("CVT" if "cvt" in combined.lower() else "")),
        vin=vin_match.group(0) if vin_match else clean_text(raw.get("vin") or ""),
        stock_number=clean_text(raw.get("stock_number") or raw.get("stockNumber") or ""),
        cpo=raw.get("cpo"),
        notes=[description] if description else [],
        raw=raw,
    )

    if "certified" in combined.lower() or source_defaults.get("cpo") is True:
        listing.cpo = True
    if "clean title" in combined.lower():
        listing.title_status = "clean"
    if "no accident" in combined.lower():
        listing.accident_history = "none"
    if "salvage" in combined.lower():
        listing.title_status = "salvage"
    if "rebuilt" in combined.lower():
        listing.title_status = "rebuilt"
    return listing


def extract_json_ld(html_text: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for match in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.I | re.S):
        payload = clean_text(match.group(1))
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if isinstance(candidate, dict):
                graph = candidate.get("@graph")
                if isinstance(graph, list):
                    items.extend([item for item in graph if isinstance(item, dict)])
                items.append(candidate)
    return items


def extract_crosstrek_text_blocks(html_text: str, source_url: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    lower = html_text.lower()
    for match in re.finditer(r".{0,500}crosstrek.{0,1500}", lower, re.S):
        snippet = html_text[match.start() : match.end()]
        text = clean_text(snippet)
        if "subaru" not in text.lower():
            continue
        listing_like = (
            VIN_RE.search(text)
            or (re.search(r"\$[\d,]{4,}", text) and re.search(r"\b\d{1,3},?\d{3}\s*(miles|mi\.?|mile)\b", text, re.I))
            or (re.search(r"\b202[0-6]\b", text) and re.search(r"\b(used|certified|pre-owned|stock|vin)\b", text, re.I))
        )
        if not listing_like:
            continue
        href_match = re.search(r'href=["\']([^"\']+)["\']', snippet, re.I)
        url = href_match.group(1) if href_match else source_url
        if url.startswith("/"):
            base = re.match(r"https?://[^/]+", source_url)
            url = (base.group(0) if base else "") + url
        blocks.append({"title": text[:240], "description": text, "url": url})
    return blocks[:30]


def normalize_items(raw_items: Iterable[Dict[str, Any]], source_defaults: Dict[str, Any]) -> List[Listing]:
    listings = []
    for raw in raw_items:
        listing = listing_from_raw(raw, source_defaults)
        if (listing.make.lower() == "subaru" or "subaru" in str(raw).lower()) and (
            listing.model.lower() == "crosstrek" or "crosstrek" in str(raw).lower()
        ):
            listings.append(listing)
    return listings
