import asyncio
import datetime
import os
from typing import List

import dotenv
import httpx
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


async def get_feed_data_async(feed: str, client: httpx.Client):
    """returns the feeddata from online"""
    key = os.environ["ADAFRUIT_IO_KEY"]
    user = os.environ["ADAFRUIT_IO_USERNAME"]

    headers = {"X-AIO-Key": key}
    url = f"https://io.adafruit.com/api/v2/{user}/feeds/{feed}/data/last"

    r = await client.get(url, headers=headers)

    # this section formats time to the Seattle time.  Expected time from the
    # data feed is UTC

    utc_time = datetime.datetime.strptime(r.json()["created_at"], date_format)
    seattle_time = utc_time - datetime.timedelta(hours=8)

    return {"timestamp": seattle_time, "value": r.json()["value"]}


async def get_async_sensor_data():
    """async method to get all the data for the async methods"""
    async with httpx.AsyncClient() as client:
        r_humidity = await get_feed_data_async(
            feed="office-temperature.office-humidity", client=client
        )
        r_temperature = await get_feed_data_async(
            feed="office-temperature.office-temperature", client=client
        )
        r_pm10 = await get_feed_data_async(feed="air-quality-pm10", client=client)
        r_pm25 = await get_feed_data_async(feed="air-quality-pm25", client=client)
        r_pm100 = await get_feed_data_async(feed="air-quality-pm100", client=client)

    return {
        "humidity": r_humidity,
        "temperature": r_temperature,
        "r_pm10": r_pm10,
        "r_pm25": r_pm25,
        "r_pm100": r_pm100,
    }


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


class Sensor:
    """wrapper around individual sensor for the adafruit IO data feed

    meant to be aggregated with the sensorSuite"""

    # controls how much data is pulled back from sensor feed
    TIME_RANGE = 24  # hours

    def __init__(self, name: str, feed: str):
        self.name = name
        self.feed = feed
        self.key = os.environ["ADAFRUIT_IO_KEY"]
        self.user = os.environ["ADAFRUIT_IO_USERNAME"]
        self.headers = {"X-AIO-Key": self.key}
        self._data = []  # placholder to store the data

    @property
    def url(self):
        return f"https://io.adafruit.com/api/v2/{self.user}/feeds/{self.feed}/data"

    async def get_data(self, client: httpx.Client):
        """returns the feeddata from online.  This sets the self._data
        value and returns resulting list.

        Builds a list of tuples with the timestamp first then value"""

        # sets start time so we can offset by X time.  Defaults to
        # 24 hours
        start_time = (
            datetime.datetime.utcnow() - datetime.timedelta(hours=self.TIME_RANGE)
        ).strftime(date_format)
        r = await client.get(
            self.url,
            headers=self.headers,
            params={"limit": 1000, "start_time": start_time},
        )

        query_data = r.json()
        results = []
        for record in query_data:
            utc_time = datetime.datetime.strptime(record["created_at"], date_format)
            results.append(
                (utc_time - datetime.timedelta(hours=8), float(record["value"]))
            )
        self._data = results
        return results

    @property
    def min(self):
        """returns the minimum value from list"""
        return min([i[1] for i in self._data])

    @property
    def max(self):
        """returns the minimum value from list"""
        return max([i[1] for i in self._data])

    @property
    def min_date(self):
        """returns earliest timestamp"""
        return min([i[0] for i in self._data])

    @property
    def max_date(self):
        """returns earliest timestamp"""
        return max([i[0] for i in self._data])

    @property
    def last_point(self):
        """returns most recent data point"""
        return self._data[0]


class SensorSuite:
    """sensor suite which covers my home monitoring suite"""

    def __init__(self, sensors: List[Sensor]):
        self.sensors = sensors

    async def get_data(self):
        """gets data for all sensors"""
        async with httpx.AsyncClient() as client:
            for i in self.sensors:
                _ = await i.get_data(client=client)


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


@app.command()
def stats_2():
    """
    Shoot the portal gun
    """
    console.clear()
    loop = asyncio.get_event_loop()
    tasks = (get_async_sensor_data(), get_async_sensor_data(), get_async_sensor_data())
    results = loop.run_until_complete(asyncio.gather(*tasks))
    rich.print(results)
    loop.close()


@app.command()
def stats_3():
    """
    Shoot the portal gun
    """

    sensors = [
        Sensor(name="humidity", feed="office-temperature.office-humidity"),
        Sensor(name="temperature", feed="office-temperature.office-temperature"),
        Sensor(name="pm10", feed="air-quality-pm10"),
        Sensor(name="pm25", feed="air-quality-pm25"),
        Sensor(name="pm100", feed="air-quality-pm100"),
    ]

    sensor_suite = SensorSuite(sensors=sensors)

    console.clear()
    with console.status("[bold green]Getting Data...") as status:
        # async method to get the senors
        loop = asyncio.get_event_loop()
        tasks = (sensor_suite.get_data(),)
        results = loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()

    table = Table()
    table.add_column("measure", justify="right")
    table.add_column("value")
    table.add_column("min-value")
    table.add_column("max-value")

    for i in sensor_suite.sensors:
        table.add_row(i.name, f"{i.last_point[1]:.1f}", f"{i.min:.1f}", f"{i.max:.1f}")

    print(f"Readings at {sensor_suite.sensors[0].last_point[0]}")
    print(
        f"Minutes since last reading: {date_diff(sensor_suite.sensors[0].last_point[0])} minutes"
    )
    console.print(table)
