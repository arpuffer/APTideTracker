'''
****************************************************************
****************************************************************

                TideTracker for E-Ink Display

                        by Sam Baker

****************************************************************
****************************************************************
'''
import datetime as dt
import json
import sys
import os
import time
import traceback
import random
from io import BytesIO
from typing import Optional, Iterable, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import weather_tides_api

sys.path.append('lib')
from waveshare_epd import epd7in5_V2

picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')
icondir = os.path.join(picdir, 'icon')
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'font')

configpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')

with open(configpath, 'r') as configfile:
    config = json.load(configfile)

LOCATION = config.get('location_name')


def write_to_screen(image, epd):
    print('Writing to screen.') # for debugging
    h_image = Image.new('1', (epd.width, epd.height), 255)
    # Open the template
    screen_output_file = Image.open(os.path.join(picdir, image))
    # Initialize the drawing context with template as background
    h_image.paste(screen_output_file, (0, 0))

    # Write to screen
    epd.init()
    epd.Clear()
    epd.display(epd.getbuffer(h_image))
    epd.sleep() # Put screen to sleep to prevent damage


def display_error(error_source, epd):
    print('Error in the', error_source, 'request.')
    # Initialize drawing
    error_image = Image.new('1', (epd.width, epd.height), 255)
    # Initialize the drawing
    draw = ImageDraw.Draw(error_image)
    draw.text((100, 150), error_source +' ERROR', font=font50, fill=black)
    draw.text((100, 300), 'Retrying in 30 seconds', font=font22, fill=black)
    current_time = dt.datetime.now().strftime('%H:%M')
    draw.text((300, 365), 'Last Refresh: ' + str(current_time), font = font50, fill=black)
    # Save the error image
    error_image_file = 'error.png'
    error_image.save(os.path.join(picdir, error_image_file))
    # Close error image
    error_image.close()
    # Write error to screen
    write_to_screen(error_image_file, epd)


# Plot last 24 hours of tide
def plotTide(TideData):
    # Adjust data for negative values
    minlevel = TideData['v'].min()
    TideData['v'] = TideData['v'] - minlevel

    # Create Plot
    fig, axs = plt.subplots(figsize=(12, 4))
    TideData['v'].plot.area(ax=axs, color='black')
    plt.title('Tide- Past 24 Hours', fontsize=20)
    #fontweight="bold",
    #axs.xaxis.set_tick_params(labelsize=20)
    #axs.yaxis.set_tick_params(labelsize=20)
    plt.savefig('images/TideLevel.png', dpi=60)
    #plt.show()


# Set the font sizes
font15 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 15)
font20 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 20)
font22 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 22)
font30 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 30)
font35 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 35)
font50 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 50)
font60 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 60)
font100 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 100)
font160 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 160)

# Set the colors
black = 'rgb(0,0,0)'
white = 'rgb(255,255,255)'
grey = 'rgb(235,235,235)'

class ForecastData:
    def __init__(self, daily_forecast: Iterable[dict]):
        self.temp_min = daily_forecast['temp']['min']
        self.temp_max = daily_forecast['temp']['max']
        self.precip_percent = daily_forecast['pop'] * 100
        self.icon_code = daily_forecast['weather'][0]['icon']

        self.fmt_temp_min = 'Low: ' + format(self.temp_min, '>.0f') + u'\N{DEGREE SIGN}F'
        self.fmt_temp_max = 'High:  ' + format(self.temp_max, '>.0f') + u'\N{DEGREE SIGN}F'
        self.fmt_precip_percent = 'Precip: ' + str(format(self.precip_percent, '.0f'))  + '%'
        self.fmt_icon_code = self.icon_code + '.png'


def main():
    # Initialize and clear screen
    print('Initializing and clearing screen.')
    epd = epd7in5_V2.EPD() # Create object for display functions

    onecall_result = weather_tides_api.onecall()
    # Get current weather conditions
    current_conditions = onecall_result.get('current')
    temp_current = current_conditions['temp']
    feels_like = current_conditions['feels_like']
    humidity = current_conditions['humidity']
    wind = current_conditions['wind_speed']
    weather = current_conditions['weather']
    report = weather[0]['description']
    icon_code = weather[0]['icon']

    # get daily forecasts
    daily = onecall_result['daily']

    today_forecast = ForecastData(daily[0])
    nx_forecast = ForecastData(daily[1])
    nx_nx_forecast = ForecastData(daily[2])

    # Format current conditions data
    string_temp_current = format(temp_current, '.0f') + u'\N{DEGREE SIGN}F'
    string_feels_like = 'Feels like: ' + format(feels_like, '.0f') +  u'\N{DEGREE SIGN}F'
    # string_humidity = 'Humidity: ' + str(humidity) + '%'  # Never used originally
    string_wind = 'Wind: ' + format(wind, '.1f') + ' MPH'
    string_report = 'Now: ' + report.title()

    # Last updated time
    now = dt.datetime.now()
    current_time = now.strftime("%H:%M")
    last_update_string = 'Last Updated: ' + current_time

    # Tide Data
    # Get water level
    wl_error = True
    while wl_error == True:
        try:
            WaterLevel = weather_tides_api.water_level_24h()
            wl_error = False
        except:
            display_error('Tide Data', epd)

    plotTide(WaterLevel)


    # Open template file
    template = Image.open(os.path.join(picdir, 'template.png'))
    # Initialize the drawing context with template as background
    draw = ImageDraw.Draw(template)

    # Current weather
    ## Open icon file
    icon_file = icon_code + '.png'
    icon_image = Image.open(os.path.join(icondir, icon_file))
    icon_image = icon_image.resize((130,130))
    template.paste(icon_image, (50, 50))

    draw.text((125,10), LOCATION, font=font35, fill=black)

    # Center current weather report
    w = draw.textlength(string_report, font=font20)
    h = 20
    #print(w)
    if w > 250:
        string_report = 'Now:\n' + report.title()

    center = int(120-(w/2))
    draw.text((center,175), string_report, font=font20, fill=black)

    # Data
    draw.text((250,55), string_temp_current, font=font35, fill=black)
    y = 100
    draw.text((250,y), string_feels_like, font=font15, fill=black)
    draw.text((250,y+20), string_wind, font=font15, fill=black)
    draw.text((250,y+40), today_forecast.fmt_precip_percent, font=font15, fill=black)
    draw.text((250,y+60), today_forecast.fmt_temp_max, font=font15, fill=black)
    draw.text((250,y+80), today_forecast.fmt_temp_min, font=font15, fill=black)

    draw.text((125,218), last_update_string, font=font15, fill=black)

    # Weather Forcast
    # Tomorrow
    icon_file = nx_forecast.fmt_icon_code
    icon_image = Image.open(os.path.join(icondir, icon_file))
    icon_image = icon_image.resize((130,130))
    template.paste(icon_image, (435, 50))
    draw.text((450,20), 'Tomorrow', font=font22, fill=black)
    draw.text((415,180), nx_forecast.fmt_temp_max, font=font15, fill=black)
    draw.text((515,180), nx_forecast.fmt_temp_min, font=font15, fill=black)
    draw.text((460,200), nx_forecast.fmt_precip_percent, font=font15, fill=black)

    # Next Next Day Forcast
    icon_file = nx_nx_forecast.fmt_icon_code
    icon_image = Image.open(os.path.join(icondir, icon_file))
    icon_image = icon_image.resize((130,130))
    template.paste(icon_image, (635, 50))
    draw.text((625,20), 'Next-Next Day', font=font22, fill=black)
    draw.text((615,180), nx_nx_forecast.fmt_temp_max, font=font15, fill=black)
    draw.text((715,180), nx_nx_forecast.fmt_temp_min, font=font15, fill=black)
    draw.text((660,200), nx_nx_forecast.fmt_precip_percent, font=font15, fill=black)


    ## Dividing lines
    draw.line((400,10,400,220), fill='black', width=3)
    draw.line((600,20,600,210), fill='black', width=2)


    # Tide Info
    # Graph
    tidegraph = Image.open('images/TideLevel.png')
    template.paste(tidegraph, (125, 240))

    # Large horizontal dividing line
    h = 240
    draw.line((25, h, 775, h), fill='black', width=3)

    # Daily tide times
    draw.text((30,260), "Today's Tide", font=font22, fill=black)

    # Get tide time predictions
    hilo_error = True
    while hilo_error == True:
        try:
            hilo_daily = weather_tides_api.HiLo()
            hilo_error = False
        except:
            display_error('Tide Prediction', epd)

    # Display tide preditions
    y_loc = 300 # starting location of list
    # Iterate over preditions
    for index, row in hilo_daily.iterrows():
        # For high tide
        if row['hi_lo'] == 'H':
            tide_time = index.strftime("%H:%M")
            tidestr = "High: " + tide_time
        # For low tide
        elif row['hi_lo'] == 'L':
            tide_time = index.strftime("%H:%M")
            tidestr = "Low:  " + tide_time

        # Draw to display image
        draw.text((40,y_loc), tidestr, font=font15, fill=black)
        y_loc += 25 # This bumps the next prediction down a line


    # Save the image for display as PNG
    screen_output_file = os.path.join(picdir, 'screen_output.png')
    template.save(screen_output_file)
    # Close the template file
    template.close()

    write_to_screen(screen_output_file, epd)
    #epd.Clear()

if __name__ == '__main__':
    main()
