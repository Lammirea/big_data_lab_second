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
from train import MultiModel

SHOW_LOG = False

class TestMultiModel(unittest.TestCase):

    def setUp(self) -> None:
        logger = Logger(SHOW_LOG)
        self.log = logger.get_logger(__name__)
        self.model = MultiModel()
        self.test_df = pd.DataFrame({
            'Flow ID': ['flow1', 'flow2'],
            ' Source IP': ['192.168.1.1', '192.168.1.2'],
            ' Source Port': [12345.0, 54321.0],
            ' Destination IP': ['10.0.0.1', '10.0.0.2'],
            ' Destination Port': [80.0, 443.0],
            ' Protocol': [6.0, 17.0],
            ' Timestamp': ['2023-01-01 00:00:00', '2023-01-01 00:01:00'],
            ' Flow Duration': [1000.0, 2000.0],
            ' Total Fwd Packets': [1.0, 2.0],
            ' Total Backward Packets': [1.0, 2.0],
            ' Total Length of Fwd Packets': [100.0, 200.0],
            ' Total Length of Bwd Packets': [50.0, 100.0],
            ' Fwd Packet Length Max': [100.0, 200.0],
            ' Fwd Packet Length Min': [100.0, 100.0],
            ' Fwd Packet Length Mean': [100.0, 150.0],
            ' Fwd Packet Length Std': [0.0, 50.0],
            'Bwd Packet Length Max': [50.0, 100.0],
            ' Bwd Packet Length Min': [50.0, 50.0],
            ' Bwd Packet Length Mean': [50.0, 75.0],
            ' Bwd Packet Length Std': [0.0, 25.0],
            'Flow Bytes/s': [150.0, 150.0],
            ' Flow Packets/s': [2.0, 2.0],
            ' Flow IAT Mean': [500.0, 1000.0],
            ' Flow IAT Std': [0.0, 500.0],
            ' Flow IAT Max': [500.0, 1500.0],
            ' Flow IAT Min': [500.0, 500.0],
            'Fwd IAT Total': [500.0, 1000.0],
            ' Fwd IAT Mean': [500.0, 500.0],
            ' Fwd IAT Std': [0.0, 250.0],
            ' Fwd IAT Max': [500.0, 750.0],
            ' Fwd IAT Min': [500.0, 250.0],
            'Bwd IAT Total': [500.0, 1000.0],
            ' Bwd IAT Mean': [500.0, 500.0],
            ' Bwd IAT Std': [0.0, 250.0],
            ' Bwd IAT Max': [500.0, 750.0],
            ' Bwd IAT Min': [500.0, 250.0],
            'Fwd PSH Flags': [0.0, 1.0],
            ' Bwd PSH Flags': [0.0, 1.0],
            ' Fwd URG Flags': [0.0, 0.0],
            ' Bwd URG Flags': [0.0, 0.0],
            ' Fwd Header Length': [20.0, 40.0],
            ' Bwd Header Length': [20.0, 40.0],
            'Fwd Packets/s': [1.0, 1.0],
            ' Bwd Packets/s': [1.0, 1.0],
            ' Min Packet Length': [50.0, 50.0],
            ' Max Packet Length': [100.0, 200.0],
            ' Packet Length Mean': [75.0, 125.0],
            ' Packet Length Std': [25.0, 75.0],
            ' Packet Length Variance': [625.0, 5625.0],
            'FIN Flag Count': [0.0, 1.0],
            ' SYN Flag Count': [1.0, 1.0],
            ' RST Flag Count': [0.0, 0.0],
            ' PSH Flag Count': [0.0, 1.0],
            ' ACK Flag Count': [1.0, 1.0],
            ' URG Flag Count': [0.0, 0.0],
            ' CWE Flag Count': [0.0, 0.0],
            ' ECE Flag Count': [0.0, 0.0],
            ' Down/Up Ratio': [1.0, 1.0],
            ' Average Packet Size': [75.0, 125.0],
            ' Avg Fwd Segment Size': [100.0, 150.0],
            ' Avg Bwd Segment Size': [50.0, 75.0],
            ' Fwd Header Length.1': [20.0, 40.0],
            'Fwd Avg Bytes/Bulk': [0.0, 0.0],
            ' Fwd Avg Packets/Bulk': [0.0, 0.0],
            ' Fwd Avg Bulk Rate': [0.0, 0.0],
            ' Bwd Avg Bytes/Bulk': [0.0, 0.0],
            ' Bwd Avg Packets/Bulk': [0.0, 0.0],
            'Bwd Avg Bulk Rate': [0.0, 0.0],
            'Subflow Fwd Packets': [1.0, 2.0],
            ' Subflow Fwd Bytes': [100.0, 200.0],
            ' Subflow Bwd Packets': [1.0, 2.0],
            ' Subflow Bwd Bytes': [50.0, 100.0],
            'Init_Win_bytes_forward': [1024.0, 2048.0],
            ' Init_Win_bytes_backward': [1024.0, 2048.0],
            ' act_data_pkt_fwd': [1.0, 2.0],
            ' min_seg_size_forward': [20.0, 20.0],
            'Active Mean': [0.0, 100.0],
            ' Active Std': [0.0, 50.0],
            ' Active Max': [0.0, 150.0],
            ' Active Min': [0.0, 50.0],
            'Idle Mean': [0.0, 1000.0],
            ' Idle Std': [0.0, 500.0],
            ' Idle Max': [0.0, 1500.0],
            ' Idle Min': [0.0, 500.0],
            ' Label': ['BENIGN', 'ATTACK']
        })

    def test_preprocess_data(self):
        X, y = self.model.preprocess_data(self.test_df)
        
        # Проверяем, что целевая переменная правильно создается
        self.assertEqual(y.iloc[0], 1)  # BENIGN -> 1
        self.assertEqual(y.iloc[1], 0)  # ATTACK -> 0
        
        # Проверяем удаление категориальных столбцов
        self.assertNotIn('Flow ID', X.columns)
        self.assertNotIn(' Source IP', X.columns)
        self.assertNotIn(' Destination IP', X.columns)
        self.assertNotIn(' Timestamp', X.columns)
        self.assertNotIn(' Label', X.columns)
        
        # Проверяем удаление столбцов из columns_to_drop
        columns_to_drop = [
            'Total Fwd Packets', 'Flow IAT Mean', 'Fwd Packet Length Std', 'Bwd IAT Mean',
            'Bwd IAT Max', 'Fwd IAT Total', 'Bwd IAT Mean', 'Active Max', 'Fwd IAT Min',
            'Fwd IAT Mean', 'Bwd IAT Std', 'Bwd IAT Total', 'Fwd PSH Flags', 'FIN Flag Count',
            'Active Min', 'Down/Up Ratio', 'Bwd IAT Min', 'Active Std', 'Fwd Packet Length Min',
            'SYN Flag Count', 'Active Mean', 'Idle Std', 'Bwd PSH Flags', 'Bwd URG Flags',
            'Fwd URG Flags', 'Fwd Avg Bytes/Bulk', 'RST Flag Count', 'CWE Flag Count',
            'Bwd Avg Bulk Rate', 'Bwd Avg Packets/Bulk', 'Bwd Avg Bytes/Bulk',
            'Fwd Avg Bulk Rate', 'Fwd Avg Packets/Bulk', 'ECE Flag Count'
        ]
        for col in columns_to_drop:
            self.assertNotIn(col, X.columns)
        
        # Проверяем, что оставшиеся столбцы присутствуют
        self.assertIn('Flow Duration', X.columns)
        self.assertIn('Total Length of Fwd Packets', X.columns)


if __name__ == "__main__":
    Logger(SHOW_LOG).get_logger(__name__).info("TEST TRAIN IS READY")
    unittest.main()