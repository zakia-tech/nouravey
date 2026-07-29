from django.core.management.base import BaseCommand

from apps.satellite.services import refresh_satellite_hotspots


class Command(BaseCommand):
    help = "Fetches active fire/thermal hotspots from NASA FIRMS and saves them as SatelliteHotspot records."

    def handle(self, *args, **options):
        self.stdout.write("Fetching latest satellite hotspot data from FIRMS...")

        created = refresh_satellite_hotspots()

        if not created:
            self.stdout.write(self.style.WARNING("No active hotspots detected in the last 24 hours. This is normal."))
            return

        self.stdout.write(self.style.SUCCESS(f"Saved {len(created)} hotspot(s):"))
        for hotspot in created:
            self.stdout.write(f"  - {hotspot}")
