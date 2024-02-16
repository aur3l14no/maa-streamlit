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
    return "\n".join(s.splitlines()[-n:])
