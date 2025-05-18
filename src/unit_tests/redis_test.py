import redis
import unittest
import os

class TestRedisIntegration(unittest.TestCase):
    def setUp(self):
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_password = os.getenv('REDIS_PASSWORD', 'sugar')
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.redis_client = redis.Redis(host=self.redis_host,
                    port=self.redis_port,
                    password=self.redis_password,
                    db=self.redis_db,
                    decode_responses=True)

    def test_redis_connection(self):
        self.assertTrue(self.redis_client.ping())

def test_data_persistence(self):
    """Проверка записи и чтения данных из Redis."""
    key = 'test_key'
    val = 'test_value'
    # Очистка перед тестом
    self.redis_client.delete(key)
    # Запись
    self.redis_client.set(key, val)
    # Чтение
    result = self.redis_client.get(key)
    self.assertEqual(result, val)

if __name__ == '__main__':
    unittest.main()