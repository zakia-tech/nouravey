from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.reports.models import Report
from apps.sensors.models import SensorReading
from apps.analysis.models import Hotspot


def map_view(request):
    return render(request, 'dashboard/map.html')


@api_view(['GET'])
def map_data(request):
    reports = Report.objects.all()
    reports_data = [
        {
            'id': r.id,
            'latitude': r.latitude,
            'longitude': r.longitude,
            'ward': r.get_ward_display(),
            'pollution_type': r.get_pollution_type_display(),
            'severity': r.severity,
            'status': r.get_status_display(),
            'status_raw': r.status,
            'likely_cause': r.likely_cause,
            'submitted_at': r.submitted_at.isoformat(),
        }
        for r in reports
    ]

    latest_sensor = SensorReading.objects.first()
    sensor_data = None
    if latest_sensor:
        sensor_data = {
            'latitude': latest_sensor.latitude,
            'longitude': latest_sensor.longitude,
            'aqi': latest_sensor.aqi,
            'station_name': latest_sensor.station_name,
            'fetched_at': latest_sensor.fetched_at.isoformat(),
        }

    hotspots = Hotspot.objects.filter(is_active=True)
    hotspots_data = [
        {
            'id': h.id,
            'latitude': h.center_latitude,
            'longitude': h.center_longitude,
            'ward': h.get_ward_display(),
            'score': h.score,
            'severity_label': h.severity_label,
            'narrative': h.narrative,
            'recommended_action': h.recommended_action,
            'report_count': h.reports.count(),
            'predicted_trend': h.get_predicted_trend_display(),
            'predicted_trend_raw': h.predicted_trend,
            'prediction_confidence': h.prediction_confidence,
            'prediction_rationale': h.prediction_rationale,
        }
        for h in hotspots
    ]

    return Response({
        'reports': reports_data,
        'sensor': sensor_data,
        'hotspots': hotspots_data,
    })


@api_view(['GET'])
def subcounty_boundaries(request):
    import json
    from pathlib import Path
    path = Path(__file__).resolve().parent.parent / 'geo' / 'data' / 'mombasa_subcounties.json'
    with open(path) as f:
        data = json.load(f)
    return Response(data)


WARD_NAME_MAP = {
    'port_reitz': 'Port Reitz Ward',
    'kipevu': 'Kipevu Ward',
    'airport': 'Airport Ward',
    'changamwe': 'Changamwe Ward',
    'chaani': 'Chaani Ward',
    'jomvu_kuu': 'Jomvu Kuu Ward',
    'miritini': 'Miritini Ward',
    'mikindani': 'Mikindani Ward',
    'mjambere': 'Mjambere Ward',
    'junda': 'Junda Ward',
    'bamburi': 'Bamburi Ward',
    'mwakirunge': 'Mwakirunge Ward',
    'mtopanga': 'Mtopanga Ward',
    'magogoni': 'Magogoni Ward',
    'shanzu': 'Shanzu Ward',
    'frere_town': 'Frere Town Ward',
    'ziwa_la_ngombe': "Ziwa La Ng'ombe Ward",
    'mkomani': 'Mkomani Ward',
    'kongowea': 'Kongowea Ward',
    'kadzandani': 'Kadzandani Ward',
    'mtongwe': 'Mtongwe Ward',
    'shika_adabu': 'Shika Adabu Ward',
    'bofu': 'Bofu Ward',
    'likoni': 'Likoni Ward',
    'timbwani': 'Timbwani Ward',
    'mji_wa_kale': 'Makadara Ward-mji Wa Kale Ward',
    'tudor': 'Tudor Ward',
    'tononoka': 'Tononoka Ward',
    'majengo': 'Majengo Ward',
    'shimanzi': 'Ganjoni Ward-shimanzi Ward',
}


@api_view(['GET'])
def ward_boundary(request, ward_key):
    import json
    from pathlib import Path
    from rest_framework.response import Response as DRFResponse

    ward_name = WARD_NAME_MAP.get(ward_key)
    if not ward_name:
        return DRFResponse({'error': 'Unknown ward'}, status=404)

    path = Path(__file__).resolve().parent.parent / 'geo' / 'data' / 'mombasa_wards.json'
    with open(path) as f:
        data = json.load(f)

    for feature in data['features']:
        if feature['properties'].get('ward') == ward_name:
            return DRFResponse(feature)

    return DRFResponse({'error': 'Ward boundary not found'}, status=404)
