from django.core.management.base import BaseCommand
from Recommendation.models import ParkingLot, ParkingPreference

class Command(BaseCommand):
    help = 'Generate ParkingPreference data for all ParkingLots'

    def handle(self, *args, **kwargs):
        preferences = ['pay-less', 'walk-less']

        for parking_lot in ParkingLot.objects.all():
            for preference in preferences:
                if not ParkingPreference.objects.filter(parking_lot=parking_lot, preference=preference).exists():
                    ParkingPreference.objects.create(
                        parking_lot=parking_lot,
                        preference=preference
                    )
        self.stdout.write(self.style.SUCCESS("ParkingPreference data generated successfully!"))
