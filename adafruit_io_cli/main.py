import datetime
import os

import dotenv
import requests
import rich
import typer
from rich.console import Console
from rich.table import Table

dotenv.load_dotenv()

app = typer.Typer()

console = rich.console.Console()

date_format = "%Y-%m-%dT%H:%M:%SZ"


def date_diff(d1: str) -> int:
    """returns number of minutes between dates.
    The date input is compared with current date.  Expected date
    is to be input in UTC"""
    if not isinstance(d1, datetime.datetime):
        d1 = datetime.datetime.strptime(d1, date_format)
    d2 = datetime.datetime.now()
    delta = d2 - d1

    return delta.days * 24 * 60 + int(delta.seconds / 60)


def get_feed_data(feed: str):
    """returns the feeddata from online"""
    key = os.environ["ADAFRUIT_IO_KEY"]
    user = os.environ["ADAFRUIT_IO_USERNAME"]

    headers = {"X-AIO-Key": key}
    url = f"https://io.adafruit.com/api/v2/{user}/feeds/{feed}/data/last"

    r = requests.get(url, headers=headers)

    # this section formats time to the Seattle time.  Expected time from the
    # data feed is UTC

    utc_time = datetime.datetime.strptime(r.json()["created_at"], date_format)
    seattle_time = utc_time - datetime.timedelta(hours=8)

    return {"timestamp": seattle_time, "value": r.json()["value"]}


def get_full_feed_data(feed: str):
    """returns the feeddata from online"""
    key = os.environ["ADAFRUIT_IO_KEY"]
    user = os.environ["ADAFRUIT_IO_USERNAME"]

    headers = {"X-AIO-Key": key}
    url = f"https://io.adafruit.com/api/v2/{user}/feeds/{feed}/data"

    # set limit to 1000 so we get full data if possible
    # this is current limit of the API
    start_time = (datetime.datetime.utcnow() - datetime.timedelta(hours=8)).strftime(
        date_format
    )
    r = requests.get(
        url, headers=headers, params={"limit": 1000, "start_time": start_time}
    )

    # this section formats time to the Seattle time.  Expected time from the
    # data feed is UTC

    query_data = r.json()
    results = []
    for record in query_data:
        utc_time = datetime.datetime.strptime(record["created_at"], date_format)
        results.append(
            {
                "timestamp": utc_time - datetime.timedelta(hours=8),
                "value": float(record["value"]),
            }
        )

    return results


def get_humidity_data():
    """retrieves the humidity data from online"""
    feed = "office-temperature.office-humidity"
    return get_feed_data(feed=feed)


def get_temperature_data():
    """retrieves the temperature data from online"""
    feed = "office-temperature.office-temperature"
    return get_feed_data(feed=feed)


def get_air_quality_pm10_data():
    """returns all the air quality data feeds"""
    feed = "air-quality-pm10"
    return get_feed_data(feed=feed)


def get_air_quality_pm25_data():
    """returns all the air quality data feeds"""
    feed = "air-quality-pm25"
    return get_feed_data(feed=feed)


def get_air_quality_pm100_data():
    """returns all the air quality data feeds"""
    feed = "air-quality-pm100"
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
    print(
        f'Minutes since last reading: {date_diff(temperature_data["timestamp"])} minutes'
    )

    table = Table()
    table.add_column("measure", justify="right")
    table.add_column("value")
    table.add_column("min-value")
    table.add_column("max-value")

    table.add_row("temperature", f'{float(temperature_data["value"]):.1f} C')
    table.add_row("humidity", f'{float(humidity_data["value"]):.1f} %')
    table.add_row("pm10", str(float(aq10["value"])))
    table.add_row("pm25", str(float(aq25["value"])))
    table.add_row("pm100", str(float(aq100["value"])))

    console.print(table)
