import csv
from django.core.management.base import BaseCommand
from Recommendation.models import ParkingLot  # Adjust this import to match your actual app name and model

import csv
from django.core.management.base import BaseCommand
from Recommendation.models import ParkingLot  # Adjust this import to match your actual app name and model


class Command(BaseCommand):
    help = 'Load parking lot data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file to load data from')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        with open(csv_file, newline='', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            # Print the column names for debugging
            print("Columns in the CSV file:", reader.fieldnames)
            for row in reader:
                try:
                    code = int(row['code'].strip())  # Ensure the code is an integer
                    parking_lot = ParkingLot(
                        code=code,
                        name=row['name'].strip(),
                        address=row['address'].strip(),
                        gps_latitude=row['gps_latitude'] or None,
                        gps_longitude=row['gps_longitude'] or None,
                        day_hour_weekday=row.get('day_hour_weekday', '').strip() or None,
                        daily_rate_day_weekday=row.get('daily_rate_day_weekday', '').strip() or None,
                        hourly_rate_day_weekday=row.get('hourly_rate_day_weekday', '').strip() or None,
                        daily_night_rate_weekday=row.get('daily_night_rate_weekday', '').strip() or None,
                        hourly_night_rate_weekday=row.get('hourly_night_rate_weekday', '').strip() or None,
                        day_hour_friday=row.get('day_hours_Friday', '').strip() or None,
                        daily_rate_day_friday=row.get('daily_rate_day_friday', '').strip() or None,
                        hourly_rate_day_friday=row.get('hourly_rate_day_friday', '').strip() or None,
                        daily_night_rate_friday=row.get('daily_rate_night_friday', '').strip() or None,
                        hourly_night_rate_friday=row.get('hourly_night_rate_friday', '').strip() or None,
                        day_hour_saturday=row.get('day_hours_Saturday', '').strip() or None,
                        daily_rate_day_saturday=row.get('daily_rate_day_saturday', '').strip() or None,
                        hourly_rate_day_saturday=row.get('hourly_rate_day_saturday', '').strip() or None,
                        daily_night_rate_saturday=row.get('daily_rate_night_saturday', '').strip() or None,
                        hourly_night_rate_saturday=row.get('hourly_night_rate_saturday', '').strip() or None,
                        resident_discount=row.get('resident_discount', '').strip() or None,
                        close_to_home=row.get('close_to_home', '').strip().lower() in ['true', '1', 'yes'],
                        notes=row.get('notes', '').strip() or None,
                    )
                    parking_lot.save()
                except Exception as e:
                    print(f"Error processing row: {row}, Error: {e}")

        self.stdout.write(self.style.SUCCESS('Successfully loaded parking lot data'))
