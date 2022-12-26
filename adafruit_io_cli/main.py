import datetime
import os

import dotenv
import httpx
import requests
import rich
import typer
from rich.console import Console

dotenv.load_dotenv()

app = typer.Typer()

console = rich.console.Console()


def get_feed_data(feed: str):
    """returns the feeddata from online"""
    key = os.environ["ADAFRUIT_IO_KEY"]
    user = os.environ["ADAFRUIT_IO_USERNAME"]

    headers = {"X-AIO-Key": key}
    url = f"https://io.adafruit.com/api/v2/{user}/feeds/{feed}/data/last"

    r = requests.get(url, headers=headers)

    # this section formats time to the Seattle time.  Expected time from the
    # data feed is UTC
    date_format = "%Y-%m-%dT%H:%M:%SZ"
    utc_time = datetime.datetime.strptime(r.json()["created_at"], date_format)
    seattle_time = utc_time - datetime.timedelta(hours=8)

    return {"timestamp": seattle_time, "value": r.json()["value"]}

async def get_feed_data_async(feed:str, client: httpx.Client):
    """async method to get feed data
    client expected to follow httpx pattern: https://www.python-httpx.org/async/"""
    key = os.environ["ADAFRUIT_IO_KEY"]
    user = os.environ["ADAFRUIT_IO_USERNAME"]

    headers = {"X-AIO-Key": key}
    url = f"https://io.adafruit.com/api/v2/{user}/feeds/{feed}/data/last"

    r = await client.get(url, headers=headers)
    date_format = "%Y-%m-%dT%H:%M:%SZ"
    utc_time = datetime.datetime.strptime(r.json()["created_at"], date_format)
    seattle_time = utc_time - datetime.timedelta(hours=8)

    return {"timestamp": seattle_time, "value": r.json()["value"]}



def get_humidity_data():
    """retrieves the humidity data from online"""
    feed = "office-temperature.office-humidity"
    return get_feed_data(feed=feed)

async def get_humidity_data_async(client:httpx.Client):
    """retrieves the humidity data from online"""
    feed = "office-temperature.office-humidity"
    r = await get_feed_data_async(feed=feed, client=client)
    return r

def get_temperature_data():
    """retrieves the temperature data from online"""
    feed = "office-temperature.office-temperature"
    return get_feed_data(feed=feed)

async def get_temperature_data_async(client: httpx.Client):
    """retrieves the temperature data from online"""
    feed = "office-temperature.office-temperature"
    r = await get_feed_data_async(feed=feed, client=client)
    return r


def get_air_quality_pm10_data():
    """returns all the air quality data feeds"""
    feed = "air-quality-pm10"
    return get_feed_data(feed=feed)

async def get_air_quality_pm10_data_async(client: httpx.Client):
    """returns all the air quality data feeds"""
    feed = "air-quality-pm10"
    return await get_feed_data_async(feed=feed, client=client)


def get_air_quality_pm25_data():
    """returns all the air quality data feeds"""
    feed = "air-quality-pm25"
    return get_feed_data(feed=feed)

async def get_air_quality_pm25_data_async(client: httpx.Client):
    """returns all the air quality data feeds"""
    feed = "air-quality-pm25"
    return await get_feed_data_async(feed=feed, client=client)


def get_air_quality_pm100_data():
    """returns all the air quality data feeds"""
    feed = "air-quality-pm100"
    return get_feed_data(feed=feed)

async def get_air_quality_pm100_data_async(client: httpx.Client):
    """returns all the air quality data feeds"""
    feed = "air-quality-pm100"
    return await get_feed_data_async(feed=feed, client=client)


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
    print("-------------------------------------------------------")
    print(f'temperature: {float(temperature_data["value"]):.1f} C')
    print(f'humidity: {float(humidity_data["value"]):.1f} %')
    print()
    print(f'Air Quality Readings at {aq10["timestamp"]}')
    print("-------------------------------------------------------")
    print(f'pm10: {float(aq10["value"])}')
    print(f'pm25: {float(aq25["value"])}')
    print(f'pm100: {float(aq100["value"])}')

@app.command()
async def stats_2():
    """
    Shoot the portal gun
    """
    console.clear()
    with console.status("[bold green]Getting Data...") as status:
        async with httpx.AsyncClient() as client:
            temperature_data = await get_temperature_data_async(client=client)
            humidity_data = await get_humidity_data_async(client=client)
            aq10 = await get_air_quality_pm10_data_async(client=client)
            aq25 = await get_air_quality_pm25_data_async(client=client)
            aq100 = await get_air_quality_pm100_data_async(client=client)

    print(f'Readings at {temperature_data["timestamp"]}')
    print("-------------------------------------------------------")
    print(f'temperature: {float(temperature_data["value"]):.1f} C')
    print(f'humidity: {float(humidity_data["value"]):.1f} %')
    print()
    print(f'Air Quality Readings at {aq10["timestamp"]}')
    print("-------------------------------------------------------")
    print(f'pm10: {float(aq10["value"])}')
    print(f'pm25: {float(aq25["value"])}')
    print(f'pm100: {float(aq100["value"])}')