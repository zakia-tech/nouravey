import requests
from django.conf import settings

IQAIR_BASE_URL = "http://api.airvisual.com/v2"


def fetch_mombasa_air_quality():
    """
    Fetches current air quality data for Mombasa city from IQAir's free
    Community tier. Returns a dict ready to create a SensorReading, or
    None if the request fails.
    """
    try:
        response = requests.get(
            f"{IQAIR_BASE_URL}/city",
            params={
                "city": "Mombasa",
                "state": "Mombasa",
                "country": "Kenya",
                "key": settings.IQAIR_API_KEY,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            return None

        result = data["data"]
        coordinates = result["location"]["coordinates"]  # [lng, lat]
        pollution = result["current"]["pollution"]

        return {
            "station_name": f"{result['city']} (IQAir)",
            "latitude": coordinates[1],
            "longitude": coordinates[0],
            "aqi": pollution["aqius"],
            "pm25": None,  # raw concentration not available on free tier
        }

    except (requests.RequestException, KeyError, ValueError):
        return None
