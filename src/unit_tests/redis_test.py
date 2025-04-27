import redis
import unittest

class TestRedisIntegration(unittest.TestCase):
    def setUp(self):
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

    def test_redis_connection(self):
        self.assertTrue(self.redis_client.ping())

    def test_data_persistence(self):
        self.redis_client.set("test_key", "test_value")
        self.assertEqual(self.redis_client.get("test_key"), "test_value")