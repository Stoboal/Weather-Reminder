from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib import auth
from django.shortcuts import redirect, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView

from .utils import get_weather_data_from_api
from .models import Subscription, CustomUser, WeatherData
from .forms import (
    UserRegistrationForm,
    UserAuthenticationForm,
    CreateSubscriptionForm,
    ChangePeriodForm,
)


def index_page_view(request):
    user = request.user
    if user.is_authenticated:
        return redirect(reverse("main", kwargs={"username": user.username}))
    else:
        return redirect(reverse("login"))


class MainPageView(ListView):
    model = Subscription
    template_name = "weather_reminder/main.html"
    context_object_name = "subscriptions"

    def get_user(self):
        username = self.kwargs.get("username")
        return get_object_or_404(CustomUser, username=username)

    def get_queryset(self):
        self.user = self.get_user()
        return Subscription.objects.filter(user=self.user).order_by("city")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CreateSubscriptionForm()
        context["user"] = self.user
        return context

    def post(self, request, *args, **kwargs):
        self.user = self.get_user()

        if "create_subscription" in request.POST:
            form = CreateSubscriptionForm(request.POST)
            if self.user.check_subscriptions_amount():
                if form.is_valid():
                    with transaction.atomic():
                        subscription = form.save(commit=False)
                        subscription.user = self.user
                        subscription.save()
                        return redirect(
                            reverse("main", kwargs={"username": self.user.username})
                        )

        elif "change_period" in request.POST:
            subscription_id = request.POST.get("subscription_id")
            subscription = get_object_or_404(
                Subscription, id=subscription_id, user=self.user
            )
            change_period_form = ChangePeriodForm(request.POST, instance=subscription)
            if change_period_form.is_valid():
                change_period_form.save()
                return redirect(
                    reverse("main", kwargs={"username": self.user.username})
                )

        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_response(context)


def login_view(request):
    if request.method == "POST":
        form = UserAuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = auth.authenticate(request, username=username, password=password)
            if user:
                auth.login(request, user)
                return HttpResponseRedirect(reverse("index"), status=302)
            else:
                return render(request, "weather_reminder/login.html", {"form": form})
    else:
        form = UserAuthenticationForm()
    return render(request, "weather_reminder/login.html", {"form": form})


def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("login"))
    else:
        form = UserRegistrationForm()
    return render(request, "weather_reminder/register.html", {"form": form}, status=401)


@login_required
def logout_view(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse("login"))


@login_required
def change_attr_view(request, subscription_id, attr):
    subscription = get_object_or_404(Subscription, id=subscription_id)
    user = subscription.user
    if user.id == subscription.user.id:
        if hasattr(subscription, attr):
            current_value = getattr(subscription, attr)
            setattr(subscription, attr, not current_value)
            subscription.save()
            return redirect(
                reverse("main", kwargs={"username": user.username}), status_code=200
            )
        else:
            return redirect(reverse("index"), status_code=401)
    else:
        JsonResponse({"message": "Cheater detected"}, status=401)


@login_required
def delete_subscription_view(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id)
    user = request.user

    if user.id == subscription.user.id:
        subscription.delete()
        return redirect(
            reverse("main", kwargs={"username": user.username}), status_code=200
        )
    else:
        JsonResponse({"message": "Cheater detected"}, status=401)


def get_weather_view(request, subscription_id):
    try:
        subscription = Subscription.objects.get(id=subscription_id)
    except Subscription.DoesNotExist:
        return JsonResponse({"message": "Subscription not found"}, status=404)

    latitude = subscription.city.latitude
    longitude = subscription.city.longitude
    city = subscription.city
    weather_data_object, created = WeatherData.objects.get_or_create(city=city)
    data = weather_data_object.weather_data

    if created:
        weather_data_object.update_data(
            get_weather_data_from_api(latitude=latitude, longitude=longitude)
        )
        data = weather_data_object.weather_data
        if "error" in data:
            return JsonResponse(
                {"message": f"Error fetching weather data: {data['error']}"}, status=500
            )
        return JsonResponse(data, status=200)

    # The reason for the next restriction is payments for weather data service
    if timezone.now() - weather_data_object.updated_at > timedelta(hours=1):
        weather_data_object.update_data(
            get_weather_data_from_api(latitude=latitude, longitude=longitude)
        )

    return JsonResponse(data, status=200)
