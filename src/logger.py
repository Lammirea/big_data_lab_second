import logging
import os
import sys
import warnings

warnings.filterwarnings("ignore")

class Logger:
    """
        Class for logging behaviour of data exporting - object of ExportingTool class
    """

    def __init__(self, show, enable = True) -> None:
        """
            Re-defined __init__ method which sets show parametr

        Args:
            show (bool): if set all logs will be shown in terminal
        """
        self.FORMATTER = logging.Formatter(
            "%(asctime)s — %(name)s — %(levelname)s — %(message)s")
        self.LOG_FILE = "logfile.log"
        self.show = show # Логгировать ли в консоль
        self.enable = enable # Включен ли логгер вообще (для тестов - отключаем)

    def clear_log_file(self) -> None:
        """Очищает файл логов"""
        if os.path.exists(self.LOG_FILE):
            with open(self.LOG_FILE, 'w'):
                pass

    def get_console_handler(self) -> logging.StreamHandler:
        """
            Class method the aim of which is getting a console handler to show logs on terminal

        Returns:
            logging.StreamHandler: handler object for streaming output through terminal
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.FORMATTER)
        return console_handler

    def get_file_handler(self) -> logging.FileHandler:
        """
            Class method the aim of which is getting a file handler to write logs in file LOG_FILE

        Returns:
            logging.FileHandler: handler object for streaming output through std::filestream
        """
        file_handler = logging.FileHandler(self.LOG_FILE, mode='a')
        file_handler.setFormatter(self.FORMATTER)
        return file_handler

    def get_logger(self, logger_name: str):
        """
            Class method which creates logger with certain name

        Args:
            logger_name (str): name for logger

        Returns:
            logger: object of Logger class
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        if self.enable:
            if self.show:
                logger.addHandler(self.get_console_handler())
            logger.addHandler(self.get_file_handler())
        logger.propagate = False
        return logger