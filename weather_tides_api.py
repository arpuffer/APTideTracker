import datetime as dt
import json
import os
import requests
import time

import noaa_coops

configpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')

with open(configpath, 'r') as configfile:
    config = json.load(configfile)
# Optional, displayed on top left
LOCATION = config.get('location')

# NOAA Station Code for tide data
StationID = config.get('noaa_station_id')

# For weather data
# Create Account on openweathermap.com and get API key
API_KEY = config.get('openweather_api_key')
# Get LATITUDE and LONGITUDE of location
LATITUDE = config.get('latitude')
LONGITUDE = config.get('longitude')
UNITS = config.get('units')  # 'imperial' for Fahrenheit, 'metric' for Celsius

# Create URL for API call
OPENWEATHER_CURRENT_CONDITIONS_URL = 'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={units}&appid={api_key}'
OPENWEATHER_FORECAST_URL =           'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}'

def request_with_retries(url, retries=3, backoff_factor=0.3):
    """Make a GET request with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(backoff_factor * (2 ** attempt))
            else:
                raise e

def current_weather():
    """Fetch current weather data from OpenWeatherMap API."""
    url = OPENWEATHER_CURRENT_CONDITIONS_URL.format(
        lat=LATITUDE,
        lon=LONGITUDE,
        units=UNITS,
        api_key=API_KEY
    )
    response = request_with_retries(url)
    return response.json()

def forecast_weather(days=2):
    """Fetch weather forecast data from OpenWeatherMap API."""
    url = OPENWEATHER_FORECAST_URL.format(
        lat=LATITUDE,
        lon=LONGITUDE,
        cnt=days,
        api_key=API_KEY
    )
    response = request_with_retries(url)
    return response.json()

# last 24 hour data, add argument for start/end_date
def water_level_24h(StationID):
    # Create Station Object
    stationdata = noaa_coops.Station(StationID)

    # Get today date string
    today = dt.datetime.now()
    todaystr = today.strftime("%Y%m%d %H:%M")
    # Get yesterday date string
    yesterday = today - dt.timedelta(days=1)
    yesterdaystr = yesterday.strftime("%Y%m%d %H:%M")

    # Get water level data
    WaterLevel = stationdata.get_data(
        begin_date=yesterdaystr,
        end_date=todaystr,
        product="water_level",
        datum="MLLW",
        time_zone="lst_ldt")

    return WaterLevel

def tides(StationID):
    # Create Station Object
    stationdata = noaa_coops.Station(StationID)

    # Get today date string
    today = dt.datetime.now()
    todaystr = today.strftime("%Y%m%d")
    # Get yesterday date string
    tomorrow = today + dt.timedelta(days=1)
    tomorrowstr = tomorrow.strftime("%Y%m%d")

    # Get Hi and Lo Tide info
    TideHiLo = stationdata.get_data(
        begin_date=todaystr,
        end_date=tomorrowstr,
        product="predictions",
        datum="MLLW",
        interval="hilo",
        time_zone="lst_ldt")

    return TideHiLo

def main():
    # Running this file directly will print out current weather and tide data
    weather = current_weather()
    print("Current Weather:")
    print(weather)

    forecast = forecast_weather()
    print("\nForecast:")
    print(forecast)

    water_level = water_level_24h(StationID)
    print("\nWater Level (Last 24 hours):")
    print(water_level)
    
    tide = tides(StationID)
    print("\nTide Data:")
    print(tide)

if __name__ == "__main__":
    main()
