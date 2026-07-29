"""
Management command: seed_demo_data

Creates realistic-looking demo reports spread across Mombasa wards,
forming 5 distinct hotspot clusters that tell the "scattered reports →
clustered hotspot" story for the demo.

Usage:
    python manage.py seed_demo_data           # add demo data
    python manage.py seed_demo_data --clear   # wipe all reports/hotspots first, then seed
    python manage.py seed_demo_data --skip-narrative  # skip Gemma narrative (faster, offline)
"""

import io
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

try:
    from PIL import Image, ImageDraw
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

from apps.reports.models import Report


# Ward anchor coordinates (centre-point for each ward used in seeding)
# Jitter is applied per-report so pins don't stack on the map.
WARD_COORDS = {
    'mwakirunge':   (-3.9900, 39.7150),
    'bamburi':      (-3.9850, 39.7250),
    'shanzu':       (-3.9550, 39.7300),
    'mtopanga':     (-3.9700, 39.7200),
    'changamwe':    (-4.0200, 39.6450),
    'kipevu':       (-4.0300, 39.6250),
    'port_reitz':   (-4.0150, 39.6300),
    'airport':      (-4.0280, 39.6380),
    'likoni':       (-4.0800, 39.6600),
    'shika_adabu':  (-4.0750, 39.6620),
    'timbwani':     (-4.0950, 39.6650),
    'mji_wa_kale':  (-4.0600, 39.6700),
    'majengo':      (-4.0550, 39.6720),
    'tudor':        (-4.0450, 39.6650),
    'shimanzi':     (-4.0600, 39.6600),
    'kongowea':     (-4.0100, 39.7050),
    'mikindani':    (-4.0100, 39.6650),
    'miritini':     (-4.0050, 39.6580),
}


# Demo report definitions grouped into 5 narrative clusters
DEMO_REPORTS = [

    # CLUSTER A: Mwakirunge Dumpsite Fire (Kisauni)
    # High-severity, multi-type cluster. The anchor story for the demo.
    {
        'ward': 'mwakirunge', 'pollution_type': 'burning', 'severity': 5,
        'confidence': 0.96, 'input_type': 'text',
        'text_description': (
            "Kuna moto mkubwa unaowaka saa hii karibu na dampo la Mwakirunge. "
            "Moshi mzito mweusi unaingia kwenye nyumba za jirani na watu wanakohoa. "
            "Watoto wamekaa ndani lakini moshi umeingia hata ndani ya nyumba."
        ),
        'likely_cause': "Moto wa taka ngumu dampo la Mwakirunge — takataka za plastiki na taya zinaungua",
        'status': 'in_progress',
    },
    {
        'ward': 'mwakirunge', 'pollution_type': 'burning', 'severity': 4,
        'confidence': 0.91, 'input_type': 'text',
        'text_description': (
            "Thick black smoke rising from the Mwakirunge area since early morning. "
            "The smell is unbearable — it smells like burning plastic and rubber. "
            "I can see the fire from my window, it has been going for over 3 hours now."
        ),
        'likely_cause': "Open burning of mixed municipal waste including plastics and vehicle tyres at Mwakirunge landfill",
        'status': 'in_progress',
    },
    {
        'ward': 'mwakirunge', 'pollution_type': 'industrial', 'severity': 4,
        'confidence': 0.87, 'input_type': 'text',
        'text_description': (
            "Smoke from the dump is getting worse in the afternoon. "
            "Three separate fire points visible from the main road. "
            "Matatu drivers are complaining about poor visibility near the junction."
        ),
        'likely_cause': "Multiple fire points at Mwakirunge landfill, likely reignited from yesterday's burning",
        'status': 'in_progress',
    },
    {
        'ward': 'mtopanga', 'pollution_type': 'smoke', 'severity': 3,
        'confidence': 0.82, 'input_type': 'text',
        'text_description': (
            "Smoke drifting from Mwakirunge direction is affecting Mtopanga as well. "
            "The sky has a brownish haze. My asthmatic child had an episode this morning."
        ),
        'likely_cause': "Smoke drift from Mwakirunge landfill fire reaching adjacent Mtopanga ward",
        'status': 'resolved',
    },
    {
        'ward': 'mwakirunge', 'pollution_type': 'burning', 'severity': 3,
        'confidence': 0.78, 'input_type': 'text',
        'text_description': (
            "Moshi bado unaendelea usiku. Wenyeji wanaomba serikali kuchukua hatua "
            "dhidi ya watu wanaochoma taka usiku badala ya asubuhi."
        ),
        'likely_cause': "Continued night burning at Mwakirunge dumpsite — residents report this is a recurring pattern",
        'status': 'unresolved',
    },

    # CLUSTER B: Changamwe Industrial Corridor
    # Port-adjacent industrial emissions. Moderate-high severity.
    {
        'ward': 'changamwe', 'pollution_type': 'industrial', 'severity': 4,
        'confidence': 0.93, 'input_type': 'text',
        'text_description': (
            "Heavy grey smoke from the factory near Changamwe roundabout. "
            "This has been going on since Monday — the stack is emitting continuously "
            "and the smell is chemical, not like burning wood or rubbish."
        ),
        'likely_cause': "Industrial stack emissions from a processing facility near Changamwe roundabout — "
                        "chemical odour suggests solvent or fuel combustion",
        'status': 'unresolved',
    },
    {
        'ward': 'kipevu', 'pollution_type': 'industrial', 'severity': 4,
        'confidence': 0.89, 'input_type': 'text',
        'text_description': (
            "Kipevu industrial area is producing a lot of smoke and fumes. "
            "Workers in the area have complained of headaches and eye irritation. "
            "The emissions seem to be worst between 6am and 10am."
        ),
        'likely_cause': "Industrial emissions from Kipevu oil storage and processing facilities during morning operations",
        'status': 'resolved',
    },
    {
        'ward': 'changamwe', 'pollution_type': 'smoke', 'severity': 3,
        'confidence': 0.80, 'input_type': 'text',
        'text_description': (
            "Moshi mzito unaonekana kutoka pande za bandari asubuhi. "
            "Hewa inakaa nzito na inaumiza macho. Watoto wanaenda shule kupita hapo."
        ),
        'likely_cause': "Smoke from port industrial operations, likely vessel emissions or cargo handling equipment",
        'status': 'unresolved',
    },
    {
        'ward': 'port_reitz', 'pollution_type': 'industrial', 'severity': 3,
        'confidence': 0.76, 'input_type': 'text',
        'text_description': (
            "Fumes near Port Reitz, especially on the road towards the container terminal. "
            "Smells like diesel and something chemical. Visibility on the road is reduced."
        ),
        'likely_cause': "Diesel exhaust and industrial fumes from container terminal heavy vehicle operations",
        'status': 'unresolved',
    },

    # CLUSTER C: Likoni Ferry Diesel Exhaust
    # Lower severity but high citizen concern — busy commuter route.
    {
        'ward': 'likoni', 'pollution_type': 'smoke', 'severity': 3,
        'confidence': 0.85, 'input_type': 'text',
        'text_description': (
            "The queue of vehicles waiting for the Likoni ferry produces thick diesel "
            "exhaust fumes. During rush hour, the air quality is terrible — you can "
            "taste the smoke. This is daily, not a one-off event."
        ),
        'likely_cause': "Diesel exhaust from idling matatus, trucks and buses queuing at Likoni ferry terminal "
                        "— problem worsens during morning and evening peak hours",
        'status': 'unresolved',
    },
    {
        'ward': 'shika_adabu', 'pollution_type': 'smoke', 'severity': 2,
        'confidence': 0.79, 'input_type': 'text',
        'text_description': (
            "Smoke from vehicle exhausts near the ferry approach road "
            "drifts into the Shika Adabu residential area. It is worse in the morning "
            "between 6:30 and 8:30. The smell stays even after traffic clears."
        ),
        'likely_cause': "Diesel exhaust drift from Likoni ferry approach road affecting adjacent residential ward",
        'status': 'in_progress',
    },
    {
        'ward': 'likoni', 'pollution_type': 'dust', 'severity': 2,
        'confidence': 0.71, 'input_type': 'text',
        'text_description': (
            "Vumbi na moshi karibu na kivuko cha Likoni. Magari mengi yanasimama "
            "muda mrefu na kutoa moshi mwingi. Watoto na wazee wanaumia zaidi."
        ),
        'likely_cause': "Combined dust from unpaved waiting area and diesel exhaust at Likoni ferry terminal",
        'status': 'unresolved',
    },

    # CLUSTER D: Old Town / Mvita Waste Burning
    # Evening waste burning — recurring pattern in dense urban area.
    {
        'ward': 'mji_wa_kale', 'pollution_type': 'burning', 'severity': 3,
        'confidence': 0.88, 'input_type': 'text',
        'text_description': (
            "Waste burning near the old town walls every evening around 6 - 8pm. "
            "The smoke mixes with the narrow street air and is very difficult to breathe. "
            "Tourists and residents complain but it happens every day."
        ),
        'likely_cause': "Informal daily waste burning at collection points in Mji wa Kale — "
                        "likely due to delayed municipal waste collection in the dense old town area",
        'status': 'unresolved',
    },
    {
        'ward': 'majengo', 'pollution_type': 'burning', 'severity': 3,
        'confidence': 0.83, 'input_type': 'text',
        'text_description': (
            "Moshi kutoka kwa kuchoma takataka mtaani Majengo. Kila jioni watu "
            "wanachoma taka kwenye pembe za barabara. Hakuna mahali pa kupeleka taka "
            "kwa hiyo wachoma. Hewa ni mbaya usiku wote."
        ),
        'likely_cause': "Nightly household waste burning in Majengo — inadequate waste collection forcing "
                        "residents to burn as disposal method",
        'status': 'in_progress',
    },
    {
        'ward': 'majengo', 'pollution_type': 'smoke', 'severity': 3,
        'confidence': 0.77, 'input_type': 'text',
        'text_description': (
            "Smoke from waste fires in Majengo is significant tonight. "
            "I counted at least four separate burning piles on one street. "
            "The smoke is hanging low because of the humidity."
        ),
        'likely_cause': "Multiple simultaneous waste burning incidents in Majengo exacerbated by high evening humidity "
                        "trapping smoke at street level",
        'status': 'unresolved',
    },

    # CLUSTER E: Bamburi Beach Road Construction Dust
    # Lower severity, dust-only. Shows the dust pollution type on the map.
    {
        'ward': 'bamburi', 'pollution_type': 'dust', 'severity': 2,
        'confidence': 0.82, 'input_type': 'text',
        'text_description': (
            "Construction work on Bamburi beach road is producing large amounts of dust. "
            "No water spraying or dust suppression measures visible. "
            "Nearby shops are coated in white dust and business is affected."
        ),
        'likely_cause': "Road construction without dust suppression — dry excavation and unpaved diversion routes "
                        "along Bamburi beach road",
        'status': 'unresolved',
    },
    {
        'ward': 'bamburi', 'pollution_type': 'dust', 'severity': 2,
        'confidence': 0.76, 'input_type': 'text',
        'text_description': (
            "Vumbi kubwa kutoka ujenzi karibu na Bamburi. Watu wanaopita barabarani "
            "wanafunikwa na vumbi. Hakuna hatua zozote za kuzuia vumbi zinazoonekana."
        ),
        'likely_cause': "Dust from construction earthworks on Bamburi beach road with no visible mitigation measures",
        'status': 'unresolved',
    },
    {
        'ward': 'bamburi', 'pollution_type': 'dust', 'severity': 1,
        'confidence': 0.68, 'input_type': 'text',
        'text_description': (
            "Some dust from the road works near Bamburi market. Not as bad as last week "
            "but still noticeable. Food stalls near the construction are suffering."
        ),
        'likely_cause': "Residual construction dust from Bamburi beach road works — reduced but ongoing",
        'status': 'unresolved',
    },

    # ── ISOLATED REPORT: Shanzu (single unconfirmed report) ────────────────
    # Demonstrates a lone report that has not yet formed a hotspot.
    {
        'ward': 'shanzu', 'pollution_type': 'smoke', 'severity': 2,
        'confidence': 0.61, 'input_type': 'text',
        'text_description': (
            "Noticed some smoke near Shanzu beach hotel area this morning. "
            "Could not identify the source — might be a cooking fire or something nearby. "
            "Lasted about 20 minutes and then cleared."
        ),
        'likely_cause': "Unconfirmed smoke source in Shanzu — possibly cooking fire or small waste burn, "
                        "cleared quickly; single report, low confidence",
        'status': 'unresolved',
    },
]


def _make_placeholder_photo(ward: str, pollution_type: str) -> ContentFile:
    """
    Generate a minimal placeholder JPEG using Pillow.
    The image is a solid colour block labelled with ward + type —
    sufficient for the demo without needing real uploaded photos.
    Falls back to a tiny 1×1 grey JPEG if Pillow is unavailable.
    """
    PALETTE = {
        'burning':    (180, 60,  20),
        'smoke':      (100, 100, 100),
        'dust':       (194, 162, 100),
        'industrial': (60,  80,  120),
        'unknown':    (150, 150, 150),
    }

    if not HAS_PILLOW:
        # Minimal valid JPEG bytes (1×1 grey pixel)
        fallback = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
            b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
            b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e'
            b'..;L..;L\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
            b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08'
            b'\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03'
            b'\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12'
            b'!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1'
            b'\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJ'
            b'STUVWXYZ\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd8\xff\xd9'
        )
        return ContentFile(fallback, name=f"demo_{ward}_{pollution_type}.jpg")

    colour = PALETTE.get(pollution_type, (150, 150, 150))
    # Add slight brightness variation so photos aren't identical
    r, g, b = [max(0, min(255, c + random.randint(-20, 20))) for c in colour]

    img = Image.new('RGB', (400, 300), color=(r, g, b))
    draw = ImageDraw.Draw(img)

    # Simple label overlay
    label = f"{ward.replace('_', ' ').title()}\n{pollution_type.upper()}"
    draw.multiline_text((20, 120), label, fill=(255, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=70)
    buf.seek(0)
    return ContentFile(buf.read(), name=f"demo_{ward}_{pollution_type}.jpg")


class Command(BaseCommand):
    help = (
        "Seed the database with realistic demo pollution reports across Mombasa wards. "
        "Creates 5 distinct hotspot clusters for demonstration purposes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing Report and Hotspot records before seeding.',
        )
        parser.add_argument(
            '--skip-narrative',
            action='store_true',
            help='Skip the Gemma narrative generation step (faster, works offline).',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_existing()

        self.stdout.write(f"Seeding {len(DEMO_REPORTS)} demo reports across {len(WARD_COORDS)} wards...\n")

        created = 0
        failed = 0
        now = timezone.now()

        # In-memory ward → hotspot PK map so same-ward reports always find
        # the same hotspot without relying on a DB lookup that can race with
        # mid-loop saves.
        ward_hotspot_map = {}

        for i, data in enumerate(DEMO_REPORTS):
            try:
                ward = data['ward']
                base_lat, base_lon = WARD_COORDS.get(ward, (-4.05, 39.67))

                # Spread pins within ~100m of the ward centre
                lat = base_lat + random.uniform(-0.001, 0.001)
                lon = base_lon + random.uniform(-0.001, 0.001)

                # Stagger submission times over the past 72 hours so the
                # timeline looks realistic
                hours_ago = random.uniform(0, 72)
                submitted_at = now - timedelta(hours=hours_ago)

                report = Report(
                    ward=ward,
                    latitude=lat,
                    longitude=lon,
                    input_type=data['input_type'],
                    text_description=data['text_description'],
                    pollution_type=data['pollution_type'],
                    severity=data['severity'],
                    confidence=data['confidence'],
                    likely_cause=data['likely_cause'],
                    status=data.get('status', 'unresolved'),
                )
                report.photo.save(
                    f"demo_{ward}_{i}.jpg",
                    _make_placeholder_photo(ward, data['pollution_type']),
                    save=False,
                )
                report.save()

                # Fix auto_now_add so reports show realistic past timestamps
                Report.objects.filter(pk=report.pk).update(submitted_at=submitted_at)

                created += 1
                self.stdout.write(f"  [{created:02d}/{len(DEMO_REPORTS)}] {report}")

                # Cluster using the in-memory ward map — no DB distance lookup
                self._cluster_report(report, ward_hotspot_map)

            except Exception as exc:
                failed += 1
                self.stderr.write(self.style.ERROR(f"  FAILED report {i+1}: {exc}"))

        # Score and narrate all hotspots once, after all reports are attached
        self._finalise_hotspots(ward_hotspot_map, skip_narrative=options['skip_narrative'])

        style = self.style.SUCCESS if failed == 0 else self.style.WARNING
        self.stdout.write(style(
            f"\nDone. {created} reports created, {failed} failed. "
            f"Run 'python manage.py shell' and check Report.objects.count() to verify."
        ))

    def _clear_existing(self):
        """Delete all reports and hotspots (demo reset)."""
        report_count = Report.objects.count()
        Report.objects.all().delete()
        self.stdout.write(self.style.WARNING(
            f"Cleared {report_count} existing report(s)."
        ))

        try:
            from apps.analysis.models import Hotspot
            hotspot_count = Hotspot.objects.count()
            Hotspot.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"Cleared {hotspot_count} existing hotspot(s)."
            ))
        except ImportError:
            pass

    def _cluster_report(self, report, ward_hotspot_map):
        """
        Seed-specific clustering using an in-memory ward → hotspot PK map.

        Bypasses the geo service's 500m radius DB lookup entirely. The real
        cluster_report() checks distance from an existing hotspot's center,
        which can create duplicate hotspots when random jitter places a report
        just outside that radius mid-loop. Tracking ward → hotspot PK in memory
        guarantees every same-ward report lands on the same hotspot regardless
        of exact coordinates.

        Scoring and narrative are deferred to _finalise_hotspots() so that all
        reports are attached before scores are calculated.
        """
        try:
            from apps.analysis.models import Hotspot

            if report.ward in ward_hotspot_map:
                hotspot = Hotspot.objects.get(pk=ward_hotspot_map[report.ward])
            else:
                hotspot = Hotspot.objects.create(
                    ward=report.ward,
                    is_active=True,
                    center_latitude=report.latitude,
                    center_longitude=report.longitude,
                    subcounty=report.subcounty,
                )
                ward_hotspot_map[report.ward] = hotspot.pk

            hotspot.reports.add(report)

            # Keep center accurate as reports accumulate
            all_reports = list(hotspot.reports.all())
            hotspot.center_latitude = sum(r.latitude for r in all_reports) / len(all_reports)
            hotspot.center_longitude = sum(r.longitude for r in all_reports) / len(all_reports)
            hotspot.save(update_fields=['center_latitude', 'center_longitude'])

        except Exception as exc:
            self.stderr.write(self.style.WARNING(
                f"    Clustering warning for {report}: {exc}"
            ))

    def _finalise_hotspots(self, ward_hotspot_map, skip_narrative=False):
        """
        Score and optionally narrate all hotspots created during this seed run.
        Called once after all reports are clustered so scores reflect the full
        report set for each hotspot rather than a partial mid-loop snapshot.
        """
        from apps.analysis.models import Hotspot
        from apps.analysis.scorers import score_hotspot

        if not ward_hotspot_map:
            return

        self.stdout.write(f"\nFinalising {len(ward_hotspot_map)} hotspot(s)...")

        for ward, pk in ward_hotspot_map.items():
            try:
                hotspot = Hotspot.objects.get(pk=pk)
                score_hotspot(hotspot)

                if skip_narrative:
                    hotspot.narrative = (
                        f"Demo data: {hotspot.reports.count()} report(s) in "
                        f"{hotspot.get_ward_display()} ward. "
                        f"Severity: {hotspot.severity_label}."
                    )
                    hotspot.recommended_action = (
                        "Dispatch field inspector to verify and document the incident."
                    )
                    hotspot.predicted_trend = 'insufficient_data'
                    hotspot.prediction_confidence = 0.0
                    hotspot.prediction_rationale = 'Prediction skipped in fast seed mode.'
                else:
                    from apps.analysis.services import generate_hotspot_narrative, predict_hotspot_trend
                    generate_hotspot_narrative(hotspot)
                    predict_hotspot_trend(hotspot)

                hotspot.save()
                self.stdout.write(
                    f"  {hotspot.get_ward_display():25} [{hotspot.severity_label.upper():8}] "
                    f"score={hotspot.score:.1f}, {hotspot.reports.count()} report(s)"
                )

            except Exception as exc:
                self.stderr.write(self.style.WARNING(
                    f"  Finalise warning for ward {ward}: {exc}"
                ))
