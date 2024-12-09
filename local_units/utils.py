def format_local_unit(data: dict) -> dict:
    """
    Formatting the json local unit data
    """
    location = data.get("location_details", None)
    if location:
        coordinates = location.get("coordinates")
        data["location_json"] = {
            "type": location.get("type"),
            "lat": coordinates[1],
            "lng": coordinates[0],
        }
    return data
