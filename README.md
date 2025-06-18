# Final Project – Parking Recommendation System 🚗🅿️

This Django-based project is a smart **Parking Recommendation System** that suggests optimal parking lots based on user preferences, walking distance, and cost.

## 🔧 Features
- User registration and login
- Personalized parking lot recommendations
- Integration with **Google Distance Matrix API** to calculate walking times
- User preference history tracking
- Admin interface for managing data
  

## 🔑 Important Note on Google API
To use the recommendation system, you must update the API key in views.py:
gmaps = Client(key='YOUR_GOOGLE_API_KEY_HERE')
Make sure the API key has access to the Google Distance Matrix API.

## 📁 Project Structure
RecommendationSystem/ – Main Django project folder
Recommendation/ – App logic: views, models, templates, URLs
static/ – Static files (CSS, JS)
templates/ – HTML templates

## 🙋‍♀️ Author
Developed by Noya Litav as part of her final project in the Information Systems & Business Analytics track.
