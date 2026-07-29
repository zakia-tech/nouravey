from .models import SensorReading
from .providers.iqair import fetch_mombasa_air_quality


def refresh_air_quality():
    """
    Fetches the latest Mombasa air quality data from IQAir and saves it
    as a new SensorReading. Returns the created instance, or None if
    the fetch failed.
    """
    data = fetch_mombasa_air_quality()

    if data is None:
        return None

    return SensorReading.objects.create(**data)
