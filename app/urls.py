from django.urls import path
from .views import *

urlpatterns = [
    path("", index_page_view, name="index"),
    path("user/<str:username>", MainPageView.as_view(), name="main"),
    path(
        "subscription/<uuid:subscription_id>/condition",
        get_weather_view,
        name="get_weather",
    ),
    path(
        "subscription/<uuid:subscription_id>/change_attr/<str:attr>",
        change_attr_view,
        name="change_attr",
    ),
    path(
        "subscription/<uuid:subscription_id>/delete",
        delete_subscription_view,
        name="delete_subscription",
    ),
    path("login", login_view, name="login"),
    path("register", register_view, name="register"),
    path("logout", logout_view, name="logout"),
]
