from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response

from apps.analysis.services import classify_report, process_report_into_hotspot
from .models import Report
from .serializers import ReportSubmissionSerializer, ReportOutputSerializer


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def submit_report(request):
    serializer = ReportSubmissionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    classification = classify_report(
        photo=data['photo'],
        text_description=data.get('text_description', ''),
        voice_note=data.get('voice_note'),
        debug=True,
    )

    if not classification['is_relevant']:
        return Response({
            'success': False,
            'message': 'Not relevant to pollution reporting',
            'rejection_reason': classification.get('rejection_reason', 'This does not appear to be a pollution report.'),
        }, status=status.HTTP_200_OK)

    report = Report.objects.create(
        ward=data['ward'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        photo=data['photo'],
        input_type=data['input_type'],
        text_description=data.get('text_description', ''),
        voice_note=data.get('voice_note'),
        pollution_type=classification['pollution_type'],
        severity=classification['severity'],
        confidence=classification['confidence'],
        likely_cause=classification['likely_cause'],
    )

    hotspot = process_report_into_hotspot(report)

    output = ReportOutputSerializer(report)

    return Response({
        'success': True,
        'message': 'Report received',
        'report': output.data,
        'hotspot': {
            'id': hotspot.id,
            'score': hotspot.score,
            'severity_label': hotspot.severity_label,
            'narrative': hotspot.narrative,
            'recommended_action': hotspot.recommended_action,
        },
    }, status=status.HTTP_201_CREATED)


def submit_report_page(request):
    from django.shortcuts import render
    return render(request, 'reports/submit.html')
