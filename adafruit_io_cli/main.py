import typer
import datetime
import dotenv
import rich
from rich.console import Console
import requests
import os

dotenv.load_dotenv()

app = typer.Typer()

console = rich.console.Console()

def get_feed_data(feed:str):
    """returns the feeddata from online"""
    key = os.environ['ADAFRUIT_IO_KEY']
    user = os.environ['ADAFRUIT_IO_USERNAME']
    
    headers = {'X-AIO-Key': key}
    url = f'https://io.adafruit.com/api/v2/{user}/feeds/{feed}/data/last'

    r = requests.get(url, headers=headers)
    
    # this section formats time to the Seattle time.  Expected time from the 
    # data feed is UTC
    date_format = "%Y-%m-%dT%H:%M:%SZ"
    utc_time = datetime.datetime.strptime(r.json()['created_at'], date_format)
    seattle_time = utc_time - datetime.timedelta(hours=8)

    return {'timestamp': seattle_time,
            'value': r.json()['value']
            }

def get_humidity_data():
    """retrieves the humidity data from online"""
    feed = 'office-temperature.office-humidity'
    return get_feed_data(feed=feed)

def get_temperature_data():
    """retrieves the temperature data from online"""
    feed = 'office-temperature.office-temperature'
    return get_feed_data(feed=feed)

def get_air_quality_pm10_data():
    """returns all the air quality data feeds"""
    feed = 'air-quality-pm10'
    return get_feed_data(feed=feed)

def get_air_quality_pm25_data():
    """returns all the air quality data feeds"""
    feed = 'air-quality-pm25'
    return get_feed_data(feed=feed)

def get_air_quality_pm100_data():
    """returns all the air quality data feeds"""
    feed = 'air-quality-pm100'
    return get_feed_data(feed=feed)
    

@app.callback()
def callback():
    """
    Awesome Portal Gun
    """
    pass

@app.command()
def stats():
    """
    Shoot the portal gun
    """
    console.clear()
    with console.status("[bold green]Getting Data...") as status:
        temperature_data = get_temperature_data()
        humidity_data = get_humidity_data()
        aq10 = get_air_quality_pm10_data()
        aq25 = get_air_quality_pm25_data()
        aq100 = get_air_quality_pm100_data()

        
    print(f'Readings at {temperature_data["timestamp"]}')
    print('-------------------------------------------------------')
    print(f'temperature: {float(temperature_data["value"]):.1f} C')
    print(f'humidity: {float(humidity_data["value"]):.1f} %')
    print()
    print(f'Air Quality Readings at {aq10["timestamp"]}')
    print('-------------------------------------------------------')
    print(f'pm10: {float(aq10["value"])}')
    print(f'pm25: {float(aq25["value"])}')
    print(f'pm100: {float(aq100["value"])}')