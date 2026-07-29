from apps.analysis.models import Hotspot
from .utils import haversine_distance

CLUSTER_RADIUS_METERS = 500


def cluster_report(report):
    """
    Finds an existing active Hotspot near this report (same ward, within
    CLUSTER_RADIUS_METERS) and attaches the report to it, recalculating
    the hotspot's center. If none exists, creates a new Hotspot.

    Returns the Hotspot the report was attached to.
    """
    candidate_hotspots = Hotspot.objects.filter(ward=report.ward, is_active=True)

    matched_hotspot = None
    for hotspot in candidate_hotspots:
        distance = haversine_distance(
            report.latitude, report.longitude,
            hotspot.center_latitude, hotspot.center_longitude
        )
        if distance <= CLUSTER_RADIUS_METERS:
            matched_hotspot = hotspot
            break

    if matched_hotspot is None:
        matched_hotspot = Hotspot.objects.create(
            center_latitude=report.latitude,
            center_longitude=report.longitude,
            ward=report.ward,
            subcounty=report.subcounty,
        )

    matched_hotspot.reports.add(report)
    _recalculate_center(matched_hotspot)

    return matched_hotspot


def _recalculate_center(hotspot):
    """Recomputes the hotspot's center as the average of all attached reports' coordinates."""
    reports = hotspot.reports.all()
    if not reports:
        return

    avg_lat = sum(r.latitude for r in reports) / len(reports)
    avg_lng = sum(r.longitude for r in reports) / len(reports)

    hotspot.center_latitude = avg_lat
    hotspot.center_longitude = avg_lng
    hotspot.save(update_fields=['center_latitude', 'center_longitude'])
