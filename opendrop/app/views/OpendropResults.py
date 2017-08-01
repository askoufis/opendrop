from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from opendrop.app.view_core import BaseView

from opendrop.app import widgets

from opendrop.shims import tkinter as tk
from opendrop.shims import ttk

class OpendropResults(BaseView):
    TITLE = "Results"

    def body(self, physical_quants_fig, drop_fit_figs):
        top_level = self.top_level

        top_level.geometry("650x550")

        notebook = ttk.Notebook(top_level)
        notebook.pack()

        self.physical_quants_tab = widgets.forms.Frame(notebook)
        self.drop_fits_tab = widgets.forms.Frame(notebook)
        self.log_tab = widgets.forms.Frame(notebook)

        notebook.add(self.physical_quants_tab, text="Physical quantities")
        notebook.add(self.drop_fits_tab, text="Drop fits")
        notebook.add(self.log_tab, text="Log")

        self.physical_quants_canvas = FigureCanvasTkAgg(physical_quants_fig, master=self.physical_quants_tab)
        self.physical_quants_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

        self.drop_fits_tab.columnconfigure(0, weight=1)
        self.drop_fits_tab.rowconfigure(0, weight=1)

        self.drop_fit_canvases = []

        for drop_fit_fig in drop_fit_figs:
            self.drop_fit_canvases.append(
                FigureCanvasTkAgg(drop_fit_fig, master=self.drop_fits_tab)
            )

        self.drop_fit_canvas = None # update_drop_fit_fig() will create the canvas

        self.drop_fit_navigator = widgets.forms.PageNavigator(self.drop_fits_tab, from_=1, to=len(drop_fit_figs), wrap_around=True)
        self.drop_fit_navigator.grid(row=1)

        # Events

        top_level.bind("<Left>", lambda e: self.drop_fit_navigator.go_back())
        top_level.bind("<Right>", lambda e: self.drop_fit_navigator.go_next())

        self.drop_fit_navigator.on_change.bind(lambda w, v: self.update_drop_fit_fig())

        self.update_drop_fit_fig()

        self.center()

    def update_drop_fit_fig(self):
        if self.drop_fit_canvas:
            self.drop_fit_canvas.get_tk_widget().grid_forget()

        new_drop_fit_index = self.drop_fit_navigator.value - 1

        new_drop_fit_canvas = self.drop_fit_canvases[new_drop_fit_index]

        new_drop_fit_canvas.get_tk_widget().grid(row=0, sticky="wens")

        self.drop_fit_canvas = new_drop_fit_canvas
