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
