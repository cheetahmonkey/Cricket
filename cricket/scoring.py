from typing import Dict, List, Tuple

from .models import Listing


def classify_color(color: str, config: Dict) -> str:
    text = (color or "").lower()
    preferences = config.get("color_preferences", {})
    for tier in ("highest", "med_high", "med", "low"):
        for token in preferences.get(tier, []):
            if token.lower() in text:
                return tier
    return "unknown"


def infer_features(listing: Listing) -> None:
    text = " ".join(
        [
            listing.trim or "",
            listing.exterior_color or "",
            " ".join(listing.notes),
            str(listing.raw),
        ]
    ).lower()

    def has_any(tokens: List[str]) -> bool:
        return any(token in text for token in tokens)

    if has_any(["rearview camera", "rear-view camera", "backup camera", "rear camera"]):
        listing.rear_camera = "yes"
    if has_any(["blind spot", "bsd"]):
        listing.blind_spot_detection = "yes"
    if has_any(["rear cross", "rcta", "cross-traffic", "cross traffic"]):
        listing.rear_cross_traffic_alert = "yes"
    if has_any(["reverse automatic braking", "reverse auto braking"]):
        listing.reverse_automatic_braking = "yes"

    if has_any(["no reverse automatic braking", "without reverse automatic braking", "rab not"]):
        listing.reverse_automatic_braking = "no"
        listing.feature_confidence = "contradicted"
        return

    all_confirmed = all(
        getattr(listing, field) == "yes"
        for field in (
            "rear_camera",
            "blind_spot_detection",
            "rear_cross_traffic_alert",
            "reverse_automatic_braking",
        )
    )
    if all_confirmed:
        listing.feature_confidence = "confirmed"
    elif (
        listing.reverse_automatic_braking == "unknown"
        and listing.trim.lower() == "limited"
        and listing.year is not None
        and 2021 <= listing.year <= 2024
        and listing.blind_spot_detection == "yes"
        and listing.rear_cross_traffic_alert == "yes"
    ):
        listing.feature_confidence = "likely"
        listing.notes.append("Limited trim with BSD/RCTA evidence; verify RAB before visiting.")
    elif listing.trim.lower() == "limited" and listing.year is not None and 2021 <= listing.year <= 2024:
        listing.feature_confidence = "likely"
        listing.notes.append("Limited trim makes RAB plausible, but listing evidence is incomplete.")
    elif listing.blind_spot_detection == "yes" and listing.rear_cross_traffic_alert == "yes":
        listing.feature_confidence = "unknown"
    else:
        listing.feature_confidence = "unknown"


def apply_hard_filters(listing: Listing, config: Dict) -> Tuple[bool, str]:
    vehicle = config.get("vehicle", {})
    if (listing.make or "").lower() != "subaru":
        return False, "wrong make"
    if (listing.model or "").lower() != "crosstrek":
        return False, "wrong model"
    if listing.year is None or listing.year < vehicle.get("years_min", 2020):
        return False, "older than 2020 or missing year"
    if listing.mileage is not None and listing.mileage >= vehicle.get("max_mileage", 45000):
        return False, "over mileage limit"
    if listing.mileage is None:
        return False, "missing mileage"
    if any(token in (listing.title_status or "").lower() for token in ["salvage", "rebuilt", "lemon", "buyback"]):
        return False, "bad title status"
    if "manual" in (listing.transmission or "").lower():
        return False, "manual transmission"
    if listing.reverse_automatic_braking == "no" or listing.feature_confidence == "contradicted":
        return False, "RAB contradicted or missing"
    if listing.feature_confidence == "unknown" and listing.trim.lower() != "limited":
        return False, "missing required safety evidence"
    return True, ""


def score_listing(listing: Listing, config: Dict) -> Listing:
    listing.color_score = classify_color(listing.exterior_color, config)

    feature_points = {
        "confirmed": 25,
        "likely": 20,
        "unknown": 10 if listing.blind_spot_detection == "yes" and listing.rear_cross_traffic_alert == "yes" else 3,
        "contradicted": 0,
    }.get(listing.feature_confidence, 3)

    price_points = 10
    listing.price_confidence = "unknown"

    miles = listing.mileage if listing.mileage is not None else 999999
    if miles < 15000:
        mileage_points = 15
    elif miles < 25000:
        mileage_points = 13
    elif miles < 35000:
        mileage_points = 10
    elif miles < 45000:
        mileage_points = 7
    else:
        mileage_points = 0

    if listing.trim.lower() == "limited":
        year_points = {2024: 10, 2023: 9, 2022: 8, 2021: 7, 2020: 5}.get(listing.year, 0)
    else:
        year_points = 4 if listing.feature_confidence == "confirmed" else 0

    seller_text = "%s %s" % (listing.dealer_name.lower(), listing.dealer_type.lower())
    if "carter subaru" in seller_text:
        seller_points = 10
    elif "cpo" in seller_text:
        seller_points = 9
    elif "subaru dealer" in seller_text or "subaru" in listing.dealer_name.lower():
        seller_points = 8
    elif "franchise" in seller_text:
        seller_points = 6
    elif "retailer" in seller_text:
        seller_points = 5
    elif "private" in seller_text:
        seller_points = 2
    else:
        seller_points = 3

    distance = listing.distance_miles
    if distance is None:
        distance_points = 4
    elif distance <= 15:
        distance_points = 10
    elif distance <= 30:
        distance_points = 8
    elif distance <= 50:
        distance_points = 6
    elif distance <= 100:
        distance_points = 4
    elif distance <= 200:
        distance_points = 2
    else:
        distance_points = 0

    history_text = "%s %s %s" % (listing.accident_history, listing.title_status, listing.service_records)
    history_text = history_text.lower()
    if listing.owners == 1 and "none" in history_text and "clean" in history_text:
        history_points = 5
    elif "none" in history_text and "clean" in history_text:
        history_points = 4
    elif "minor" in history_text:
        history_points = 2
    elif any(token in history_text for token in ["salvage", "rebuilt", "lemon", "buyback"]):
        history_points = 0
    else:
        history_points = 1

    notes_text = " ".join(listing.notes).lower()
    extras = 0.0
    if "heated seat" in notes_text:
        extras += 1
    if "power driver" in notes_text:
        extras += 1
    if "keyless" in notes_text or "push-button" in notes_text or "push button" in notes_text:
        extras += 1
    if "light interior" in notes_text or "easy entry" in notes_text or "good visibility" in notes_text:
        extras += 1
    extras += {"highest": 1, "med_high": 0.5, "med": 0.25}.get(listing.color_score, 0)
    mom_fit_points = min(5, extras)

    total = int(round(feature_points + price_points + mileage_points + year_points + seller_points + distance_points + history_points + mom_fit_points))
    listing.score = total
    listing.score_breakdown = {
        "feature_confidence": feature_points,
        "price_value": price_points,
        "mileage": mileage_points,
        "year_trim": year_points,
        "seller_quality": seller_points,
        "distance": distance_points,
        "vehicle_history": history_points,
        "mom_fit_extras": mom_fit_points,
    }
    return listing
