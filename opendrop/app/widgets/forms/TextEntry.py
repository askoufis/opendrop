from FormWidget import FormWidget

from opendrop.shims import tkinter as tk
from opendrop.shims import ttk

from opendrop.utility.argfiddler import ExtKwargs

class TextEntry(tk.Entry, FormWidget):
    def __init__(self, master, name = None, **options):
        FormWidget.__init__(self, master, name)

        self._value = tk.StringVar()
        self._bind_var(self._value)

        tk.Entry.__init__(self, master, textvariable = self._value)

        self.configure(**options)

    def _configuration_dump(self):
        return self.configure_() # Not fully implemented

    configure_ = tk.Entry.configure
    def configure(self, **options):
        if not options:
            return self._configuration_dump()

        options = ExtKwargs(options)
        options.alias({"background":"bg"})

        entry_options = options.extract("justify", "font", "width", "background") \
                               .rename({"background": "highlightbackground"})
        self.configure_(**entry_options)
