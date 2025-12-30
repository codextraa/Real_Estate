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
