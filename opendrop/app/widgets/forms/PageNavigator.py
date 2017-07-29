from FormWidget import FormWidget
from IntegerEntry import IntegerEntry

from opendrop.shims import tkinter as tk
from opendrop.shims import ttk

import tkFont

from opendrop.utility.argfiddler import ExtKwargs

class PageNavigator(tk.Frame, FormWidget):
    def __init__(self, master, from_, to, name=None, value=None, wrap_around=False, **options):
        FormWidget.__init__(self, master, name)

        tk.Frame.__init__(self, master)

        self.from_ = from_
        self.to = to

        self.wrap_around = wrap_around

        self._value = tk.IntVar()
        self._bind_var(self._value)

        self.left = tk.Button(self, text="<", command=self.go_back, width=2)
        self.right = tk.Button(self, text=">", command=self.go_next, width=2)

        self.text_frame = tk.Frame(self, padx=10)

        self.entry = IntegerEntry(self.text_frame, justify="right")
        self.text = tk.Label(self.text_frame)

        self.entry.grid(row=0, column=0)
        self.text.grid(row=0, column=1)

        self.left.grid(row=0, column=0)
        self.text_frame.grid(row=0, column=1)
        self.right.grid(row=0, column=2)

        self.entry.bind("<Return>", self.entry_return_cb)

        if value is not None:
            self.value = value
        else:
            self.value = from_

        self.configure(from_=from_, to=to, **options)

    def configure(self, **options):
        options = ExtKwargs(options)

        bounds = options.extract("from_",  "to")

        if "from_" in bounds:
            self.from_ = bounds["from_"]

            if self.value < self.from_:
                self.value = self.from_

        if "to" in bounds:
            self.to = bounds["to"]

            # Update 'of {}' label
            self.text.configure(text="of {}".format(self.to))

            # Resize the entry to make sure it can still fit numbers from new range
            self.entry.configure(width=len(str(max(self.from_, self.to))) + 1)

            if self.value > self.to:
                self.value = self.to

    def entry_return_cb(self, e):
        self.go_to(self.entry.value)

        self.master.focus() # remove the focus from entry box

    def go_next(self):
        if self.wrap_around and self.value == self.to:
            self.value = self.from_
        else:
            self.value += 1

    def go_back(self):
        if self.wrap_around and self.value == self.from_:
            self.value = self.to
        else:
            self.value -= 1

    def go_to(self, value):
        self.value = value

    def sync_entry(self):
        self.entry.value = self.value

    @property
    def value(self):
        return super(PageNavigator, self).value

    @value.setter
    def value(self, value):
        if value > self.to:
            value = self.to
        elif value < self.from_:
            value = self.from_

        super(PageNavigator, PageNavigator).value.__set__(self, value)

        self.sync_entry()
