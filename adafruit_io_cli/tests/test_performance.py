"""performance test for accessing the data from API"""
from ..main import stats, Sensor, SensorSuite

import asyncio


def test_all_feed_data(benchmark):
    """tests performance to build data object which contains all items"""
    assert True
