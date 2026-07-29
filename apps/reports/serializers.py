from rest_framework import serializers

from .models import Report, WARD_CHOICES

MAX_PHOTO_SIZE_MB = 5
MAX_VOICE_SIZE_MB = 10


class ReportSubmissionSerializer(serializers.Serializer):
    """Validates incoming citizen report data before it reaches Gemma."""

    ward = serializers.ChoiceField(choices=WARD_CHOICES)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    photo = serializers.ImageField()
    input_type = serializers.ChoiceField(choices=['text', 'voice'])
    text_description = serializers.CharField(required=False, allow_blank=True)
    voice_note = serializers.FileField(required=False)

    def validate_photo(self, value):
        max_bytes = MAX_PHOTO_SIZE_MB * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError(f"Photo must be under {MAX_PHOTO_SIZE_MB}MB.")
        return value

    def validate_voice_note(self, value):
        max_bytes = MAX_VOICE_SIZE_MB * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError(f"Voice note must be under {MAX_VOICE_SIZE_MB}MB.")
        return value

    def validate(self, data):
        input_type = data.get('input_type')
        text_description = data.get('text_description', '').strip()
        voice_note = data.get('voice_note')

        if input_type == 'text' and not text_description:
            raise serializers.ValidationError({
                'text_description': 'Text description is required when input_type is "text".'
            })

        if input_type == 'voice' and not voice_note:
            raise serializers.ValidationError({
                'voice_note': 'Voice note is required when input_type is "voice".'
            })

        # Enforce mutual exclusivity — don't let both be populated
        if input_type == 'text' and voice_note:
            raise serializers.ValidationError('Only one of text_description or voice_note should be provided.')

        if input_type == 'voice' and text_description:
            raise serializers.ValidationError('Only one of text_description or voice_note should be provided.')

        return data


class ReportOutputSerializer(serializers.ModelSerializer):
    """Used to represent a saved Report back to the frontend."""

    class Meta:
        model = Report
        fields = [
            'id', 'ward', 'subcounty', 'latitude', 'longitude', 'photo',
            'input_type', 'text_description', 'voice_note', 'submitted_at',
            'pollution_type', 'severity', 'confidence', 'likely_cause', 'status',
        ]
        read_only_fields = fields
