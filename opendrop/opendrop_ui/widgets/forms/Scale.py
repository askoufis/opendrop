from FormWidget import FormWidget
from opendrop.shims import tkinter as tk
from opendrop.shims import ttk
import tkFont

from opendrop.utility.argfiddler import ExtKwargs

class Scale(FormWidget, tk.Frame):
    def __init__(self, master, name=None, resolution=1, from_=0, to=100, value=0,
                 orient=tk.HORIZONTAL, **options):
        FormWidget.__init__(self, master, name)

        tk.Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.resolution = resolution
        self.from_ = from_
        self.to = to
        self.dtype = type(resolution)

        self._value = tk.StringVar()
        self._bind_var(self._value)

        self.scale = ttk.Scale(self, variable=self._value, command=self.scale_change)

        self.spinbox_var = tk.StringVar()
        self.spinbox_var.trace("w", self.spinbox_change)

        self.spinbox = tk.Spinbox(self,
            textvariable=self.spinbox_var,
            increment=resolution,
            validate="key",
            validatecommand=(
                self.register(self.validate),
                "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W"
            )
        )

        self.configure(from_=from_, to=to, orient=orient, **options)

        if "spinbox_width" not in options:
            spinbox_width = len(str(max(from_, to)))
            self.configure(spinbox_width=spinbox_width)

        self.scale_change(value)

    def configure(self, **options):
        options = ExtKwargs(options)
        options.alias({"background":"bg"})

        frame_options = options.extract("width", "height", "background")
        tk.Frame.configure(self, **frame_options)

        scale_options = options.extract("from_", "to", "length", "orient")

        if "from_" in scale_options:
            self.from_ = scale_options["from_"]

        if "to" in scale_options:
            self.to = scale_options["to"]

        if "orient" in scale_options:
            if scale_options["orient"] == tk.HORIZONTAL:
                self.scale.grid(row=0, column=0, sticky="we")
                self.spinbox.grid(row=0, column=1)
            elif scale_options["orient"] == tk.VERTICAL:
                self.scale.grid(row=0, column=0, sticky="we")
                self.spinbox.grid(row=1, column=0)

        self.scale.configure(**scale_options)

        spinbox_options = options.extract("background", "from_", "to", "spinbox_width") \
                                 .rename({"spinbox_width":"width", "background":"highlightbackground"})
        self.spinbox.configure(**spinbox_options)

    @property
    def value(self):
        return self.dtype(float(super(Scale, self).value or "0"))

    @value.setter
    def value(self, value):
        value = float(value)
        value = round(value/self.resolution)*self.resolution
        value = self.dtype(value)

        max_value = max(self.from_, self.to)
        min_value = min(self.from_, self.to)

        value = max(min(value, max_value), min_value)

        super(Scale, Scale).value.__set__(self, value)
        self.set_spinbox(value)

    def set_spinbox(self, new_value):
        self.spinbox.delete(0, len(self.spinbox.get()))
        self.spinbox.insert(0, new_value)

    def scale_change(self, new_value):
        self.value = new_value

    def spinbox_change(self, *args, **kwargs):
        new_value = self.spinbox_var.get()

        if new_value == "":
            return

        if self.dtype(float(new_value or "0")) != self.value:
            self.value = new_value

    def validate(self, action, index, value_if_allowed, prior_value, text, validation_type,
                 trigger_type, widget_name):
        if value_if_allowed == "":
            return True
        elif self.dtype == float and value_if_allowed == ".":
            return True
        else:
            if all(char in "0123456789.-+" for char in text):
                try:
                    return self.dtype(value_if_allowed) >= self.from_ and \
                           self.dtype(value_if_allowed) <= self.to
                except ValueError:
                    return False
            else:
                return False
