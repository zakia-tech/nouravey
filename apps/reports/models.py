from django.conf import settings
from django.db import models


# Ward choices grouped by subcounty, with a lookup to auto-derive subcounty from ward
WARD_SUBCOUNTY_MAP = {
    # Changamwe
    'port_reitz': ('Port Reitz', 'Changamwe'),
    'kipevu': ('Kipevu', 'Changamwe'),
    'airport': ('Airport', 'Changamwe'),
    'changamwe': ('Changamwe', 'Changamwe'),
    'chaani': ('Chaani', 'Changamwe'),
    # Jomvu
    'jomvu_kuu': ('Jomvu Kuu', 'Jomvu'),
    'miritini': ('Miritini', 'Jomvu'),
    'mikindani': ('Mikindani', 'Jomvu'),
    # Kisauni
    'mjambere': ('Mjambere', 'Kisauni'),
    'junda': ('Junda', 'Kisauni'),
    'bamburi': ('Bamburi', 'Kisauni'),
    'mwakirunge': ('Mwakirunge', 'Kisauni'),
    'mtopanga': ('Mtopanga', 'Kisauni'),
    'magogoni': ('Magogoni', 'Kisauni'),
    'shanzu': ('Shanzu', 'Kisauni'),
    # Nyali
    'frere_town': ('Frere Town', 'Nyali'),
    'ziwa_la_ngombe': ('Ziwa la Ng\'ombe', 'Nyali'),
    'mkomani': ('Mkomani', 'Nyali'),
    'kongowea': ('Kongowea', 'Nyali'),
    'kadzandani': ('Kadzandani', 'Nyali'),
    # Likoni
    'mtongwe': ('Mtongwe', 'Likoni'),
    'shika_adabu': ('Shika Adabu', 'Likoni'),
    'bofu': ('Bofu', 'Likoni'),
    'likoni': ('Likoni', 'Likoni'),
    'timbwani': ('Timbwani', 'Likoni'),
    # Mvita
    'mji_wa_kale': ('Mji wa Kale/Makadara', 'Mvita'),
    'tudor': ('Tudor', 'Mvita'),
    'tononoka': ('Tononoka', 'Mvita'),
    'majengo': ('Majengo', 'Mvita'),
    'shimanzi': ('Shimanzi/Ganjoni', 'Mvita'),
}

WARD_CHOICES = [(key, label) for key, (label, _) in WARD_SUBCOUNTY_MAP.items()]

SUBCOUNTY_CHOICES = [
    ('changamwe', 'Changamwe'),
    ('jomvu', 'Jomvu'),
    ('kisauni', 'Kisauni'),
    ('nyali', 'Nyali'),
    ('likoni', 'Likoni'),
    ('mvita', 'Mvita'),
]

INPUT_TYPE_CHOICES = [
    ('text', 'Text'),
    ('voice', 'Voice'),
]

POLLUTION_TYPE_CHOICES = [
    ('smoke', 'Smoke'),
    ('dust', 'Dust'),
    ('burning', 'Open Burning'),
    ('industrial', 'Industrial'),
    ('unknown', 'Unknown'),
]

STATUS_CHOICES = [
    ('unresolved', 'Unresolved'),
    ('in_progress', 'In Progress'),
    ('resolved', 'Resolved'),
]


class Report(models.Model):
    # Location
    ward = models.CharField(max_length=50, choices=WARD_CHOICES)
    subcounty = models.CharField(max_length=50, choices=SUBCOUNTY_CHOICES, editable=False)
    latitude = models.FloatField()
    longitude = models.FloatField()

    # Citizen-submitted evidence
    photo = models.ImageField(upload_to='reports/photos/')
    input_type = models.CharField(max_length=10, choices=INPUT_TYPE_CHOICES)
    text_description = models.TextField(blank=True)
    voice_note = models.FileField(upload_to='reports/voice/', blank=True, null=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    # Gemma-structured fields (only ever set for approved/relevant reports)
    pollution_type = models.CharField(max_length=20, choices=POLLUTION_TYPE_CHOICES)
    severity = models.IntegerField()  # 1-5, raw value; label mapping happens at display layer
    confidence = models.FloatField()  # 0-1
    likely_cause = models.TextField(blank=True)

    # Municipal workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unresolved')
    status_updated_at = models.DateTimeField(auto_now=True)
    status_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='status_updates',
    )

    def save(self, *args, **kwargs):
        # Auto-derive subcounty from the selected ward
        if self.ward in WARD_SUBCOUNTY_MAP:
            _, subcounty_label = WARD_SUBCOUNTY_MAP[self.ward]
            self.subcounty = subcounty_label.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_pollution_type_display()} report in {self.get_ward_display()} ({self.submitted_at:%Y-%m-%d})"

    class Meta:
        ordering = ['-submitted_at']
