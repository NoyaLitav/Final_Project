"""
URL configuration for RecommendationSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Recommendation import views

# test git

urlpatterns = [
    path("admin/", admin.site.urls),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("connected/", views.signup, name="connected"),
    path("logout/", views.logout, name="logout"),
    path("homepage/", views.homepage, name="homepage"),
    path('destination/<str:username>/', views.destination, name='destination'),
    path('parking_lots/', views.get_parking_lot_data_with_coordinates, name='available_parking_lots'),
    path("", views.homepage, name="landing_page"),  # This makes the homepage the landing page
    path("get_default_address/", views.get_default_address, name="get_default_address"),
    path("get_default_preferences/", views.get_default_preferences, name="get_default_preferences"),
    path("recommendation_results/", views.handle_parking_calculations, name="recommendation_results"),
    path('save_user_choice/', views.save_user_choice, name='save_user_choice'),

]
