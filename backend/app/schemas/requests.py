"""Request body helpers / validation."""


def validate_bounds(data):
    """
    Extract and validate bounds from request JSON.
    Returns (bounds_dict, error_message).
    """
    if not data:
        return None, "Missing JSON body"

    bounds = data.get("bounds")
    if not bounds:
        return None, "Missing bounds parameter"

    keys = ("minLon", "minLat", "maxLon", "maxLat")
    if any(bounds.get(k) is None for k in keys):
        return None, "Invalid bounds coordinates"

    return {
        "minLon": bounds["minLon"],
        "minLat": bounds["minLat"],
        "maxLon": bounds["maxLon"],
        "maxLat": bounds["maxLat"],
    }, None
