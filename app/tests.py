import json
from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Subscription, WeatherData, City

User = get_user_model()


class TestWeatherReminderViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="Password123")
        self.username = "testuser"
        self.password = "Password123"
        self.city = City.objects.create(name="Calgary")
        self.subscription = Subscription.objects.create(user=self.user, city=self.city)
        self.weather_data = WeatherData.objects.create(city=self.subscription.city, weather_data={"temp": 25})

        self.index_url = reverse("index")
        self.main_url = reverse("main", kwargs={"username": self.user.username})
        self.login_url = reverse("login")
        self.register_url = reverse("register")
        self.logout_url = reverse("logout")
        self.change_attr_url = reverse("change_attr",
                                       kwargs={"subscription_id": self.subscription.id, "attr": "is_active"})
        self.delete_subscription_url = reverse("delete_subscription", kwargs={"subscription_id": self.subscription.id})
        self.get_weather_url = reverse("get_weather", kwargs={"subscription_id": self.subscription.id})

    def test_index_page_view_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.index_url)
        self.assertRedirects(response, self.main_url)

    def test_index_page_view_unauthenticated(self, mock_provider_login_url):
        response = self.client.get(self.index_url)
        self.assertRedirects(response, self.login_url)
        mock_provider_login_url.assert_called_once()

    def test_main_page_view(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.main_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "weather_reminder/main.html")
        self.assertContains(response, "Calgary")

    def test_login_view_successful(self):
        response = self.client.post(self.login_url, {"username": self.username, "password": self.password})
        self.assertRedirects(response, self.index_url)

    def test_login_view_invalid_credentials(self):
        response = self.client.post(self.login_url, {"username": "wronguser", "password": "wrongpassword"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "weather_reminder/login.html")

    def test_register_view_successful(self):
        response = self.client.post(self.register_url, {
            "username": "Testuser",
            "password1": "Password_123",
            "password2": "Password_123"
        })
        self.assertRedirects(response, self.login_url)

    def test_logout_view(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)

    def test_change_attr_view(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.change_attr_url)
        self.subscription.refresh_from_db()
        self.assertRedirects(response, self.main_url)
        self.assertFalse(self.subscription.is_active)

    def test_delete_subscription_view(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.delete_subscription_url)
        self.assertRedirects(response, self.main_url)
        self.assertFalse(Subscription.objects.filter(id=self.subscription.id).exists())

    def test_get_weather_view_existing_data(self):
        response = self.client.get(self.get_weather_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["temp"], 25)

    def test_get_weather_view_update_data(self):
        self.weather_data.updated_at = timezone.now() - timedelta(hours=2)
        self.weather_data.save()

        with self.assertLogs("weather_reminder", level="INFO") as log:
            response = self.client.get(self.get_weather_url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("INFO:weather_reminder:Updating weather data", log.output[0])

