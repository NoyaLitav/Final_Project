from django.core.management.base import BaseCommand
from Recommendation.models import UserSetting
import csv
import os

class Command(BaseCommand):
    help = 'Import users from a CSV file'

    def handle(self, *args, **kwargs):
        # Define the path to the CSV file
        file_path = os.path.join('C:', os.sep, 'Users', 'Noy', 'Documents', 'Final Project', 'RecommendationSystem', 'Recommendation', 'cleaned_users_by_username.csv')

        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Skip the header row

            for column in reader:
                user_id = int(column[0]) if column[0] else None
                name = column[1]
                username = column[2]
                password = column[3]
                email = column[4]
                default_preferences = column[5]
                default_address = column[6]
                parking_area = column[7]
                birth_year = int(column[8]) if column[8] else None
                gender = column[9]

                user = UserSetting(
                    user_id=user_id,
                    name=name,
                    username=username,
                    password=password,
                    email=email,
                    default_preferences=default_preferences,
                    default_address=default_address,
                    parking_area=parking_area,
                    birth_year=birth_year,
                    gender=gender
                )
                user.save()

        self.stdout.write(self.style.SUCCESS('Users imported successfully'))
