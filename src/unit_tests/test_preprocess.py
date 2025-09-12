import configparser
import os
import unittest
import pandas as pd
import sys

# Добавляем путь для импорта модуля train, где определён класс MultiModel
sys.path.insert(1, os.path.join(os.getcwd(), "src"))

# Определяем текущую директорию теста и путь к корню проекта (где ожидается config.ini)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
config_path = os.path.join(project_root, "config.ini")
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
    def setUp(self) -> None:
        """
        Установка: переключаем рабочую директорию на корень проекта (где лежит config.ini),
        чтобы DataMaker корректно разрешал относительные пути к данным при запуске в CI.
        """
        self._orig_cwd = os.getcwd()
        os.chdir(project_root)

        logger = Logger(SHOW_LOG)
        self.log = logger.get_logger(__name__)

        # Создаём экземпляр DataMaker. Ваша реализация может принимать дополнительные аргументы;
        # если сигнатура изменилась, можно передать config_path или пути явным образом.
        # Здесь оставляю вызов с единственным параметром (как у вас было): DataMaker(False)
        # — предполагается, что DataMaker внутри сам читает config.ini из cwd.
        try:
            self.data_maker = DataMaker(False)  # Отключаем логгирование внутри класса
        except TypeError:
            # Если конструктор DataMaker теперь принимает другие аргументы, пробуем передать config_path
            try:
                self.data_maker = DataMaker(config_path, False)
            except Exception as e:
                # Если всё равно упало — пробуем без параметров
                self.log.warning(f"Не удалось создать DataMaker с разными сигнатурами: {e}. "
                                 f"Попытка создать DataMaker() без аргументов.")
                self.data_maker = DataMaker()

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
        # Берём test_file (или train_file если test_file отсутствует) из секции DATA
        data_file = None
        if config.has_section("DATA"):
            data_file = config.get("DATA", "test_file", fallback=None) or config.get("DATA", "train_file", fallback=None)

        if data_file is None:
            raise KeyError("В config.ini не найдена секция DATA с ключами test_file/train_file")

        # Приведём к абсолютному пути относительно project_root, если путь относительный
        if not os.path.isabs(data_file):
            data_file = os.path.join(project_root, data_file)

        # Читаем CSV и вызываем save_splitted_data, предполагая сигнатуру (df, dest_path)
        df = pd.read_csv(data_file, index_col=0)
        result = self.data_maker.save_splitted_data(df, data_file)
        self.assertEqual(result, True)


if __name__ == "__main__":
    Logger(SHOW_LOG).get_logger(__name__).info("TEST TRAIN IS READY")
    unittest.main()