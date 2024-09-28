import datetime as dt
import logging

import psutil


def print_process_tree(process, indent=""):
    try:
        if process.is_running():
            print(indent + "|-", process.pid, process.name())
            indent += " " * 4
            for child in process.children(recursive=False):
                print_process_tree(child, indent)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass


class StreamlitLogHandler(logging.Handler):
    def __init__(self, widget_update_func):
        super().__init__()
        self.widget_update_func = widget_update_func

    def emit(self, record):
        msg = self.format(record)
        self.widget_update_func(msg)


def last_n_lines(s, n):
    lines = s.splitlines()
    error_lines = [line for line in lines if "error" in line.lower()]
    return "\n".join(error_lines + lines[-(n - len(error_lines)) :])


def get_arknights_weekday(x: dt.datetime):
    # 1 = Monday, ...
    date = x.date() if x.hour >= 4 else x.date() - dt.timedelta(days=1)
    return date.weekday() + 1
