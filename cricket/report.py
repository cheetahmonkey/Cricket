from pathlib import Path
from typing import Dict, List

from .models import Listing, SourceResult


REPORTS_DIR = Path("reports")


def money(value):
    return "$%s" % format(value, ",") if value is not None else "Unknown"


def miles(value):
    return format(value, ",") if value is not None else "Unknown"


def table_cell(value) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|")


def report_action(listing: Listing) -> str:
    if listing.feature_confidence == "confirmed":
        return "Verify history and out-the-door price"
    if listing.feature_confidence == "likely":
        return "Verify RAB before visiting"
    return "Needs safety-feature verification"


def why_listing(listing: Listing) -> List[str]:
    reasons = []
    if listing.trim.lower() == "limited":
        reasons.append("Limited trim")
    if listing.mileage is not None and listing.mileage < 45000:
        reasons.append("Under 45K miles")
    if listing.distance_miles is not None and listing.distance_miles <= 30:
        reasons.append("Near Mom")
    if "carter" in listing.dealer_name.lower():
        reasons.append("Seller preference match")
    if listing.color_score in ("highest", "med_high"):
        reasons.append("Preferred color tier")
    if listing.cpo:
        reasons.append("CPO listing")
    if not reasons:
        reasons.append("Meets the configured hard filters")
    return reasons


def open_questions(listing: Listing) -> List[str]:
    questions = ["Confirm clean title / accident history", "Ask for out-the-door price"]
    if listing.feature_confidence != "confirmed":
        questions.insert(0, "Confirm Reverse Automatic Braking")
    return questions


def vehicle_history_summary(listing: Listing) -> str:
    owners = "%s owner%s" % (listing.owners, "" if listing.owners == 1 else "s") if listing.owners else "owners unknown"
    accident = listing.accident_history or "unknown"
    title = listing.title_status or "unknown"
    return "%s; accident history %s; title %s" % (owners, accident, title)


def rear_package_safety(listing: Listing) -> str:
    features = []
    if listing.reverse_automatic_braking == "yes":
        features.append("RAB")
    if listing.blind_spot_detection == "yes":
        features.append("BSD")
    if listing.rear_cross_traffic_alert == "yes":
        features.append("RCTA")
    return ", ".join(features) if features else "None confirmed"


def safety_evidence_summary(listing: Listing) -> str:
    evidence = listing.safety_evidence or {}
    parts = []
    for key in ("RAB", "BSD", "RCTA"):
        if evidence.get(key):
            parts.append("%s: %s" % (key, evidence[key]))
    return "; ".join(parts)


def markdown_link(label: str, url: str) -> str:
    if not url:
        return label
    safe_label = label.replace("[", "(").replace("]", ")")
    safe_url = url.replace(")", "%29")
    return "[%s](%s)" % (safe_label, safe_url)


def linked_color(listing: Listing) -> str:
    color = listing.exterior_color or "Unknown"
    return markdown_link(color, listing.source_url)


def compact_dealer_name(listing: Listing) -> str:
    dealer = listing.dealer_name or listing.source
    dealer = dealer.replace("Carter Subaru Shoreline", "Carter Shoreline")
    dealer = dealer.replace("Carter Subaru Ballard", "Carter Ballard")
    return dealer


def distance_summary(listing: Listing) -> str:
    return "%s mi" % listing.distance_miles if listing.distance_miles is not None else "Unknown"


def source_limitations(source_results: List[SourceResult]) -> List[str]:
    lines = []
    for result in source_results:
        if result.errors:
            lines.append("- %s: %s" % (result.source_name, "; ".join(result.errors)))
    return lines


def generate_report(
    date: str,
    listings: List[Listing],
    rejected: List[Listing],
    source_results: List[SourceResult],
    new_keys: List[str],
    removed_keys: List[str],
    price_changes: Dict[str, int],
) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / ("%s_crosstrek_search_report.md" % date)
    top = sorted(listings, key=lambda item: item.score, reverse=True)
    lines: List[str] = []
    lines.append("# %s Crosstrek Search Report" % date)
    lines.append("")
    lines.append("## Summary")
    sitemap_candidates = [
        item for item in rejected if item.raw.get("source_kind") == "dealer_eprocess_inventory_sitemap"
    ]
    if top:
        carter_count = len([item for item in top if "carter" in item.dealer_name.lower()])
        lines.append(
            "Cricket found %d promising Crosstrek%s today. %s"
            % (len(top), "" if len(top) == 1 else "s", "Cricket found %d Carter listing%s worth verifying." % (carter_count, "" if carter_count == 1 else "s") if carter_count else "No Carter listing qualified from available source data.")
        )
        lines.append("Cricket says: verify RAB before visiting unless the listing explicitly confirms Reverse Automatic Braking.")
    else:
        if sitemap_candidates:
            lines.append(
                "Cricket found no qualifying listings today, but did find %d Carter sitemap candidate%s that need mileage, price, and safety-feature verification."
                % (len(sitemap_candidates), "" if len(sitemap_candidates) == 1 else "s")
            )
        else:
            lines.append("Cricket found no qualifying listings today. Source access or sparse dealer markup may have limited the results, so this report should be treated as a conservative first pass.")
        lines.append("Cricket says: verify RAB before visiting when a candidate appears.")
    lines.append("")

    limitations = source_limitations(source_results)
    if limitations:
        lines.append("### Source Access Notes")
        lines.extend(limitations)
        lines.append("")

    lines.append("## Top Opportunities")
    if top:
        lines.append("| Rank | Score | Year | Trim | Safety | Feature Confidence | Miles | Price | Color | Seller | Distance |")
        lines.append("| ---: | ----: | ---- | ---- | ------ | ------------------ | ----: | ----: | ----- | ------ | -------: |")
        for index, listing in enumerate(top, start=1):
            lines.append(
                "| %d | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                % (
                    index,
                    listing.score,
                    listing.year or "Unknown",
                    table_cell(listing.trim or "Unknown"),
                    table_cell(rear_package_safety(listing)),
                    table_cell(listing.feature_confidence),
                    miles(listing.mileage),
                    money(listing.price),
                    table_cell(linked_color(listing)),
                    table_cell(compact_dealer_name(listing)),
                    distance_summary(listing),
                )
            )
        lines.append("")
        for index, listing in enumerate(top, start=1):
            lines.append(
                "## #%d - %s Subaru Crosstrek %s - %s miles - %s"
                % (index, listing.year or "Unknown", listing.trim or "Unknown", miles(listing.mileage), money(listing.price))
            )
            lines.append("")
            lines.append("Score: %d/100  " % listing.score)
            lines.append("Seller: %s  " % (listing.dealer_name or listing.source))
            lines.append("Distance: %s  " % ("%s miles" % listing.distance_miles if listing.distance_miles is not None else "Unknown"))
            lines.append("Color: %s - %s color tier  " % (listing.exterior_color or "Unknown", listing.color_score))
            lines.append("URL: %s  " % (listing.source_url or "Unknown"))
            lines.append("VIN: %s  " % (listing.vin or "Unknown"))
            lines.append("Vehicle history: %s  " % vehicle_history_summary(listing))
            if listing.history_report_url:
                lines.append("History report: %s  " % listing.history_report_url)
            lines.append("Feature confidence: %s - %s  " % (listing.feature_confidence.title(), report_action(listing)))
            safety_evidence = safety_evidence_summary(listing)
            if safety_evidence:
                lines.append("Safety evidence: %s  " % safety_evidence)
            lines.append("")
            lines.append("Why it ranks well:")
            for reason in why_listing(listing):
                lines.append("- %s" % reason)
            lines.append("")
            lines.append("Open questions:")
            for question in open_questions(listing):
                lines.append("- %s" % question)
            lines.append("")
    else:
        lines.append("No listings qualified for the main ranked list.")
        lines.append("")

    lines.append("## New / Rejected / Price Drop Listings")
    lines.append("")
    lines.append("New listings: %d" % len(new_keys))
    for key in new_keys[:20]:
        lines.append("- %s" % key)
    lines.append("")
    drops = {key: change for key, change in price_changes.items() if change < 0}
    lines.append("Price drops: %d" % len(drops))
    for key, change in drops.items():
        lines.append("- %s: %s" % (key, money(change)))
    lines.append("")
    lines.append("Rejected listings: %d" % len(rejected))
    if rejected:
        lines.append("")
        lines.append("| # | Reason | Year | Trim | Safety | Feature Confidence | Miles | Price | Color | Seller | Distance |")
        lines.append("| ---: | ------ | ---- | ---- | ------ | ------------------ | ----: | ----: | ----- | ------ | -------: |")
        for index, listing in enumerate(rejected[:30], start=1):
            lines.append(
                "| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                % (
                    index,
                    table_cell(listing.reject_reason or "rejected"),
                    listing.year or "Unknown",
                    table_cell(listing.trim or "Unknown"),
                    table_cell(rear_package_safety(listing)),
                    table_cell(listing.feature_confidence),
                    miles(listing.mileage),
                    money(listing.price),
                    table_cell(linked_color(listing)),
                    table_cell(compact_dealer_name(listing)),
                    distance_summary(listing),
                )
            )
    if removed_keys:
        lines.append("")
        lines.append("Removed since prior history: %d" % len(removed_keys))
        for key in removed_keys[:20]:
            lines.append("- %s" % key)
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
