from django.db import models

class UserSetting(models.Model):
    PREFERENCES_CHOICES = [
        ('pay-less', 'Pay Less'),
        ('walk-less', 'Walk Less'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user_id = models.AutoField(primary_key=True, default=None)
    name = models.CharField(max_length=32)
    username = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    default_preferences = models.CharField(max_length=150, choices=PREFERENCES_CHOICES, default=None)
    default_address = models.CharField(max_length=150, default=None)
    parking_area = models.CharField(max_length=2, blank=True)
    birth_year = models.IntegerField(default=None)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='F')

    def __str__(self):
        return self.username


class ParkingLot(models.Model):
    code = models.CharField(primary_key=True, max_length=3)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    gps_latitude = models.FloatField(null=True, blank=True)
    gps_longitude = models.FloatField(null=True, blank=True)
    day_hour_weekday = models.CharField(max_length=255, null=True, blank=True)
    daily_rate_day_weekday = models.FloatField(null=True, blank=True)
    hourly_rate_day_weekday = models.FloatField(null=True, blank=True)
    daily_night_rate_weekday = models.FloatField(null=True, blank=True)
    hourly_night_rate_weekday = models.FloatField(null=True, blank=True)
    day_hour_friday = models.CharField(max_length=255, null=True, blank=True)
    daily_rate_day_friday = models.FloatField(null=True, blank=True)
    hourly_rate_day_friday = models.FloatField(null=True, blank=True)
    daily_night_rate_friday = models.FloatField(null=True, blank=True)
    hourly_night_rate_friday = models.FloatField(null=True, blank=True)
    day_hour_saturday = models.CharField(max_length=255, null=True, blank=True)
    daily_rate_day_saturday = models.FloatField(null=True, blank=True)
    hourly_rate_day_saturday = models.FloatField(null=True, blank=True)
    daily_night_rate_saturday = models.FloatField(null=True, blank=True)
    hourly_night_rate_saturday = models.FloatField(null=True, blank=True)
    resident_discount = models.FloatField(null=True, blank=True)
    close_to_home = models.BooleanField(default=False)
    parking_area = models.CharField(null=True, max_length=10)
    notes = models.TextField(null=True, blank=True)


class Distance(models.Model):
    destination = models.CharField(max_length=255)
    distance = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.destination} - Distance: {self.distance}, Duration: {self.duration}"


class ParkingHistory(models.Model):
    user = models.ForeignKey(UserSetting, on_delete=models.CASCADE)  # Reference UserSetting instead of User
    search_datetime = models.DateTimeField()  # Save current datetime manually
    search_address = models.CharField(max_length=255)  # The address searched by the user
    preference = models.CharField(max_length=50, choices=[('Pay Less', 'Pay Less'), ('Walk Less', 'Walk Less')])  # User's preference
    parking_duration = models.CharField(max_length=50)  # Duration of parking
    recommendation_1 = models.ForeignKey(ParkingLot, related_name='recommendation_1', on_delete=models.SET_NULL, null=True)
    recommendation_2 = models.ForeignKey(ParkingLot, related_name='recommendation_2', on_delete=models.SET_NULL, null=True, blank=True)
    recommendation_3 = models.ForeignKey(ParkingLot, related_name='recommendation_3', on_delete=models.SET_NULL, null=True, blank=True)
    final_choice = models.ForeignKey(ParkingLot, related_name='final_choice', on_delete=models.SET_NULL, null=True, blank=True)  # שינוי לשדה ForeignKey

    def __str__(self):
        return f'User ID: {self.user.user_id}'


class ParkingPreference(models.Model):
    parking_lot = models.ForeignKey('ParkingLot', on_delete=models.CASCADE)  # Reference to ParkingLot
    preference = models.CharField(max_length=50, choices=[('pay-less', 'Pay Less'), ('walk-less', 'Walk Less')])  # Preference
    parking_preference_id = models.CharField(max_length=255, unique=True)  # Unique ID for ParkingLot + Preference

    def save(self, *args, **kwargs):
        if not self.parking_preference_id:
            self.parking_preference_id = f'{self.parking_lot.code}_{self.preference}'
        super(ParkingPreference, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.parking_lot.code} - {self.preference}'


class UserParkingRating(models.Model):
    user = models.ForeignKey(UserSetting, on_delete=models.CASCADE)  # Reference to UserSetting
    parking_preference = models.ForeignKey(ParkingPreference, on_delete=models.CASCADE)  # Reference to ParkingPreference
    rating = models.IntegerField()  # Rating 1-5

    def __str__(self):
        return f'{self.user.user_id} - {self.parking_preference} - {self.rating}'


