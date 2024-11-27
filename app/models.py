from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser

import uuid

from django.utils import timezone
from geopy.geocoders import Nominatim


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"{self.username}"

    def check_subscriptions_amount(self):
        if self.subscriptions.count() >= 5:
            raise ValidationError("You can't add more than 5 subscriptions!")
        return True


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE, related_name="subscriptions")
    city = models.ForeignKey("City", on_delete=models.CASCADE, related_name="subscriptions")
    period = models.PositiveIntegerField(default=6, blank=False)
    next_message = models.DateTimeField(default=timezone.now, blank=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # User's choice:
    temperature = models.BooleanField(default=True)
    precipitation = models.BooleanField(default=True)
    cloudiness = models.BooleanField(default=True)
    humidity = models.BooleanField(default=False)
    wind = models.BooleanField(default=False)
    wind_speed = models.BooleanField(default=False)
    pressure = models.BooleanField(default=False)
    feels_like = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscription"
        unique_together = ("user", "city")
        indexes = [
            models.Index(fields=["user", "city"]),
        ]
        ordering = ["-city"]

    def __str__(self):
        return f"{self.user.username} - {self.city.name} - {self.next_message}"

    def save(self, *args, **kwargs):
        if self.next_message <= timezone.now():
            self.next_message = (
                timezone.now()
                + timedelta(hours=self.period)
                - timedelta(
                    minutes=timezone.now().minute,
                    seconds=timezone.now().second,
                    microseconds=timezone.now().microsecond,
                )
            )

        super(Subscription, self).save(*args, **kwargs)

    def get_weather_data(self):
        return self.city.data.first().weather_data


class City(models.Model):
    name = models.CharField(max_length=124)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    def set_coordinates(self):
        location = Nominatim(user_agent=settings.env('NOMINATUM_ACCOUNT_NAME')).geocode(self.name)
        self.latitude, self.longitude = location.latitude, location.longitude


class WeatherData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    city = models.ForeignKey("City", on_delete=models.CASCADE, related_name="data", null=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    weather_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.city.name} - {self.updated_at}"

    def update_data(self, data):
        self.weather_data = data
        self.updated_at = timezone.now()
        self.save()
