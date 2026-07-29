from django.core.management.base import BaseCommand

from apps.sensors.services import refresh_air_quality


class Command(BaseCommand):
    help = "Fetches the latest Mombasa air quality data from IQAir and saves it as a SensorReading."

    def handle(self, *args, **options):
        self.stdout.write("Fetching latest air quality data from IQAir...")

        reading = refresh_air_quality()

        if reading is None:
            self.stderr.write(self.style.ERROR("Failed to fetch air quality data. Check IQAIR_API_KEY and network connection."))
            return

        self.stdout.write(self.style.SUCCESS(f"Saved: {reading}"))
