import json
import urllib.request
import environ

env = environ.Env()
environ.Env.read_env()
key = env("WEATHER_API_KEY")


def get_weather_data_from_api(latitude, longitude):
    weather_request = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={key}&units=metric"
    try:
        weather = urllib.request.urlopen(weather_request)
        data = json.loads(weather.read())
        if isinstance(data, dict):
            return data
    except Exception as e:
        return {"error": f"Error fetching weather data: {e}"}
