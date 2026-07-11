import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .models import Listing, SourceResult


DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "listings_raw"
NORMALIZED_DIR = DATA_DIR / "listings_normalized"
DB_PATH = DATA_DIR / "listings_history.sqlite"


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


def load_previous_state() -> Dict[str, Dict]:
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("select listing_key, last_price, last_mileage, payload_json from listings").fetchall()
    return {
        key: {"last_price": price, "last_mileage": mileage, "payload": json.loads(payload)}
        for key, price, mileage, payload in rows
    }


def save_history(date: str, listings: Iterable[Listing], rejected: Iterable[Listing]) -> Tuple[List[str], List[str], Dict[str, int]]:
    ensure_storage()
    listings = list(listings)
    rejected = list(rejected)
    previous = load_previous_state()
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
            if old:
                listing.first_seen_date = old["payload"].get("first_seen_date") or date
            else:
                listing.first_seen_date = date
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
            conn.execute(
                "insert into rejected_listings (run_date, listing_key, reject_reason, payload_json) values (?, ?, ?, ?)",
                (date, listing.key(), listing.reject_reason, json.dumps(listing.to_dict(), sort_keys=True)),
            )
    return new_keys, removed_keys, price_changes
