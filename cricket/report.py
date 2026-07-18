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


def visit_check(listing: Listing) -> str:
    checks = []
    if listing.feature_confidence != "confirmed":
        checks.append("Verify RAB")
    if listing.history_report_url:
        checks.append(markdown_link("Open CARFAX", listing.history_report_url))
    else:
        checks.append("Review history")
    checks.append("Final OTD")
    return " + ".join(checks)


def estimated_out_the_door(listing: Listing, pricing: Dict) -> int:
    if listing.price is None:
        return None
    sales_tax_rate = pricing.get("sales_tax_rate", 0.11)
    doc_fee = pricing.get("dealer_doc_fee", 200)
    registration = pricing.get("wa_registration_estimate", 700)
    return int(round(listing.price * (1 + sales_tax_rate) + doc_fee + registration))


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
    questions = ["Review the linked CARFAX report", "Ask for final out-the-door price"]
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


def item_value(item, key: str, default=""):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def compact_listing_label(item) -> str:
    year = item_value(item, "year") or "Unknown"
    trim = item_value(item, "trim") or "Unknown"
    mileage = miles(item_value(item, "mileage"))
    price = money(item_value(item, "price"))
    dealer = item_value(item, "dealer_name") or item_value(item, "source") or "Unknown seller"
    label = "%s %s, %s mi, %s, %s" % (year, trim, mileage, price, compact_dealer_name_from_text(dealer))
    url = item_value(item, "source_url") or item_value(item, "url")
    return markdown_link(label, url) if url else label


def compact_dealer_name_from_text(dealer: str) -> str:
    dealer = dealer.replace("Carter Subaru Shoreline", "Carter Shoreline")
    dealer = dealer.replace("Carter Subaru Ballard", "Carter Ballard")
    return dealer


def compact_inventory_changes(inventory_changes: Dict) -> List[str]:
    if not inventory_changes or not inventory_changes.get("previous_date"):
        return []

    new_qualified = inventory_changes.get("new_qualified", [])
    removed_qualified = inventory_changes.get("removed_qualified", [])
    new_rejected = inventory_changes.get("new_rejected", [])
    removed_rejected = inventory_changes.get("removed_rejected", [])

    lines = []
    if new_qualified or removed_qualified:
        lines.append(
            "Top opportunities since %s: +%d new, -%d removed."
            % (inventory_changes["previous_date"], len(new_qualified), len(removed_qualified))
        )
    else:
        lines.append("Top opportunities: no additions or removals since %s." % inventory_changes["previous_date"])
    if new_rejected or removed_rejected:
        lines.append("Watchlist changes: +%d added, -%d removed." % (len(new_rejected), len(removed_rejected)))

    details = []
    if new_qualified:
        details.append("- New top opportunity: %s" % "; ".join(compact_listing_label(item) for item in new_qualified[:3]))
    if removed_qualified:
        details.append("- Removed top opportunity: %s" % "; ".join(compact_listing_label(item) for item in removed_qualified[:3]))
    if new_rejected:
        details.append("- New watchlist: %s" % "; ".join(compact_listing_label(item) for item in new_rejected[:3]))
    if removed_rejected:
        details.append("- Removed watchlist: %s" % "; ".join(compact_listing_label(item) for item in removed_rejected[:3]))
    if details:
        lines.extend(details)
    return lines


def morning_note(top: List[Listing], inventory_changes: Dict, price_changes: Dict[str, int], pricing: Dict) -> List[str]:
    """Return a short decision-relevant note, or nothing when there is no news."""
    if not top:
        return ["No qualifying Crosstreks are on Cricket's current shortlist."]

    changes = inventory_changes or {}
    new_top = changes.get("new_qualified", [])
    removed_top = changes.get("removed_qualified", [])
    new_watchlist = changes.get("new_rejected", [])
    removed_watchlist = changes.get("removed_rejected", [])
    notes = []
    if new_top or removed_top:
        notes.append(
            "Top opportunities changed: %d added and %d removed." % (len(new_top), len(removed_top))
        )

    drops = {key: change for key, change in price_changes.items() if change < 0}
    if drops:
        dropped_listings = [listing for listing in top if listing.key() in drops]
        if dropped_listings:
            listing = dropped_listings[0]
            notes.append(
                "%s at %s dropped %s; its estimated out-the-door cost is now %s."
                % (
                    markdown_link("%s %s" % (listing.year or "Unknown", listing.trim or "Crosstrek"), listing.source_url),
                    compact_dealer_name(listing),
                    money(abs(drops[listing.key()])),
                    money(estimated_out_the_door(listing, pricing)),
                )
            )
        else:
            notes.append("%d listing%s had a price drop." % (len(drops), "" if len(drops) == 1 else "s"))

    if new_watchlist or removed_watchlist:
        notes.append("Watchlist: %d added and %d removed." % (len(new_watchlist), len(removed_watchlist)))
    return notes


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
    inventory_changes: Dict = None,
    pricing: Dict = None,
) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / ("%s_crosstrek_search_report.md" % date)
    top = sorted(listings, key=lambda item: item.score, reverse=True)
    pricing = pricing or {}
    lines: List[str] = []
    lines.append("# %s Crosstrek Search Report" % date)
    lines.append("")
    sitemap_candidates = [
        item for item in rejected if item.raw.get("source_kind") == "dealer_eprocess_inventory_sitemap"
    ]
    note_lines = morning_note(top, inventory_changes or {}, price_changes, pricing)
    if note_lines:
        lines.append("## Cricket's Morning Note")
        lines.extend(note_lines)
        lines.append("")
    if not top:
        if sitemap_candidates:
            lines.append(
                "Cricket found no qualifying listings today, but did find %d Carter sitemap candidate%s that need mileage, price, and safety-feature verification."
                % (len(sitemap_candidates), "" if len(sitemap_candidates) == 1 else "s")
            )
        else:
            lines.append("Cricket found no qualifying listings today. Source access or sparse dealer markup may have limited the results, so this report should be treated as a conservative first pass.")
        lines.append("Cricket says: a good listing still needs clear RAB evidence before it becomes a real candidate.")
        lines.append("")
    inventory_lines = compact_inventory_changes(inventory_changes or {})
    if inventory_lines:
        lines.append("## What Changed Since Yesterday")
        lines.extend(inventory_lines)
        drops = {key: change for key, change in price_changes.items() if change < 0}
        if drops:
            lines.append("Price drops: %d." % len(drops))
        lines.append("")

    lines.append("## Top Opportunities")
    if top:
        lines.append("| Rank | Score | Color | Year | Trim | Safety | Feature Confidence | Miles | Price | Est. OTD | Seller | Check Before Visiting |")
        lines.append("| ---: | ----: | ----- | ---- | ---- | ------ | ------------------ | ----: | ----: | -------: | ------ | --------------------- |")
        for index, listing in enumerate(top, start=1):
            lines.append(
                "| %d | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                % (
                    index,
                    listing.score,
                    table_cell(linked_color(listing)),
                    listing.year or "Unknown",
                    table_cell(listing.trim or "Unknown"),
                    table_cell(rear_package_safety(listing)),
                    table_cell(listing.feature_confidence),
                    miles(listing.mileage),
                    money(listing.price),
                    money(estimated_out_the_door(listing, pricing)),
                    table_cell(compact_dealer_name(listing)),
                    table_cell(visit_check(listing)),
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
            lines.append("Estimated out the door: %s  " % money(estimated_out_the_door(listing, pricing)))
            lines.append("Color: %s - %s color tier  " % (listing.exterior_color or "Unknown", listing.color_score))
            lines.append("URL: %s  " % (listing.source_url or "Unknown"))
            lines.append("VIN: %s  " % (listing.vin or "Unknown"))
            if listing.history_report_url:
                lines.append("CARFAX report: %s  " % listing.history_report_url)
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

    lines.append("## Other Listings to Keep in View")
    lines.append("")
    lines.append("Cricket is keeping %d listing%s visible for comparison, even though each has a concern noted below." % (len(rejected), "" if len(rejected) == 1 else "s"))
    if rejected:
        lines.append("")
        lines.append("| # | Main Concern | Color | Year | Trim | Safety | Feature Confidence | Miles | Price | Est. OTD | Seller | Check Before Visiting |")
        lines.append("| ---: | ------------ | ----- | ---- | ---- | ------ | ------------------ | ----: | ----: | -------: | ------ | --------------------- |")
        for index, listing in enumerate(rejected[:30], start=1):
            lines.append(
                "| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                % (
                    index,
                    table_cell(listing.reject_reason or "rejected"),
                    table_cell(linked_color(listing)),
                    listing.year or "Unknown",
                    table_cell(listing.trim or "Unknown"),
                    table_cell(rear_package_safety(listing)),
                    table_cell(listing.feature_confidence),
                    miles(listing.mileage),
                    money(listing.price),
                    money(estimated_out_the_door(listing, pricing)),
                    table_cell(compact_dealer_name(listing)),
                    table_cell(visit_check(listing)),
                )
            )
    lines.append("")

    lines.append("## Report Details")
    lines.append("Estimated OTD = listed price + 11%% estimated Washington sales tax + $%s Carter document fee + $%s estimated Washington registration/licensing. Confirm the dealer's final out-the-door number before purchase." % (format(pricing.get("dealer_doc_fee", 200), ","), format(pricing.get("wa_registration_estimate", 700), ",")))
    lines.append("")
    limitations = source_limitations(source_results)
    if limitations:
        lines.append("### Search Notes")
        lines.extend(limitations)
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
