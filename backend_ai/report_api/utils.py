import re
import random
import numpy as np


def generate_mock_properties(area_sqft, beds, baths, count):
    """Generates realistic random property data relative to target metrics."""
    properties = []
    base_price_sqft = random.randint(150, 450)  # Random local market price/sqft

    for _ in range(count):
        # Variance of +/- 20% for realism
        v_sqft = int(area_sqft * random.uniform(0.8, 1.2))
        v_beds = max(1, beds + random.randint(-1, 1))
        v_baths = max(1, baths + random.randint(-1, 1))

        # Price based on sqft + some noise
        v_price = int(v_sqft * base_price_sqft * random.uniform(0.9, 1.1))

        properties.append(
            {"price": v_price, "area_sqft": v_sqft, "beds": v_beds, "baths": v_baths}
        )
    return properties


def generate_mock_summary(compiled_data, property_data):
    title = property_data.get("title")
    price = property_data.get("price")
    beds = property_data.get("beds")
    baths = property_data.get("baths")

    if not compiled_data:
        avg_comp_price = 0
        price_diff = "unknown"
    else:
        avg_comp_price = sum(p.get("price", 0) for p in compiled_data) / len(
            compiled_data
        )
        price_diff = "below" if price < avg_comp_price else "above"

    return {
        "investment_summary": (
            f"Automated insight generation temporarily unavailable. Fake data generated."
            f"The property at {title} is currently priced at ${price:,.2f}, "
            f"which is {price_diff} the local market average of ${avg_comp_price:,.2f}."
        ),
        "pros": [
            f"Competitive price point relative to {len(compiled_data)} local comparables.",
            f"Standard {beds} bed / {baths} bath configuration for this sub-market.",
        ],
        "cons": [
            "Automated insight generation temporarily unavailable for detailed analysis.",
            "Market volatility may require a manual appraisal for finalized valuation.",
        ],
    }


def extract_location(address_string):
    """
    Parses: "flat_no=961, house_no=83, area=North William, city=Odomstad..."
    """
    kv_pairs = [item.strip() for item in address_string.split(",")]
    location_data = {}
    for pair in kv_pairs:
        if "=" in pair:
            k, v = pair.split("=", 1)
            location_data[k.strip()] = v.strip()

    return location_data.get("area"), location_data.get("city")


def clean_context(text):
    # Remove multiple newlines and extra spaces
    text = text.replace("\n---\n", "||SEP||")

    junk_phrases = [
        r"Click to see more",
        r"View details",
        r"Read more",
        r"Find out why.*",
        r"Follow us on.*",
        r"Save this home",
        r"Terms and Conditions",
    ]
    for pattern in junk_phrases:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\n\s*\n", "\n", text)
    text = re.sub(r" +", " ", text)

    text = text.replace("||SEP||", "\n---\n")
    return text.strip()


def split_context(text, max_chars=10000):
    """
    Splits by \n---\n to keep properties whole.
    If a group of properties exceeds max_chars, it breaks them up.
    If a single segment is still too big (no separators found),
    it forces a character split so Groq doesn't crash.
    """
    if not text:
        return []

    segments = text.split("\n---\n")

    chunks = []
    current_chunk = ""

    for segment in segments:
        if len(current_chunk) + len(segment) < max_chars:
            current_chunk += segment + "\n---\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            if len(segment) > max_chars:
                for i in range(0, len(segment), max_chars):
                    chunks.append(segment[i : i + max_chars])
                current_chunk = ""
            else:
                current_chunk = segment + "\n---\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def clean_properties(item, property_data):
    SQFT_VARIANCE = 0.30
    BED_VARIANCE = 1
    BATH_VARIANCE = 1

    target_sqft = property_data.get("area_sqft")
    target_beds = property_data.get("beds")
    target_baths = property_data.get("baths")

    price = int(
        str(item.get("price", 0))
        .replace("$", "")
        .replace(",", "")
        .split(".", maxsplit=1)[0]
    )
    sqft = int(float(str(item.get("area_sqft", 0)).replace(",", "")))
    beds = int(float(str(item.get("beds", 0))))
    baths = int(float(str(item.get("baths", 0))))

    if price <= 10000 or sqft <= 100 or beds <= 0 or baths <= 0:
        raise ValueError

    if not (
        target_sqft * (1 - SQFT_VARIANCE) <= sqft <= target_sqft * (1 + SQFT_VARIANCE)
    ):
        raise ValueError

    if not target_beds - BED_VARIANCE <= beds <= target_beds + BED_VARIANCE:
        raise ValueError

    if not target_baths - BATH_VARIANCE <= baths <= target_baths + BATH_VARIANCE:
        raise ValueError

    return price, sqft, beds, baths


def average_prices_beds_baths(compiled_data):
    prices = [p["price"] for p in compiled_data if p.get("price")]
    sqft = [p["area_sqft"] for p in compiled_data if p.get("area_sqft")]
    beds = [p["beds"] for p in compiled_data if p.get("beds") is not None]
    baths = [p["baths"] for p in compiled_data if p.get("baths") is not None]

    if prices:
        avg_price = sum(prices) / len(prices)
    else:
        avg_price = 0

    if sqft:
        avg_sqft = sum(sqft) / len(sqft)
    else:
        avg_sqft = 0

    # Calculate market average PPS
    if avg_sqft > 0:
        avg_pps = avg_price / avg_sqft
    else:
        avg_pps = 0

    if beds:
        avg_beds = round(sum(beds) / len(beds))
    else:
        avg_beds = 0

    if baths:
        avg_baths = round(sum(baths) / len(baths))
    else:
        avg_baths = 0

    return avg_price, avg_pps, avg_beds, avg_baths


def generate_price_score(price, predicted_price):
    # Price ratio (20% discount = 2.0 | 30% premium = -2.0)
    diff_pct = (price - predicted_price) / predicted_price
    price_score = 1.4

    if diff_pct >= 0:
        price_score += (diff_pct / 0.20) * 0.6
        price_remarks = (
            f"Listed {abs(round(diff_pct*100, 1))}% above AI predicted price"
        )
    else:
        price_score -= (diff_pct / 0.30) * 0.6
        price_remarks = (
            f"Listed {abs(round(diff_pct*100, 1))}% below AI predicted price"
        )

    price_score = np.clip(price_score, -2.0, 2.0)
    return price_score, price_remarks


def generate_space_efficiency(price, area_sqft, avg_pps):
    # Space efficiency (price per square foot)
    prop_pps = price / area_sqft
    pps_diff = (prop_pps - avg_pps) / avg_pps
    pps_score = 0.77

    if pps_diff >= 0:
        pps_score += (pps_diff / 0.10) * 0.33
        pps_remarks = f"PPS is {abs(round(pps_diff*100, 1))}% higher than median"
    else:
        pps_score -= (pps_diff / 0.15) * 0.33
        pps_remarks = f"PPS is {abs(round(pps_diff*100, 1))}% lower than median"

    pps_score = np.clip(pps_score, -1.1, 1.1)

    return pps_score, pps_remarks


def generate_bed_score(beds, area_sqft, price, predicted_price, avg_beds, avg_sqft):
    # Room Factors (-0.8 to 0.8)
    # Bed counts
    space_worth_bed = 0
    if beds == avg_beds:
        bed_count_score = 0
        bed_remarks = "same bed, "
    elif beds > avg_beds:
        bed_count_score = 0.5
        bed_remarks = "more bed, "
    elif (avg_beds - beds) >= 2:
        bed_count_score = -0.5
        bed_remarks = "2 or more less bed, "
    else:
        bed_count_score = 0.2
        bed_remarks = "one less bed, "

    if bed_count_score == 0:
        if area_sqft > avg_sqft and price < predicted_price:
            bed_final = 0.5
            bed_remarks += "more sqft, less price"
        if area_sqft >= avg_sqft and (
            (predicted_price * 0.9) <= price <= (predicted_price * 1.1)
        ):
            bed_final = 0.3
            bed_remarks += "more sqft, close to predicted price"
        if area_sqft < avg_sqft and (
            (predicted_price * 0.9) <= price <= (predicted_price * 1.1)
        ):
            bed_final = -0.2
            bed_remarks += "less sqft, close to predicted price"
        else:
            bed_final = -0.5
            bed_remarks += "more price, sqft discarded"
    else:
        # Space Worth
        prop_spb = area_sqft / beds
        avg_spb = avg_sqft / avg_beds
        if prop_spb > avg_spb + (0.1 * avg_spb):
            space_worth_bed = 0.3
            if beds > avg_beds:
                bed_remarks += "more sqft satisfy more bed count"
            else:
                bed_remarks += "more sqft gives too much big rooms"
        else:
            space_worth_bed = -0.3
            if beds > avg_beds:
                bed_remarks += "less sqft not satisfy more bed count"
            else:
                bed_remarks += "less sqft makes spacious rooms"
        bed_final = bed_count_score + space_worth_bed

    bed_final = np.clip(bed_final, -0.8, 0.8)

    return bed_final, bed_count_score, space_worth_bed, bed_remarks


def generate_bath_score(
    baths, beds, area_sqft, price, predicted_price, avg_baths, avg_sqft
):
    # Bath Density (-0.7 to 0.7)
    # Gold Standard (0.7 ratio)
    bath_price_worth = 0
    space_worth_bath = 0
    bath_ratio = baths / beds
    bath_ratio_score = 0.45 if bath_ratio >= 0.7 else -0.45
    bath_remarks = (
        "bed bath ratio > 0.7, " if bath_ratio >= 0.7 else "bed bath ratio < 0.7, "
    )

    # Bath count
    if baths == avg_baths:
        if area_sqft > avg_sqft and price < predicted_price:
            bath_price_worth = 0.4
            bath_remarks += "more sqft less price"
        if area_sqft >= avg_sqft and (
            (predicted_price * 0.9) <= price <= (predicted_price * 1.1)
        ):
            bath_price_worth = 0.2
            bath_remarks += "more sqft same price"
        if area_sqft < avg_sqft and (
            (predicted_price * 0.9) <= price <= (predicted_price * 1.1)
        ):
            bath_price_worth = -0.1
            bath_remarks += "less sqft same price"
        else:
            bath_price_worth = -0.4
            bath_remarks += "more price, sqft discarded"
        bath_final = bath_ratio_score + bath_price_worth
    else:
        # Space Worth
        prop_spba = area_sqft / baths
        avg_spba = avg_sqft / avg_baths
        if prop_spba > avg_spba + (0.1 * avg_spba):
            space_worth_bath = 0.25
            bath_remarks += "Bathrooms spacious X total sqft"
        else:
            space_worth_bath = -0.25
            bath_remarks += "Bathrooms cramped X total sqft"
        bath_final = bath_ratio_score + space_worth_bath

    bath_final = np.clip(bath_final, -0.7, 0.7)

    return (
        bath_final,
        bath_ratio_score,
        space_worth_bath,
        bath_price_worth,
        bath_remarks,
    )
