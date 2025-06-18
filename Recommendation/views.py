import numpy as np
from django.shortcuts import render, redirect
from .models import UserSetting, ParkingLot, ParkingHistory, ParkingPreference, UserParkingRating
from django.http import JsonResponse
from googlemaps import Client
import requests
import pandas as pd
from datetime import datetime
import pytz
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import time
import implicit
from scipy.sparse import csr_matrix



gmaps = Client(key='AIzaSyALf9vZ3aBoQWeVn4kN-gRCS77V3PU8AFU')

def signup(request):
    if request.method == "POST":
        users = UserSetting.objects.all()
        context = {
            'users': users,
        }

        if UserSetting.objects.filter(email=request.POST["email"]).exists():
            context['email_error'] = True
            return render(request, "signup.html", context)
        if UserSetting.objects.filter(username=request.POST["username"]).exists():
            context['userName_error'] = True
            return render(request, "signup.html", context)
        else:
            user = UserSetting(
                name=request.POST["name"],
                username=request.POST["username"],
                password=request.POST["password"],
                email=request.POST["email"],
                default_preferences=request.POST["preferences"],
                default_address=request.POST["default_address"],
                parking_area=request.POST.get("parking_area", ""),  # Use get method to handle missing field
                birth_year=request.POST["birth_year"],
                gender=request.POST["gender"]
            )
            user.save()
            return redirect(reverse('login'))  # Redirect to the 'login' endpoint
    else:
        return render(request, "signup.html", {})



def homepage(request):
    return render(request, "homepage.html", {})


@login_required
def destination(request, username):
    error_flag = request.GET.get('error', False)  # Get the error flag from the request
    return render(request, 'destination.html', {'username': username, 'error': error_flag})

@login_required
def recommendation_results(request, username):
    return render(request, 'recommendation_results.html', {'username': username})


def upload_form(request):
    return render(request, "upload_form.html", {})


def parking_lots(request):
    return render(request, "parking_lots.html", {})


def check_user_sql(username, password):
    result = UserSetting.objects.raw("SELECT * \
                       FROM recommendation_userSetting \
                       WHERE username=%s AND password=%s", [username, password])
    if len(list(result)) == 0:
        return False
    return True


def login(request):
    context = {}
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        if check_user_sql(username, password):
            user = UserSetting.objects.get(username=username, password=password)
            request.session["username"] = user.username
            destination_url = reverse('destination', kwargs={'username': username})
            print(f"Redirecting to: {destination_url}")  # Debugging line
            return redirect(destination_url)
        else:
            context['login_error'] = "Username or password are incorrect"
            return render(request, "login.html", context)
    return render(request, "login.html", context)

def get_default_address(request):
    user = UserSetting.objects.get(username=request.session["username"])
    return JsonResponse({'default_address': user.default_address})


def get_default_preferences(request):
    user = UserSetting.objects.get(username=request.session["username"])
    return JsonResponse({'default_preferences': user.default_preferences})


def logout(request):
    return render(request, "login.html")


def get_parking_lot_data_with_coordinates(request):
    """
    Fetches parking lot data, merges with coordinates, and returns merged DataFrame.
    """
    parking_lots = ParkingLot.objects.all().values()
    parking_lots_df = pd.DataFrame(list(parking_lots))

    if parking_lots_df.empty:
        return None, None  # Handle the case where no data is found in the database
    def combine_coordinates(row):
        return f"{row['gps_latitude']},{row['gps_longitude']}"

    parking_lots_df["parking_lot_coordinates"] = parking_lots_df.apply(combine_coordinates, axis=1)

    url = "https://api.tel-aviv.gov.il/parking/StationsStatus"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        parking_data_df = pd.DataFrame(data)
        parking_data_df["AhuzotCode"] = parking_data_df["AhuzotCode"].astype(str)  # Convert AhuzotCode to string
        available_parking_lots_df = parking_data_df.query("InformationToShow != 'מלא' & InformationToShow != 'סגור'")
        merged_df = available_parking_lots_df.merge(parking_lots_df, left_on="AhuzotCode", right_on="code", how="left")

        # Get the fetch time
        fetch_time = datetime.now().astimezone(pytz.timezone('Asia/Jerusalem')).strftime('%d-%m-%Y %H:%M')

        # # Set the timezone
        # timezone = pytz.timezone('Asia/Jerusalem')
        #
        # # Get the current date and replace the time with 23:04:26
        # specific_time = datetime.now().astimezone(timezone).replace(hour=23, minute=4, second=26)
        #
        # # Format it as a string
        # fetch_time = specific_time.strftime('%d-%m-%Y %H:%M:%S')

        print(f"**API day & time: {fetch_time}**")


        return merged_df, fetch_time
    else:
        return None, None  # Handle the case where the API request fails


def calculate_parking_cost(user):
    parking_lots = ParkingLot.objects.all().values()
    parking_lots_df = pd.DataFrame(list(parking_lots))

    results = []

    # Get current day and time
    now = datetime.now()
    current_day = now.strftime('%A').lower()
    current_time = now.strftime('%H:%M')

    print(f"Current day: {current_day.capitalize()}, Current time: {current_time}")
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

        if mapped_day == 'friday':
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
            print(f"Skipping parking lots due to missing coordinates.")
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
    # print("Final costs dataframe:")
    # print(results_df)
    return results_df


def address_to_coordinates(address):
    # Geocoding an address
    geocode_result = gmaps.geocode(address)
    # Extracting latitude and longitude
    if geocode_result and 'geometry' in geocode_result[0] and 'location' in geocode_result[0]['geometry']:
        location = geocode_result[0]['geometry']['location']
        latitude = location['lat']
        longitude = location['lng']
        return latitude, longitude
    else:
        return None


def parse_duration(duration_str):
    """Convert duration string to total minutes."""
    try:
        time_parts = duration_str.split()
        total_minutes = 0
        for i in range(0, len(time_parts), 2):
            if 'hour' in time_parts[i+1]:
                total_minutes += int(time_parts[i]) * 60
            elif 'min' in time_parts[i+1]:
                total_minutes += int(time_parts[i])
        return total_minutes
    except Exception as e:
        print(f"Error parsing duration: {e}")
        return 0


def parse_distance(distance_str):
    """Extract numeric part from distance string and convert to integer (assuming distance is in meters)."""
    try:
        # Assuming distance_str is like "1.2 km" or "500 m"
        if 'km' in distance_str:
            return int(float(distance_str.split()[0]) * 1000)  # Convert km to meters
        elif 'm' in distance_str:
            return int(distance_str.split()[0])  # Already in meters
    except Exception as e:
        print(f"Error parsing distance: {e}")
        return 0


def sort_results(parking_lot_list, preferences, parking_duration):
    if preferences == "walk-less":
        parking_lot_list.sort(key=lambda x: int(x['walking_time']))
    elif preferences == "pay-less":
        if parking_duration == "short-term":
            parking_lot_list.sort(key=lambda x: x['cost_2_hours'])
        else:
            parking_lot_list.sort(key=lambda x: x['cost_12_hours'])
    return parking_lot_list


def recommend_parking_lots(parking_lot_list, preferences, parking_duration):
    for lot in parking_lot_list:
        walking_time = int(lot['walking_time'])
        if parking_duration == "short-term":
            cost = lot['cost_2_hours']
        else:
            cost = lot['cost_12_hours']

        if preferences == "Walk Less":
            lot['score'] = 0.7 * walking_time + 0.3 * cost
        elif preferences == "Pay Less":
            lot['score'] = 0.7 * cost + 0.3 * walking_time

    parking_lot_list.sort(key=lambda x: x['score'])
    top_parking_lots = parking_lot_list[:3]  # Get the top 3 parking lots
    # return parking_lot_list
    return top_parking_lots


@login_required
def handle_parking_calculations(request):
    start_time = time.time()
    max_retries = 3  # Maximum number of retry attempts
    retries = 0  # Initialize retry counter

    while retries < max_retries:
        try:
            if request.method == 'POST':
                # Get user-entered destination from form
                destination = request.POST['destination']
                parking_duration = request.POST['parking_duration']
                preferences = request.POST['preferences']
                print(f"Destination: {destination}, Parking Duration: {parking_duration}, Preferences: {preferences}")

                # Geocode the destination address
                address_coordinates = address_to_coordinates(destination)

                if not address_coordinates:
                    raise Exception("Failed to geocode the destination address")

                # Fetch parking lot data with coordinates
                parking_lots_df, fetch_time = get_parking_lot_data_with_coordinates(request)
                if parking_lots_df is None:
                    raise Exception("Failed to fetch parking lot data.")

                # Fetch parking costs
                user = UserSetting.objects.get(username=request.session["username"])
                parking_costs_df = calculate_parking_cost(user)

                # Detecting Cold-Start: Check if the user has any parking ratings
                user_rating_count = UserParkingRating.objects.filter(user=user).count()

                if user_rating_count == 0:
                    # Cold-start detected, skip ALS and use only existing logic
                    print("Cold-start detected for user:", user.username)
                    als_recommendations = []  # No ALS recommendations in cold-start
                else:
                    # Non cold-start: use ALS-based recommendations
                    interaction_matrix = prepare_interaction_matrix()
                    if interaction_matrix.empty:
                        raise Exception("No interaction data available for ALS model.")

                    als_model = train_als_model(interaction_matrix)
                    als_recommendations = predict_parking_lots(user.user_id, als_model, interaction_matrix)
                    if not als_recommendations:
                        raise Exception("No ALS recommendations available.")

                # Initialize list to store parking lots data
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
                                time.sleep(2)  # Wait before retrying

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

                # Combine ALS recommendations with existing logic
                if als_recommendations:
                    print("ALS recommendations applied")
                    als_recommendation_codes = [lot.code for lot in als_recommendations]
                    unsorted_results = [result for result in unsorted_results if result['parking_lot_code'] in als_recommendation_codes]

                # Sort the results list based on user preferences
                sorted_results = sort_results(unsorted_results, preferences, parking_duration)

                # Recommend the best parking lots considering both walking time and cost
                recommended_results = recommend_parking_lots(sorted_results, preferences, parking_duration)

                # Convert the datetime string to the format required by DateTimeField
                search_datetime_str = datetime.now().astimezone(pytz.timezone('Asia/Jerusalem')).strftime('%d-%m-%Y %H:%M')
                search_datetime = datetime.strptime(search_datetime_str, '%d-%m-%Y %H:%M')

                # Save the parking history
                parking_history = ParkingHistory.objects.create(
                    user=user,
                    search_datetime=search_datetime,
                    search_address=destination,
                    preference=preferences,
                    parking_duration=parking_duration,
                    recommendation_1=ParkingLot.objects.get(code=recommended_results[0]['parking_lot_code']) if len(recommended_results) > 0 else None,
                    recommendation_2=ParkingLot.objects.get(code=recommended_results[1]['parking_lot_code']) if len(recommended_results) > 1 else None,
                    recommendation_3=ParkingLot.objects.get(code=recommended_results[2]['parking_lot_code']) if len(recommended_results) > 2 else None,
                )

                # Get the current date and time right before rendering the template
                current_datetime = datetime.now().astimezone(pytz.timezone('Asia/Jerusalem')).strftime('%A %H:%M')

                # Measure the execution time
                end_time = time.time()
                print(f"Execution Time for handle_parking_calculations: {end_time - start_time} seconds")

                return render(request, 'recommendation_results.html', {
                    'results': recommended_results,
                    'current_datetime': current_datetime,
                    'fetch_time': fetch_time,
                    'destination': destination,
                    'parking_duration': parking_duration,
                    'username': user.username,  # Updated to use user object from UserSetting
                    'parking_history_id': parking_history.id  # Pass the ParkingHistory ID to the template
                })

        except Exception as e:
            print(f"An error occurred: {e}")
            retries += 1
            if retries >= max_retries:
                # If max retries are reached, display an error message to the user
                return redirect(f'{reverse("destination", kwargs={"username": request.session["username"]})}?error=True')

        time.sleep(2)  # Retry after a 2-second delay

    return render(request, 'destination.html')


""" ALS """

def prepare_interaction_matrix():
    # Query the UserParkingRating model to get user-parking ratings
    interactions = UserParkingRating.objects.all().values('user_id', 'parking_preference_id', 'rating')

    # Convert to a pandas DataFrame
    df = pd.DataFrame(list(interactions))

    # Debugging: Print the head of the DataFrame to see some sample data
    print("Interactions DataFrame head:")
    print(df.head())

    # Create an interaction matrix with users as rows and parking preferences as columns
    interaction_matrix = df.pivot_table(index='user_id', columns='parking_preference_id', values='rating', fill_value=0)

    # Debugging: Print the head of the interaction matrix
    print("Interaction Matrix head:")
    print(interaction_matrix.head())

    return interaction_matrix

import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"

def train_als_model(interaction_matrix):
    # Convert the matrix to a sparse format expected by the implicit library
    sparse_matrix = csr_matrix(interaction_matrix.values)

    # Initialize the ALS model
    model = implicit.als.AlternatingLeastSquares(factors=50, regularization=0.01, iterations=20)

    # Train the model on the interaction matrix
    model.fit(sparse_matrix)

    return model

from scipy.sparse import csr_matrix

def predict_parking_lots(user_id, model, interaction_matrix):
    # Ensure user_id is of the correct type
    user_id = interaction_matrix.index.dtype.type(user_id)

    if user_id in interaction_matrix.index:
        user_idx = interaction_matrix.index.get_loc(user_id)
    else:
        print(f"User ID {user_id} not found in interaction matrix indices.")
        return []  # Handle the case as appropriate

    # Extract the row corresponding to the user and convert it to CSR format
    csr_user_items = csr_matrix(interaction_matrix.values[user_idx])

    # Recommend parking lots using the ALS model
    recommendations = model.recommend(user_idx, csr_user_items, N=10)

    # Get the corresponding parking preference IDs from the recommendations
    parking_preference_ids = [interaction_matrix.columns[i] for i in recommendations[0]]

    # Retrieve the ParkingLots based on these parking preferences
    parking_lots = ParkingLot.objects.filter(parkingpreference__id__in=parking_preference_ids).distinct()

    return parking_lots

""" ALS """

def update_user_parking_rating(user, parking_history):
    # List of recommendations and corresponding preferences
    recommendations = [
        (parking_history.recommendation_1, parking_history.preference),
        (parking_history.recommendation_2, parking_history.preference),
        (parking_history.recommendation_3, parking_history.preference)
    ]

    for recommendation, preference in recommendations:
        if recommendation:
            # Get or create the parking preference
            parking_preference, created = ParkingPreference.objects.get_or_create(
                parking_lot=recommendation,
                preference=preference
            )

            # Calculate the total number of times this parking lot was recommended to the user
            total_recommendations = ParkingHistory.objects.filter(
                user=user
            ).filter(
                recommendation_1=recommendation
            ).count() + ParkingHistory.objects.filter(
                user=user
            ).filter(
                recommendation_2=recommendation
            ).count() + ParkingHistory.objects.filter(
                user=user
            ).filter(
                recommendation_3=recommendation
            ).count()

            # Calculate the number of times this parking lot was chosen as the final choice
            # Note: We do not add 1 here as we did previously since matching_preferences already includes all relevant histories.
            matching_preferences = ParkingHistory.objects.filter(
                user=user,
                final_choice=recommendation
            ).count()

            # Debugging: Print the values used in the calculation
            print(f"Recommendation: {recommendation.name}, Total Recommendations: {total_recommendations}, Matching Preferences: {matching_preferences}")

            # Calculate the percentage of times the recommendation was selected
            percentage = (matching_preferences / total_recommendations) * 100 if total_recommendations > 0 else 0

            # Debugging: Print the calculated percentage
            print(f"Calculated Percentage for {recommendation.name}: {percentage}%")

            # Determine the rating based on the percentage
            if percentage <= 20:
                rating = 1
            elif 21 <= percentage <= 40:
                rating = 2
            elif 41 <= percentage <= 60:
                rating = 3
            elif 61 <= percentage <= 80:
                rating = 4
            else:
                rating = 5

            # Debugging: Print the final rating
            print(f"Final Rating for {recommendation.name}: {rating}")

            # Update or create the UserParkingRating
            UserParkingRating.objects.update_or_create(
                user=user,
                parking_preference=parking_preference,
                defaults={'rating': rating}
            )

    print(f"Updated parking ratings for user {user.username}")


# Updated save_user_choice function
@login_required
def save_user_choice(request):

    if request.method == 'POST':
        parking_lot_name = request.POST.get('parking_lot_name')
        parking_lot_code = request.POST.get('parking_lot_code')
        parking_history_id = request.POST.get('parking_history_id')
        # user = request.POST.get('username')
        user = request.user

        try:
            parking_history = ParkingHistory.objects.get(id=parking_history_id)

            if parking_lot_name == 'אחר':
                parking_history.final_choice = None
            elif parking_history.recommendation_1 and parking_lot_name == parking_history.recommendation_1.name:
                parking_history.final_choice = parking_history.recommendation_1
            elif parking_history.recommendation_2 and parking_lot_name == parking_history.recommendation_2.name:
                parking_history.final_choice = parking_history.recommendation_2
            elif parking_history.recommendation_3 and parking_lot_name == parking_history.recommendation_3.name:
                parking_history.final_choice = parking_history.recommendation_3
            else:
                parking_history.final_choice = None

            parking_history.save()

            # Update UserParkingRating based on the user's choice
            update_user_parking_rating(parking_history.user, parking_history)
            time.sleep(3.5)  # Wait before retrying
            return redirect('destination', username=parking_history.user)
        except ParkingHistory.DoesNotExist:
            return JsonResponse({'error': 'Parking history not found.'}, status=404)
        except ParkingLot.DoesNotExist:
            return JsonResponse({'error': 'Parking lot not found.'}, status=404)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


