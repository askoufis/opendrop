from opendrop.shims import tkinter as tk

from opendrop.utility import coroutines

from opendrop.app.view_core.WindowManager import WindowManager

class ViewService(object):
    def __init__(self, default_title = None):
        self.root = tk.Tk()

        self.windows = {
            "root": WindowManager(self.root)
        }

    def mainloop(self):
        self.root.mainloop()

    @coroutines.co
    def end(self):
        for window in self.windows.values():
            yield window.clear()

        self.root.destroy()
