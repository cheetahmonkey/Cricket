import argparse
from datetime import datetime
from typing import Dict, List

from .config import DEFAULT_CONFIG_PATH, load_config
from .models import Listing, RunResult
from .report import generate_report
from .scoring import apply_hard_filters, infer_features, score_listing
from .sources import build_source
from .storage import ensure_storage, save_history, save_normalized, save_raw
from .sync import sync_run_outputs


def dedupe(listings: List[Listing]) -> List[Listing]:
    seen = {}
    for listing in listings:
        key = listing.key()
        current = seen.get(key)
        if current is None or listing.score > current.score:
            seen[key] = listing
    return list(seen.values())


def run_search(config_path=DEFAULT_CONFIG_PATH) -> RunResult:
    config = load_config(config_path)
    date = datetime.now().strftime("%Y-%m-%d")
    ensure_storage()

    source_results = []
    all_listings = []
    for source_config in config.get("sources", {}).get("tier1", []):
        source = build_source(source_config)
        result = source.search()
        source_results.append(result)
        all_listings.extend(result.listings)

    qualified = []
    rejected = []
    for listing in dedupe(all_listings):
        infer_features(listing)
        score_listing(listing, config)
        ok, reason = apply_hard_filters(listing, config)
        if ok:
            qualified.append(listing)
        else:
            listing.reject_reason = reason
            rejected.append(listing)

    qualified = sorted(qualified, key=lambda item: item.score, reverse=True)
    raw_path = save_raw(date, source_results)
    new_keys, removed_keys, price_changes = save_history(date, qualified, rejected)
    normalized_path = save_normalized(date, qualified, rejected)
    report_path = generate_report(date, qualified, rejected, source_results, new_keys, removed_keys, price_changes)
    sync_paths, sync_errors = sync_run_outputs(config, [report_path, raw_path, normalized_path])

    return RunResult(
        date=date,
        listings=qualified,
        rejected=rejected,
        source_results=source_results,
        report_path=str(report_path),
        raw_path=str(raw_path),
        normalized_path=str(normalized_path),
        new_keys=new_keys,
        removed_keys=removed_keys,
        price_changes=price_changes,
        sync_paths=sync_paths,
        sync_errors=sync_errors,
    )


def print_summary(result: RunResult) -> None:
    if result.listings:
        print("Cricket found %d promising Crosstrek%s today." % (len(result.listings), "" if len(result.listings) == 1 else "s"))
        for index, listing in enumerate(result.listings[:3], start=1):
            print(
                "%d. %s %s, %s miles, %s, score %d, %s"
                % (
                    index,
                    listing.year or "Unknown",
                    listing.trim or "Unknown trim",
                    "{:,}".format(listing.mileage) if listing.mileage is not None else "unknown",
                    "$%s" % "{:,}".format(listing.price) if listing.price is not None else "unknown price",
                    listing.score,
                    listing.dealer_name or listing.source,
                )
            )
    else:
        print("Cricket found no qualifying listings today.")
    print("Cricket rejected %d listing%s today." % (len(result.rejected), "" if len(result.rejected) == 1 else "s"))
    failures = sum(len(source.errors) for source in result.source_results)
    if failures:
        print("Cricket recorded %d source-access limitation%s." % (failures, "" if failures == 1 else "s"))
    print("Cricket generated report: %s" % result.report_path)
    if result.sync_paths:
        print("Cricket synced %d file%s to the Windows data store." % (len(result.sync_paths), "" if len(result.sync_paths) == 1 else "s"))
    if result.sync_errors:
        print("Cricket recorded %d data-sync limitation%s." % (len(result.sync_errors), "" if len(result.sync_errors) == 1 else "s"))


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="python -m cricket")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="Run the Cricket Crosstrek search")
    run_parser.add_argument("--manual", action="store_true", help="Run immediately from the command line")
    run_parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to search config")

    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_search(args.config)
        print_summary(result)
        return
    parser.print_help()
