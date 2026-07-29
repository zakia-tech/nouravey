import csv
import io
from datetime import datetime, timezone

import requests
from django.conf import settings

FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Same bounding box used for the Mombasa map — west,south,east,north
MOMBASA_BBOX = "39.45,-4.15,39.70,-3.95"

# VIIRS_SNPP_NRT is a reliable near-real-time source; day_range=1 means "last 24 hours"
SOURCE = "VIIRS_SNPP_NRT"
DAY_RANGE = 1


def fetch_mombasa_hotspots():
    """
    Fetches active fire/thermal hotspots within Mombasa's bounding box from
    NASA FIRMS for the last 24 hours. Returns a list of dicts ready to
    create SatelliteHotspot instances, or an empty list on failure.
    """
    url = f"{FIRMS_BASE_URL}/{settings.FIRMS_MAP_KEY}/{SOURCE}/{MOMBASA_BBOX}/{DAY_RANGE}"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        # FIRMS returns CSV, not JSON
        reader = csv.DictReader(io.StringIO(response.text))

        results = []
        for row in reader:
            try:
                acq_date = row.get('acq_date')
                acq_time = row.get('acq_time', '0000').zfill(4)
                detected_at = datetime.strptime(
                    f"{acq_date} {acq_time}", "%Y-%m-%d %H%M"
                ).replace(tzinfo=timezone.utc)

                confidence_raw = row.get('confidence', 'n').lower()
                # VIIRS confidence is typically 'l' (low), 'n' (nominal), 'h' (high)
                confidence_map = {'l': 'low', 'n': 'nominal', 'h': 'high'}
                confidence = confidence_map.get(confidence_raw, 'nominal')

                results.append({
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'brightness': float(row.get('bright_ti4', row.get('brightness', 0))),
                    'confidence': confidence,
                    'detected_at': detected_at,
                })
            except (KeyError, ValueError):
                continue  # skip malformed rows rather than failing the whole batch

        return results

    except requests.RequestException:
        return []
