import re
import random


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


def generate_mock_summary(compiled_data, title, price, beds, baths):
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


def average_prices(compiled_data):
    prices = [p["price"] for p in compiled_data if p.get("price")]
    sqft = [p["area_sqft"] for p in compiled_data if p.get("area_sqft")]

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

    return avg_price, avg_pps


def average_beds_baths(compiled_data):
    beds = [p["beds"] for p in compiled_data if p.get("beds") is not None]
    baths = [p["baths"] for p in compiled_data if p.get("baths") is not None]

    if beds:
        avg_beds = round(sum(beds) / len(beds))
    else:
        avg_beds = 0

    if baths:
        avg_baths = round(sum(baths) / len(baths))
    else:
        avg_baths = 0

    return avg_beds, avg_baths
