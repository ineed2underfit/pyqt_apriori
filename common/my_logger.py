import os
import sys
from loguru import logger
from common.config import VERSION


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class MyLogger:
    def __init__(self):
        self.logger = logger
        self.logger.remove()

        if sys.stdout:
            self.logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                       "{process.name} | "
                       "{thread.name} | "
                       "<cyan>{module}</cyan>.<cyan>{function}</cyan>"
                       ":<cyan>{line}</cyan> | "
                       "<level>{level}</level>: <level>{message}</level>",
            )

    def get_logger(self):
        return self.logger


my_logger = MyLogger().get_logger()
