from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import CustomUser, Subscription, City


class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Input your username"}),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "Provide your e-mail address"}),
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": "Provide your password"}),
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat your password"}),
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]


class UserAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Input your username"}),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": "Provide your password"}),
    )

    class Meta:
        model = CustomUser
        fields = ["username", "password"]


class CreateSubscriptionForm(forms.ModelForm):
    city = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Enter city name"})
    )

    class Meta:
        model = Subscription
        fields = ["city", "period", "humidity", "wind", "wind_speed"]
        widgets = {
            "period": forms.NumberInput(attrs={"placeholder": "6"}),
            "humidity": forms.CheckboxInput(),
            "wind": forms.CheckboxInput(),
            "wind_speed": forms.CheckboxInput(),
        }

    def clean_city(self):
        city_name = self.cleaned_data["city"]
        city, created = City.objects.get_or_create(name=city_name)
        if created:
            city.set_coordinates()
            city.save()
        return city


class ChangePeriodForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["period"]
        widgets = {"period": forms.NumberInput(attrs={"min": 1})}
