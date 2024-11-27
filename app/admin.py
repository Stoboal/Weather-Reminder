from django.contrib import admin
from .models import CustomUser, Subscription, WeatherData


class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "active_subscriptions", "email", "is_active")

    def active_subscriptions(self, obj):
        return Subscription.objects.filter(user=obj).count()

    active_subscriptions.short_description = "Subscriptions"


admin.site.register(CustomUser, UserAdmin)


class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "city_name", "period", "next_message")

    def city_name(self, obj):
        return obj.city.name

    city_name.short_description = "City"

    def next_message(self, obj):
        return obj.next_message

    next_message.short_description = "Next message"


admin.site.register(Subscription, UserSubscriptionAdmin)


class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ("city_name", "id", "updated_at", "active_users", "has_weather_data")

    def has_weather_data(self, obj):
        return bool(obj.weather_data)

    has_weather_data.boolean = True
    has_weather_data.short_description = "Weather Data"

    def active_users(self, obj):
        return Subscription.objects.filter(city=obj.city).count()

    active_users.short_description = "Active users"

    def city_name(self, obj):
        return obj.city.name

    city_name.short_description = "City"


admin.site.register(WeatherData, WeatherDataAdmin)
