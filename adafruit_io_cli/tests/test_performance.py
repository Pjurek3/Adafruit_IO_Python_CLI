"""performance test for accessing the data from API"""
from ..main import stats

def test_all_feed_data(benchmark):
    """tests performance to build data object which contains all items"""
    result = benchmark(stats)
    assert True
