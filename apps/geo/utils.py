from math import radians, sin, cos, sqrt, atan2

EARTH_RADIUS_METERS = 6371000


def haversine_distance(lat1, lng1, lat2, lng2):
    """
    Returns the distance in meters between two lat/lng points using the
    haversine formula. Accurate enough for city-scale clustering.
    """
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lng2 - lng1)

    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return EARTH_RADIUS_METERS * c
