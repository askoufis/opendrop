# DEPRECATED

import importlib

import threading

try:
    import Queue as queue
except ImportError:
    import queue

_matplotlib = None

_include_queue = queue.Queue()
_include_queue.put("matplotlib")

def load():
    global _matplotlib

    _include_queue.get(True)

    _matplotlib = importlib.import_module("matplotlib")
    _matplotlib.use("TkAgg")

    _include_queue.task_done()

    while True:
        submodule_name = _include_queue.get(True)

        importlib.import_module("matplotlib." + submodule_name)

        _include_queue.task_done()

_loading_thread = threading.Thread(target=load)
_loading_thread.daemon = True

_loading_thread.start()

def ready():
    _include_queue.join()

    return _matplotlib

def include(submodule_name):
    _include_queue.put(submodule_name)
