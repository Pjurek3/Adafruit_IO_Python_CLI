import asyncio
import datetime
import os
from typing import List

import dotenv
import httpx
import rich
import typer
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
