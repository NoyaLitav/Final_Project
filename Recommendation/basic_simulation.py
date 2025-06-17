import datetime
from datetime import datetime
import requests
from time import sleep
import random
import time
from .models import ParkingHistory, ParkingLot
from .views import address_to_coordinates, sort_results, \
    recommend_parking_lots, parse_duration, update_user_parking_rating
import pandas as pd
from googlemaps import Client

gmaps = Client(key='AIzaSyA1wuLzDKX3kRLMKo4fXekDjwGmEDxmuxo')  # Replace with your actual Google Maps API key

def simulate_basic_recommendations():
    # Fetch all parking history records
    parking_histories = ParkingHistory.objects.all()

    # Iterate through each parking history record
    for history in parking_histories:
        try:
            # Skip if recommendations already exist
            if history.recommendation_1 or history.recommendation_2 or history.recommendation_3:
                print(f"Skipping history ID {history.id} for user {history.user.username} as it already has recommendations.")
                continue

            # Extract user, destination, preferences, duration, and the search datetime from history
            user = history.user
            if not user:
                print(f"Skipping history ID {history.id} due to missing user.")
                continue

            destination = history.search_address
            preferences = history.preference
            parking_duration = history.parking_duration
            simulation_time = history.search_datetime  # Use the search datetime from history

            # Geocode the destination address
            address_coordinates = address_to_coordinates(destination)

            if not address_coordinates:
                print(f"Failed to geocode address {destination} for user {user.username}")
                continue

            # Fetch parking lot data with coordinates, passing the simulation time
            parking_lots_df, fetch_time = get_parking_lot_data_with_coordinates_simulation(simulation_time)
            if parking_lots_df is None:
                print(f"Failed to fetch parking lot data for user {user.username}, skipping this entry.")
                continue

            # Fetch parking costs, passing the simulation time
            parking_costs_df = calculate_parking_cost_simulation(user, simulation_time)

            # Initialize list to store missing coordinates parking lots
            unsorted_results = []
            for index, row in parking_lots_df.iterrows():
                parking_lot_coordinates_str = row['parking_lot_coordinates']
                parking_lot_name = row.get('name', 'Unknown')
                parking_lot_code = row.get('code', 'Unknown')

                if pd.isna(parking_lot_coordinates_str) or parking_lot_coordinates_str == 'nan':
                    continue

                parking_lot_coordinates = tuple(map(float, parking_lot_coordinates_str.split(',')))

                if len(parking_lot_coordinates) != 2 or any(map(pd.isna, parking_lot_coordinates)):
                    continue

                try:
                    distance_matrix_result = None
                    for attempt in range(3):  # Retry up to 3 times
                        try:
                            distance_matrix_result = gmaps.distance_matrix(
                                origins=[address_coordinates],
                                destinations=[parking_lot_coordinates],
                                mode="walking"
                            )
                            break  # Exit loop if request is successful
                        except Exception as e:
                            print(f"Error during Google Maps API call: {e}")
                            time.sleep(10)  # Wait before retrying

                    if distance_matrix_result is None:
                        print(f"Failed to get distance matrix result for {parking_lot_name} after 3 attempts.")
                        continue

                    if distance_matrix_result['rows'][0]['elements'][0]['status'] == 'OK':
                        distance_to_parking = distance_matrix_result["rows"][0]["elements"][0]["distance"]["text"]
                        walking_time = parse_duration(
                            distance_matrix_result["rows"][0]["elements"][0]["duration"]["text"])

                        # Get parking costs from the DataFrame
                        cost_info = parking_costs_df.loc[parking_costs_df['name'] == parking_lot_name].to_dict('records')[0]

                        unsorted_results.append({
                            'parking_lot_name': parking_lot_name,
                            'parking_lot_code': parking_lot_code,
                            'parking_lot_address': row['address'],
                            'distance': distance_to_parking,
                            'walking_time': walking_time,
                            'cost_2_hours': cost_info['cost_2_hours'],
                            'cost_12_hours': cost_info['cost_12_hours']
                        })

                    else:
                        print(f"Error calculating distance: {distance_matrix_result['rows'][0]['elements'][0]['status']}")
                except Exception as e:
                    print(f"Error processing parking lot {parking_lot_name}: {e}")
                    continue

            # Sort the results list based on user preferences
            sorted_results = sort_results(unsorted_results, preferences, parking_duration)

            # Recommend the best parking lots considering both walking time and cost
            recommended_results = recommend_parking_lots(sorted_results, preferences, parking_duration)

            # Save or update the parking history with the simulated recommendations
            history.recommendation_1 = ParkingLot.objects.get(code=recommended_results[0]['parking_lot_code']) if len(recommended_results) > 0 else None
            history.recommendation_2 = ParkingLot.objects.get(code=recommended_results[1]['parking_lot_code']) if len(recommended_results) > 1 else None
            history.recommendation_3 = ParkingLot.objects.get(code=recommended_results[2]['parking_lot_code']) if len(recommended_results) > 2 else None

            # Simulate the user choosing the first recommendation
            history.final_choice = history.recommendation_1  # Simulating that the user picks the first recommendation
            history.save()

            # Simulate saving the user choice (which will also update ratings)
            save_user_choice_simulation(
                parking_lot_name=history.recommendation_1.name if history.recommendation_1 else 'אחר',
                parking_lot_code=history.recommendation_1.code if history.recommendation_1 else None,
                parking_history_id=history.id,
                username=user.username
            )

            # Debug: Check if `update_user_parking_rating` is called again
            print(f"Checking if `update_user_parking_rating` is called for user {user.username} after `save_user_choice_simulation`.")

        except Exception as e:
            print(f"An error occurred while processing history ID {history.id} for user {user.username}: {e}")
            continue


def save_user_choice_simulation(parking_lot_name, parking_lot_code, parking_history_id, username):
    try:
        parking_history = ParkingHistory.objects.get(id=parking_history_id)

        # Determine the final choice based on the specified probabilities
        if random.random() < 0.2:  # 20% chance
            parking_history.final_choice = None
            parking_lot_name = 'אחר'
            parking_lot_code = None
        else:  # 80% chance to pick one of the recommendations randomly
            recommendations = [parking_history.recommendation_1, parking_history.recommendation_2, parking_history.recommendation_3]
            recommendations = [rec for rec in recommendations if rec is not None]
            if recommendations:
                parking_history.final_choice = random.choice(recommendations)
                parking_lot_name = parking_history.final_choice.name
                parking_lot_code = parking_history.final_choice.code
            else:
                parking_history.final_choice = None

        parking_history.save()

        # Debug: Print when updating the user parking rating
        print(f"Updating parking rating for user {parking_history.user.username} based on the user's choice.")

        # Update UserParkingRating based on the user's choice
        update_user_parking_rating(parking_history.user, parking_history)

    except ParkingHistory.DoesNotExist:
        print(f"Parking history not found for ID {parking_history_id}")
    except ParkingLot.DoesNotExist:
        print(f"Parking lot not found with code {parking_lot_code}")


def get_parking_lot_data_with_coordinates_simulation(simulation_time):
    """
    Fetches parking lot data, merges with coordinates, and returns merged DataFrame.
    """
    parking_lots = ParkingLot.objects.all().values()
    parking_lots_df = pd.DataFrame(list(parking_lots))

    if parking_lots_df.empty:
        print("No parking lot data found in the database.")
        return None, None  # Handle the case where no data is found in the database

    def combine_coordinates(row):
        return f"{row['gps_latitude']},{row['gps_longitude']}"

    parking_lots_df["parking_lot_coordinates"] = parking_lots_df.apply(combine_coordinates, axis=1)

    url = "https://api.tel-aviv.gov.il/parking/StationsStatus"

    # Retry mechanism for API request
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if not data:  # Check if data is empty
                    print("API returned an empty response.")
                    return None, None

                parking_data_df = pd.DataFrame(data)
                parking_data_df["AhuzotCode"] = parking_data_df["AhuzotCode"].astype(str)  # Convert AhuzotCode to string
                available_parking_lots_df = parking_data_df.query("InformationToShow != 'מלא' & InformationToShow != 'סגור'")
                merged_df = available_parking_lots_df.merge(parking_lots_df, left_on="AhuzotCode", right_on="code", how="left")

                # Use the provided simulation time instead of the current time
                fetch_time = simulation_time.strftime('%d-%m-%Y %H:%M:%S')
                print(f"**Simulated API day & time: {fetch_time}**")

                if merged_df.empty:
                    print("Merged DataFrame is empty after merging with parking_lots_df.")
                    return None, None

                return merged_df, fetch_time
            else:
                print(f"API request failed with status code: {response.status_code}")
        except Exception as e:
            print(f"API request failed on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                sleep(2)  # Wait before retrying
            else:
                return None, None

    return None, None  # Return None after all retries fail


def calculate_parking_cost_simulation(user, simulation_time):
    parking_lots = ParkingLot.objects.all().values()
    parking_lots_df = pd.DataFrame(list(parking_lots))

    results = []

    # Use the provided simulation time instead of the current time
    current_day = simulation_time.strftime('%A').lower()
    current_time = simulation_time.strftime('%H:%M')

    print(f"Simulated day: {current_day.capitalize()}, Simulated time: {current_time}")
    print("//Parking cost calculate//")

    day_mapping = {
        'monday': 'weekday',
        'tuesday': 'weekday',
        'wednesday': 'weekday',
        'thursday': 'weekday',
        'friday': 'friday',
        'saturday': 'saturday',
        'sunday': 'weekday'
    }

    # Map the current day to the appropriate column suffix
    mapped_day = day_mapping[current_day]

    for index, row in parking_lots_df.iterrows():

        # Define column names dynamically based on the mapped day
        if mapped_day == 'weekday':
            day_hour_col = 'day_hour_weekday'
            daily_rate_day_col = 'daily_rate_day_weekday'
            hourly_rate_day_col = 'hourly_rate_day_weekday'
            daily_night_rate_col = 'daily_night_rate_weekday'
            hourly_night_rate_col = 'hourly_night_rate_weekday'
        elif mapped_day == 'friday':
            day_hour_col = 'day_hour_friday'
            daily_rate_day_col = 'daily_rate_day_friday'
            hourly_rate_day_col = 'hourly_rate_day_friday'
            daily_night_rate_col = 'daily_night_rate_friday'
            hourly_night_rate_col = 'hourly_night_rate_friday'
        else:
            day_hour_col = 'day_hour_saturday'
            daily_rate_day_col = 'daily_rate_day_saturday'
            hourly_rate_day_col = 'hourly_rate_day_saturday'
            daily_night_rate_col = 'daily_night_rate_saturday'
            hourly_night_rate_col = 'hourly_night_rate_saturday'

        # Get day hour range
        if day_hour_col not in row or pd.isnull(row[day_hour_col]):
            print(f"Skipping {row['name']} due to missing day hour range.")
            continue
        day_hour_range = row[day_hour_col].strip()

        # Split the range into start and end times
        day_start, day_end = day_hour_range.split(' - ')
        day_start = day_start.strip()
        day_end = day_end.strip()

        # Convert time to datetime format for comparison
        day_start_time = datetime.strptime(day_start, '%H:%M').time()
        day_end_time = datetime.strptime(day_end, '%H:%M').time()
        current_time_obj = datetime.strptime(current_time, '%H:%M').time()

        # Determine if within day rate period
        if day_start_time <= current_time_obj <= day_end_time:
            hourly_rate = row.get(hourly_rate_day_col)
            daily_rate = row.get(daily_rate_day_col)
        else:
            hourly_rate = row.get(hourly_night_rate_col)
            daily_rate = row.get(daily_night_rate_col)

        # Skip parking lot if rates are missing
        if pd.isnull(hourly_rate) and pd.isnull(daily_rate):
            print(f"Skipping {row['name']} due to missing rates.")
            continue

        # Skip parking lot if coordinates are missing
        if pd.isnull(row.get('gps_latitude')) or pd.isnull(row.get('gps_longitude')):
            print(f"Skipping parking lot due to missing coordinates.")
            continue

        # Calculate costs
        if pd.notnull(daily_rate):
            cost_2_hours = daily_rate
            cost_12_hours = daily_rate
        else:
            if pd.notnull(hourly_rate):
                cost_2_hours = hourly_rate * 2
                cost_12_hours = hourly_rate * 12

        # Apply free parking during specific hours if parking areas match
        if user.parking_area and row.get('parking_area'):
            user_parking_areas = set(user.parking_area.split(','))
            lot_parking_areas = set(row['parking_area'].split(','))
            if user_parking_areas & lot_parking_areas:
                if datetime.strptime('19:00',
                                     '%H:%M').time() <= current_time_obj or current_time_obj <= datetime.strptime(
                        '08:00', '%H:%M').time():
                    cost_2_hours = 0
                    cost_12_hours = 0

        # Apply resident discount only if user parking area is not empty
        if user.parking_area:
            resident_discount = row.get('resident_discount', 0)
            discount_multiplier = (100 - resident_discount) / 100
            cost_2_hours *= discount_multiplier
            cost_12_hours *= discount_multiplier

        # Ensure costs are not NaN and convert to integers
        cost_2_hours = int(cost_2_hours) if not pd.isna(cost_2_hours) else 0
        cost_12_hours = int(cost_12_hours) if not pd.isna(cost_12_hours) else 0

        results.append({
            'name': row['name'],
            'cost_2_hours': cost_2_hours,
            'cost_12_hours': cost_12_hours
        })

    results_df = pd.DataFrame(results)
    return results_df


def save_user_choice_simulation(parking_lot_name, parking_lot_code, parking_history_id, username):
    try:
        parking_history = ParkingHistory.objects.get(id=parking_history_id)

        # Determine the final choice based on the specified probabilities
        parking_history.final_choice = None  # Set final_choice to None for all users
        parking_lot_name = 'אחר'
        parking_lot_code = None

        parking_history.save()

        # Update UserParkingRating based on the user's choice
        update_user_parking_rating(parking_history.user, parking_history)

        print(f"User choice saved as None and ratings updated for user {username}")

    except ParkingHistory.DoesNotExist:
        print(f"Parking history not found for ID {parking_history_id}")
    except ParkingLot.DoesNotExist:
        print(f"Parking lot not found with code {parking_lot_code}")

