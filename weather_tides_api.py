import datetime as dt
import json
import os
import requests
import time

from pprint import pprint
import noaa_coops

configpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')

with open(configpath, 'r') as configfile:
    config = json.load(configfile)


NOAA_COOPS_STATION = config.get('noaa_station_id')

API_KEY = config.get('openweather_api_key')
# Get LATITUDE and LONGITUDE of location
LATITUDE = config.get('latitude')
LONGITUDE = config.get('longitude')
UNITS = config.get('units')  # 'imperial' for Fahrenheit, 'metric' for Celsius

# Create URL for API call
OPENWEATHER_ONECALL_URL = 'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units={units}&exclude=minutely,hourly&appid={api_key}'

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

def onecall():
    url = OPENWEATHER_ONECALL_URL.format(lat=LATITUDE, lon=LONGITUDE, units=UNITS, api_key=API_KEY)
    response = request_with_retries(url)
    return response.json()

def water_level_24h(NOAA_COOPS_STATION):
    stationdata = noaa_coops.Station(NOAA_COOPS_STATION)
    today = dt.datetime.now()
    todaystr = today.strftime("%Y%m%d %H:%M")
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

def tides(NOAA_COOPS_STATION):
    stationdata = noaa_coops.Station(NOAA_COOPS_STATION)
    today = dt.datetime.now()
    todaystr = today.strftime("%Y%m%d")
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
    onecall_result = onecall()
    print("Current Weather:")
    pprint(onecall_result.get('current'))

    print("\nForecast:")
    pprint(onecall_result.get('daily')[0:2]) # Print today's and tomorrow's forecast

    water_level = water_level_24h(NOAA_COOPS_STATION)
    print("\nWater Level (Last 24 hours):")
    pprint(water_level)
    
    tide = tides(NOAA_COOPS_STATION)
    print("\nTide Data:")
    pprint(tide)

if __name__ == "__main__":
    main()
