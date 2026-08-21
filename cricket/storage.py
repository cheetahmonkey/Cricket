import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .models import Listing, SourceResult


DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "listings_raw"
NORMALIZED_DIR = DATA_DIR / "listings_normalized"
DB_PATH = DATA_DIR / "listings_history.sqlite"


HISTORICAL_DETAIL_FIELDS = (
    "price",
    "mileage",
    "exterior_color",
    "interior_color",
    "drivetrain",
    "transmission",
    "vin",
    "stock_number",
    "cpo",
    "owners",
    "history_report_url",
    "rear_camera",
    "blind_spot_detection",
    "rear_cross_traffic_alert",
    "reverse_automatic_braking",
    "safety_evidence",
)


def known_detail_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "unknown", "n/a", "na", "not available", "not specified"}
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def historical_field_date(payload: Dict, field: str, snapshot_date: str) -> str:
    fallback = payload.get("raw", {}).get("historical_fallback", {})
    if not isinstance(fallback, dict):
        return snapshot_date
    field_dates = fallback.get("field_dates", {})
    if isinstance(field_dates, dict) and field_dates.get(field):
        return str(field_dates[field])
    return str(fallback.get("last_verified_date") or snapshot_date)


def restore_blocked_listing_details(date: str, listings: Iterable[Listing]) -> int:
    """Restore last-known dealer facts only after a detail access challenge.

    Each restored field keeps the date of the source snapshot where it was last
    directly known. A fallback snapshot can therefore be used on later runs
    without making an old price or mileage appear newly verified.
    """
    targets = {
        (listing.source, listing.listing_id): listing
        for listing in listings
        if listing.listing_id and listing.raw.get("detail_access_blocked")
    }
    if not targets:
        return 0

    restored_fields: Dict[Tuple[str, str], Dict[str, str]] = {key: {} for key in targets}
    candidates = sorted(
        (path for path in NORMALIZED_DIR.glob("*.json") if path.stem < date),
        reverse=True,
    )
    for path in candidates:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for prior in payload.get("qualified", []) + payload.get("rejected", []):
            key = (prior.get("source", ""), prior.get("listing_id"))
            listing = targets.get(key)
            if listing is None:
                continue
            for field in HISTORICAL_DETAIL_FIELDS:
                if field in restored_fields[key]:
                    continue
                current_value = getattr(listing, field)
                prior_value = prior.get(field)
                if known_detail_value(current_value) or not known_detail_value(prior_value):
                    continue
                setattr(listing, field, prior_value)
                listing.raw[field] = prior_value
                restored_fields[key][field] = historical_field_date(prior, field, path.stem)

    restored_listings = 0
    for key, field_dates in restored_fields.items():
        if not field_dates:
            continue
        listing = targets[key]
        # Use the oldest restored field date for the single report-facing date.
        # Per-field dates remain available in metadata for exact auditing.
        last_verified_date = min(field_dates.values())
        listing.raw["historical_fallback"] = {
            "fields": sorted(field_dates),
            "field_dates": dict(sorted(field_dates.items())),
            "last_verified_date": last_verified_date,
        }
        listing.notes.append(
            "Dealer detail access was blocked; known fields were restored from Cricket history, last verified through %s."
            % last_verified_date
        )
        restored_listings += 1
    return restored_listings


def ensure_storage() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            create table if not exists listings (
                listing_key text primary key,
                first_seen_date text not null,
                last_seen_date text not null,
                last_price integer,
                last_mileage integer,
                payload_json text not null
            )
            """
        )
        conn.execute(
            """
            create table if not exists listing_snapshots (
                id integer primary key autoincrement,
                run_date text not null,
                listing_key text not null,
                price integer,
                mileage integer,
                score integer,
                payload_json text not null
            )
            """
        )
        conn.execute(
            """
            create table if not exists rejected_listings (
                id integer primary key autoincrement,
                run_date text not null,
                listing_key text not null,
                reject_reason text not null,
                payload_json text not null
            )
            """
        )


def save_raw(date: str, source_results: List[SourceResult]) -> Path:
    path = RAW_DIR / ("%s.json" % date)
    payload = [
        {"source_name": result.source_name, "errors": result.errors, "raw_items": result.raw_items}
        for result in source_results
    ]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def save_normalized(date: str, listings: List[Listing], rejected: List[Listing]) -> Path:
    path = NORMALIZED_DIR / ("%s.json" % date)
    payload = {
        "qualified": [listing.to_dict() for listing in listings],
        "rejected": [listing.to_dict() for listing in rejected],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def payload_key(payload: Dict) -> str:
    listing_id = payload.get("listing_id")
    if listing_id:
        return "%s:%s" % (payload.get("source", ""), listing_id)
    vin = payload.get("vin")
    if vin:
        return "vin:%s" % str(vin).upper()
    return "%s:%s:%s:%s:%s" % (
        payload.get("source_url", ""),
        payload.get("year") or "",
        payload.get("mileage") or "",
        payload.get("price") or "",
        payload.get("dealer_name", ""),
    )


def listing_inventory_key(listing: Listing) -> str:
    if listing.listing_id:
        return "%s:%s" % (listing.source, listing.listing_id)
    return listing.key()


def previous_normalized_snapshot(date: str) -> Tuple[str, Dict[str, Dict[str, Dict]]]:
    ensure_storage()
    candidates = sorted(path for path in NORMALIZED_DIR.glob("*.json") if path.stem < date)
    if not candidates:
        return "", {"qualified": {}, "rejected": {}}

    path = candidates[-1]
    payload = json.loads(path.read_text(encoding="utf-8"))
    return path.stem, {
        "qualified": {payload_key(item): item for item in payload.get("qualified", [])},
        "rejected": {payload_key(item): item for item in payload.get("rejected", [])},
    }


def inventory_changes_since_previous(date: str, qualified: List[Listing], rejected: List[Listing]) -> Dict:
    previous_date, previous = previous_normalized_snapshot(date)
    current_qualified = {listing_inventory_key(listing): listing for listing in qualified}
    current_rejected = {listing_inventory_key(listing): listing for listing in rejected}
    previous_qualified = previous["qualified"]
    previous_rejected = previous["rejected"]

    return {
        "previous_date": previous_date,
        "new_qualified": [current_qualified[key] for key in sorted(set(current_qualified) - set(previous_qualified))],
        "removed_qualified": [previous_qualified[key] for key in sorted(set(previous_qualified) - set(current_qualified))],
        "new_rejected": [current_rejected[key] for key in sorted(set(current_rejected) - set(previous_rejected))],
        "removed_rejected": [previous_rejected[key] for key in sorted(set(previous_rejected) - set(current_rejected))],
    }


def load_previous_state() -> Dict[str, Dict]:
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("select listing_key, last_price, last_mileage, payload_json from listings").fetchall()
    return {
        key: {"last_price": price, "last_mileage": mileage, "payload": json.loads(payload)}
        for key, price, mileage, payload in rows
    }


def load_first_seen_dates() -> Dict[str, str]:
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        listing_rows = conn.execute("select listing_key, first_seen_date from listings").fetchall()
        rejected_rows = conn.execute(
            "select listing_key, min(run_date) from rejected_listings group by listing_key"
        ).fetchall()
    dates = {key: date for key, date in listing_rows}
    for key, date in rejected_rows:
        if key not in dates or date < dates[key]:
            dates[key] = date
    return dates


def save_history(date: str, listings: Iterable[Listing], rejected: Iterable[Listing]) -> Tuple[List[str], List[str], Dict[str, int]]:
    ensure_storage()
    listings = list(listings)
    rejected = list(rejected)
    previous = load_previous_state()
    first_seen_dates = load_first_seen_dates()
    current_keys = {listing.key() for listing in listings}
    previous_keys = set(previous.keys())
    new_keys = sorted(current_keys - previous_keys)
    removed_keys = sorted(previous_keys - current_keys)
    price_changes: Dict[str, int] = {}

    with sqlite3.connect(DB_PATH) as conn:
        for listing in listings:
            key = listing.key()
            old = previous.get(key)
            if old and old["last_price"] is not None and listing.price is not None and old["last_price"] != listing.price:
                price_changes[key] = listing.price - old["last_price"]
                listing.price_change = price_changes[key]
            listing.first_seen_date = first_seen_dates.get(key, date)
            listing.last_seen_date = date
            payload = json.dumps(listing.to_dict(), sort_keys=True)
            conn.execute(
                """
                insert into listings (listing_key, first_seen_date, last_seen_date, last_price, last_mileage, payload_json)
                values (?, ?, ?, ?, ?, ?)
                on conflict(listing_key) do update set
                  last_seen_date=excluded.last_seen_date,
                  last_price=excluded.last_price,
                  last_mileage=excluded.last_mileage,
                  payload_json=excluded.payload_json
                """,
                (key, listing.first_seen_date, date, listing.price, listing.mileage, payload),
            )
            conn.execute(
                "insert into listing_snapshots (run_date, listing_key, price, mileage, score, payload_json) values (?, ?, ?, ?, ?, ?)",
                (date, key, listing.price, listing.mileage, listing.score, payload),
            )
        for listing in rejected:
            listing.first_seen_date = first_seen_dates.get(listing.key(), date)
            listing.last_seen_date = date
            conn.execute(
                "insert into rejected_listings (run_date, listing_key, reject_reason, payload_json) values (?, ?, ?, ?)",
                (date, listing.key(), listing.reject_reason, json.dumps(listing.to_dict(), sort_keys=True)),
            )
    return new_keys, removed_keys, price_changes
