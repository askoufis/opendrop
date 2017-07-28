from FormWidget import FormWidget

from opendrop.shims import tkinter as tk

from opendrop.utility.argfiddler import ExtKwargs

class Frame(tk.Frame, FormWidget):
    def __init__(self, master, name = None, **options):
        FormWidget.__init__(self, master, name)

        tk.Frame.__init__(self, master)

        self.configure(**options)

    def configure(self, **options):
        options = ExtKwargs(options).alias({"background":"bg"}) \
                                    .extract("width", "height", "padx", "pady", "background")
        return tk.Frame.configure(self, **options)
