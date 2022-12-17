import typer
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
    return {'timestamp': r.json()['created_at'],
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
    with console.status("[bold green]Getting Data...") as status:
        temperature_data = get_temperature_data()
        humidity_data = get_humidity_data()

        
    print(f'Readings at {temperature_data["timestamp"]}')
    print('-------------------------------------------------------')
    print(f'temperature: {float(temperature_data["value"]):.1f} C')
    print(f'humidity: {float(humidity_data["value"]):.1f} %')
