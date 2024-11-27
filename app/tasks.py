from django.core.mail import send_mail
from celery import shared_task
from django.db.models import Count
from django.utils import timezone

import WeatherReminder.settings
from .models import Subscription, WeatherData, City
from datetime import timedelta

from .utils import get_weather_data_from_api


@shared_task()
def update_weather_data_for_city(weather_id):
    try:
        weather = WeatherData.objects.get(id=weather_id)
        new_data = get_weather_data_from_api(
            latitude=weather.city.latitude, longitude=weather.city.longitude
        )

        if "error" in new_data:
            print(
                f"Weather data for city {weather.city.name} hasn't been updated. Error: {new_data['error']}"
            )
        else:
            weather.update_data(new_data)
            weather.save()
            print(f"Weather data for city {weather.city.name} updated")

    except WeatherData.DoesNotExist:
        print(f"Weather data with id {weather_id} does not exist")


@shared_task()
def update_weather_data_async():
    update_interval = timezone.now() - timedelta(minutes=55)
    outdated_weather_data = WeatherData.objects.filter(updated_at__lte=update_interval)

    for weather in outdated_weather_data:
        update_weather_data_for_city.delay(weather.id)

    cities_without_data = City.objects.annotate(num_weather_data=Count("data")).filter(
        num_weather_data=0
    )

    for city in cities_without_data:
        try:
            WeatherData.objects.create(
                city=city,
                weather_data=get_weather_data_from_api(
                    latitude=city.latitude, longitude=city.longitude
                ),
            )
            print(f"Weather data for city {city.name} created")
        except Exception as e:
            print(f"Weather data for city {city.name} does not created, error: {e}")


@shared_task()
def send_weather_email():
    subscriptions = Subscription.objects.filter(next_message__hour=timezone.now().hour)
    for subscription in subscriptions:
        try:
            api_email = WeatherReminder.settings.EMAIL_HOST_USER
            weather_data = subscription.get_weather_data()
            message = f"Weather forecast for {subscription.city.name}:\n"

            if subscription.temperature:
                message += f"Temperature: {weather_data['main']['temp']}°C\n"
            if subscription.feels_like:
                message += f"Feels like: {weather_data['main']['feels_like']}°C\n"
            if subscription.humidity:
                message += f"Humidity: {weather_data['main']['humidity']}%\n"
            if subscription.pressure:
                message += f"Pressure: {weather_data['main']['pressure']} hPa\n"
            if subscription.wind:
                message += f"Wind: {weather_data['wind']['speed']} m/s at {weather_data['wind']['deg']}°\n"
            if subscription.wind_speed and "gust" in weather_data["wind"]:
                message += f"Wind gusts: {weather_data['wind']['gust']} m/s\n"
            if subscription.cloudiness:
                message += f"Cloudiness: {weather_data['clouds']['all']}%\n"
            if subscription.precipitation:
                description = weather_data["weather"][0]["description"]
                message += f"Precipitation: {description}\n"

            send_mail(
                subject=f"{subscription.user.username}, here is your {subscription.city} weather forecast for closest hour",
                message=f"{message}",
                from_email=f"{api_email}",
                recipient_list=[f"{subscription.user.email}"],
            )
            print(
                f"Weather to {subscription.user.username}, {subscription.city} was sent successfully"
            )
        except Exception as e:
            print(
                f"Error sending weather email to subscription {subscription.user.username}, {subscription.city}: {str(e)}"
            )

        subscription.next_message += timedelta(hours=subscription.period)
        subscription.save()
