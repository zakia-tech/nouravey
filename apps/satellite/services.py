from .models import SatelliteHotspot
from .providers.firms import fetch_mombasa_hotspots


def refresh_satellite_hotspots():
    """
    Fetches active fire/thermal hotspots from FIRMS and saves each as a
    SatelliteHotspot. Returns the list of created instances (may be empty
    if no hotspots were detected in the last 24 hours — this is normal).
    """
    hotspots_data = fetch_mombasa_hotspots()

    created = []
    for data in hotspots_data:
        instance = SatelliteHotspot.objects.create(**data)
        created.append(instance)

    return created
