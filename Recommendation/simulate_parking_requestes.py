import pytz

from .models import UserSetting, ParkingHistory
import pandas as pd
from datetime import datetime
import random


def simulate_parking_requests(num_entries):
    # Load the Tel Aviv addresses from the CSV file
    csv_path = r"C:\Users\Noy\Documents\Final Project\RecommendationSystem\Recommendation\tel_aviv_addresses.csv"
    addresses_df = pd.read_csv(csv_path)
    addresses = addresses_df.iloc[:, 0].tolist()  # Assuming addresses are in column A

    # Loop to create multiple simulated entries
    for _ in range(num_entries):
        # Randomly select a user from UserSettings
        user = UserSetting.objects.order_by('?').first()

        fetch_time = datetime.now().astimezone(pytz.timezone('Asia/Jerusalem')).strftime('%Y-%m-%d %H:%M')

        # Randomly select an address
        address = random.choice(addresses)

        # Randomly select a preference
        preference = random.choice(['pay-less', 'walk-less'])

        # Randomly select a parking duration
        parking_duration = random.choice(['Short-term', 'Long-term'])

        # Save the simulated data in ParkingHistory model
        ParkingHistory.objects.create(
            user=user,
            search_datetime=fetch_time,
            search_address=address,
            preference=preference,
            parking_duration=parking_duration,
            recommendation_1=None,
            recommendation_2=None,
            recommendation_3=None,
            final_choice=None
        )

    print(f"Simulated {num_entries} parking request entries successfully.")

