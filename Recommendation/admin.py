from django.contrib import admin
from .models import UserSetting, ParkingLot, ParkingHistory, ParkingPreference, UserParkingRating

# Admin class for UserSetting
class UserSettingAdmin(admin.ModelAdmin):
    fields = ['user_id', 'name', 'username', 'password', 'email', 'default_preferences', 'default_address', 'parking_area', 'birth_year', 'gender']
    readonly_fields = ['user_id']

# Admin class for ParkingLot with display settings
@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'address')

# Admin class for ParkingHistory with custom user_id display and sorting
class ParkingHistoryAdmin(admin.ModelAdmin):
    list_display = ('user_id_display', 'search_datetime', 'search_address', 'preference', 'parking_duration',
                    'recommendation_1_display', 'recommendation_2_display', 'recommendation_3_display', 'final_choice_display')
    ordering = ['user__user_id']  # Enable sorting by user ID

    def user_id_display(self, obj):
        return obj.user.user_id
    user_id_display.short_description = 'User ID'
    user_id_display.admin_order_field = 'user__user_id'  # Enable sorting by User ID

    def recommendation_1_display(self, obj):
        return obj.recommendation_1.code if obj.recommendation_1 else None
    recommendation_1_display.short_description = 'Recommendation 1'

    def recommendation_2_display(self, obj):
        return obj.recommendation_2.code if obj.recommendation_2 else None
    recommendation_2_display.short_description = 'Recommendation 2'

    def recommendation_3_display(self, obj):
        return obj.recommendation_3.code if obj.recommendation_3 else None
    recommendation_3_display.short_description = 'Recommendation 3'

    def final_choice_display(self, obj):
        return obj.final_choice.code if obj.final_choice else None
    final_choice_display.short_description = 'Final Choice'

# Admin class for UserParkingRating with custom user_id display and sorting
class UserParkingRatingAdmin(admin.ModelAdmin):
    list_display = ('user_id_display', 'parking_preference_display', 'rating')
    list_filter = ['rating']  # Enable filtering by rating
    ordering = ['user__user_id']  # Enable sorting by user ID

    def user_id_display(self, obj):
        return obj.user.user_id
    user_id_display.short_description = 'User ID'
    user_id_display.admin_order_field = 'user__user_id'  # Enable sorting by User ID

    def parking_preference_display(self, obj):
        return str(obj.parking_preference)
    parking_preference_display.short_description = 'Parking Preference'


# Admin class for UserSetting with table-like display
class UserSettingAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'username', 'email', 'get_default_preferences', 'default_address', 'parking_area', 'birth_year', 'get_gender')
    readonly_fields = ['user_id']
    ordering = ['user_id']  # Enable sorting by user_id

    # Custom method to display human-readable 'default_preferences'
    def get_default_preferences(self, obj):
        return obj.get_default_preferences_display()
    get_default_preferences.short_description = 'Default Preferences'

    # Custom method to display human-readable 'gender'
    def get_gender(self, obj):
        return obj.get_gender_display()
    get_gender.short_description = 'Gender'


# Register all models with the admin site
admin.site.register(UserSetting, UserSettingAdmin)
admin.site.register(ParkingHistory, ParkingHistoryAdmin)
admin.site.register(ParkingPreference)
admin.site.register(UserParkingRating, UserParkingRatingAdmin)
