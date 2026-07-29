from datetime import timedelta
from django.utils import timezone

from apps.satellite.models import SatelliteHotspot
from apps.sensors.models import SensorReading
from apps.geo.utils import haversine_distance

SATELLITE_PROXIMITY_METERS = 2000  # how close a FIRMS detection must be to count as corroborating
RECENCY_WINDOW_HOURS = 48  # reports older than this contribute less to the score
ELEVATED_AQI_THRESHOLD = 100  # US AQI "Unhealthy for Sensitive Groups" and above


def score_hotspot(hotspot):
    """
    Calculates a numeric score for a Hotspot based on report count, average
    severity, satellite corroboration, current air quality, and recency.
    Also sets severity_label based on the resulting score.

    Returns the score (float). Does not save — caller is responsible for
    calling hotspot.save() after any other updates.
    """
    reports = hotspot.reports.all()
    if not reports:
        hotspot.score = 0
        hotspot.severity_label = 'low'
        return 0

    report_count = len(reports)
    avg_severity = sum(r.severity for r in reports) / report_count

    # Base score: report volume matters, but severity matters more
    score = (report_count * 5) + (avg_severity * 10)

    # Recency: boost if any report is recent, decay if all are old
    now = timezone.now()
    most_recent = max(r.submitted_at for r in reports)
    hours_since_last_report = (now - most_recent).total_seconds() / 3600

    if hours_since_last_report <= RECENCY_WINDOW_HOURS:
        recency_factor = 1.0 - (hours_since_last_report / RECENCY_WINDOW_HOURS) * 0.5
    else:
        recency_factor = 0.5  # stale, but don't zero it out entirely

    score *= recency_factor

    # Satellite corroboration: any FIRMS detection within range in the last 48h adds weight
    recent_satellite = SatelliteHotspot.objects.filter(
        detected_at__gte=now - timedelta(hours=RECENCY_WINDOW_HOURS)
    )
    for sat in recent_satellite:
        distance = haversine_distance(
            hotspot.center_latitude, hotspot.center_longitude,
            sat.latitude, sat.longitude
        )
        if distance <= SATELLITE_PROXIMITY_METERS:
            score += 20
            hotspot.satellite_hotspots.add(sat)
            break  # one corroborating detection is enough to count

    # Air quality corroboration: elevated city-wide AQI adds a smaller, flat bump
    latest_reading = SensorReading.objects.first()
    if latest_reading and latest_reading.aqi >= ELEVATED_AQI_THRESHOLD:
        score += 10
        hotspot.sensor_readings.add(latest_reading)

    hotspot.score = round(score, 1)
    hotspot.severity_label = _score_to_label(hotspot.score)

    return hotspot.score


def _score_to_label(score):
    if score < 20:
        return 'low'
    elif score < 50:
        return 'medium'
    elif score < 80:
        return 'high'
    else:
        return 'critical'
