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

    def tearDown(self) -> None:
        # Восстановим cwd и удалим временную директорию
        os.chdir(self._orig_cwd)
        try:
            self.tmpdir_obj.cleanup()
        except Exception:
            pass

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
        label_path = self.config['State']['Label']
        # Подгружаем label csv, как в исходном тесте (index_col=0, т.к. мы сохраняли index=True)
        label_df = pd.read_csv(label_path, index_col=0)
        result = self.data_maker.save_splitted_data(label_df, label_path)
        self.assertEqual(result, True)


if __name__ == "__main__":
    Logger(SHOW_LOG).get_logger(__name__).info("TEST TRAIN IS READY")
    unittest.main()