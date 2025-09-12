import configparser
import os
import unittest
import pandas as pd
import sys

# Добавляем путь для импорта модуля train, где определён класс MultiModel
sys.path.insert(1, os.path.join(os.getcwd(), "src"))

# Загружаем конфигурацию, если необходимо (можно оставить этот блок, если он используется в preprocess)
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.abspath(os.path.join(current_dir, "../..", "config.ini"))
print(f"Пытаемся загрузить конфиг из: {config_path}")
if os.path.exists(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
else:
    raise FileNotFoundError(f"Ошибка: файл {config_path} не найден")

import warnings

warnings.filterwarnings("ignore")

from logger import Logger
from preprocess import DataMaker

SHOW_LOG = True

class TestDataFilter(unittest.TestCase):
    def setUp(self) -> None: # Проверка класса DataMaker из preprocess.py
        logger = Logger(SHOW_LOG)
        self.log = logger.get_logger(__name__)
        self.data_maker = DataMaker(False) # Отключаем логгирование внутри класса

    def test_get_data(self):
        """Проверка на успешную обработку данных (get_data должен вернуть True)."""
        result = self.data_maker.get_data()
        self.assertEqual(result, True)

    def test_split_data(self):
        """Проверка на успешное разбиение данных (split_data должен вернуть True)."""
        result = self.data_maker.split_data()
        self.assertEqual(result, True)

    def test_save_splitted_data(self):
        """
        Проверка на успешное сохранение данных по пути из (временного) конфига.
        Используем наш временный label.csv (self.config['State']['Label']).
        """
        self.assertEqual(self.data_maker.save_splitted_data(pd.read_csv(
            config["UTEST_DATA"]["train_file"], index_col=0, encoding='latin1', sep=";", low_memory=False), config["UTEST_DATA"]["train_file"]), True)


if __name__ == "__main__":
    Logger(SHOW_LOG).get_logger(__name__).info("TEST TRAIN IS READY")
    unittest.main()