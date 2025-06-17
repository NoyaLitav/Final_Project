import time
import requests

def check_api_availability(api_url, num_requests=10):
    successful_requests = 0
    total_time = 0

    for i in range(num_requests):
        try:
            start_time = time.time()
            response = requests.get(api_url)  # קריאה ל-API החיצוני
            end_time = time.time()

            # בדיקת הצלחת הקריאה
            if response.status_code == 200:
                successful_requests += 1
                total_time += (end_time - start_time)
                print(f"Request {i+1}: Success, Time: {end_time - start_time:.2f} seconds")
            else:
                print(f"Request {i+1}: Failed, Status Code: {response.status_code}")

        except Exception as e:
            print(f"Request {i+1}: Exception occurred - {e}")

    # חישוב אחוזי הצלחה וזמן ממוצע
    success_rate = (successful_requests / num_requests) * 100
    average_time = total_time / successful_requests if successful_requests > 0 else float('inf')

    print(f"\nAPI Availability Results:")
    print(f"Total Requests: {num_requests}")
    print(f"Successful Requests: {successful_requests}")
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Average Response Time: {average_time:.2f} seconds")

    return success_rate, average_time

# דוגמה לקריאה לפונקציה עם כתובת URL של API
api_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=PLACE_ORIGINS_HERE&destinations=PLACE_DESTINATIONS_HERE&key=YOUR_API_KEY"
check_api_availability(api_url, num_requests=10)
