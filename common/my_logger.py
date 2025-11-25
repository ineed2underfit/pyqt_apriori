import os
import sys
from loguru import logger
from common.config import VERSION


def get_base_dir():
    """返回 EXE 同目录或开发环境下的文件目录"""
    if getattr(sys, 'frozen', False):  # 运行在 exe
        return os.path.dirname(sys.executable)
    else:  # 运行在开发环境
        return os.path.dirname(os.path.abspath(__file__))


def get_log_dir():
    """确保 logs 目录总是可写，并位于 EXE 同目录"""
    base_path = get_base_dir()
    log_dir = os.path.join(base_path, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


class MyLogger:
    def __init__(self):
        base_path = get_base_dir()
        log_dir = get_log_dir()

        log_file_path = os.path.join(log_dir, f"v{VERSION}.log")

        # 写调试日志到 EXE 同级目录
        debug_path = os.path.join(base_path, "debug_log.txt")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(f"base_path={base_path}\n")
            f.write(f"log_dir={log_dir}\n")
            f.write(f"log_file_path={log_file_path}\n")

        self.logger = logger
        self.logger.remove()

        if sys.stderr:  # sys.stderr 在 console=False 时通常仍然有效，但为了安全，我们可以尝试判断
            # 更保险的做法是移除它，因为我们已经在文件中输出了。
            pass  # 移除对 sys.stdout 的添加，或将其改为 sys.stderr 并在没有窗口时忽略

        # 文件输出 (保留，这是核心日志)

        # 控制台输出
        self.logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "{process.name} | "
                   "{thread.name} | "
                   "<cyan>{module}</cyan>.<cyan>{function}</cyan>"
                   ":<cyan>{line}</cyan> | "
                   "<level>{level}</level>: <level>{message}</level>",
        )

        # 文件输出
        self.logger.add(
            log_file_path,
            level="WARNING",
            rotation="10 MB",
            format='{time:YYYY-MM-DD HH:mm:ss} - '
                   "{process.name} | "
                   "{thread.name} | "
                   "{module}.{function}:{line} - {level} - {message}",
            encoding="utf-8"
        )

    def get_logger(self):
        return self.logger


# 初始化全局 logger
my_logger = MyLogger().get_logger()
