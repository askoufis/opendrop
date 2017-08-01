# TODO: change to select canny instead of threshold

import cv2
import numpy as np

from opendrop.constants import ImageSourceOption, MOUSE_BUTTON_R

from opendrop.app import widgets
from opendrop.app.view_core import BaseView
from opendrop.app.views.utility.scale_from_bounds import scale_from_bounds

from opendrop.resources import resources

from opendrop.shims import tkinter as tk

from opendrop.utility import coroutines
from opendrop.utility import comvis
from opendrop.utility import source_loader

from opendrop.utility.vectors import Vector2

from PIL import Image, ImageTk

WIDTH_MIN, WIDTH_MAX = 0.4, 0.5
HEIGHT_MIN, HEIGHT_MAX = 0.4, 0.5

REL_SIZE_MIN = Vector2(WIDTH_MIN, HEIGHT_MIN)
REL_SIZE_MAX = Vector2(WIDTH_MAX, HEIGHT_MAX)

BACKGROUND_COLOR = "gray90"

FONT = ("Helvetica")

widgets = widgets.preconfigure({
    "*": {
        "background": BACKGROUND_COLOR,
    },
    "Label": {
        "font": FONT
    }
})

class SelectThreshold(BaseView):
    TITLE = "Canny edge detection"

    def submit(self):
        thresh_max = self.threshold_slider_max.value

        thresh_min_percent = self.threshold_slider_min.value

        thresh_min = int(float(thresh_min_percent)/100 * thresh_max)

        self.events.on_submit.fire(thresh_min, thresh_max)

    def cancel(self):
        self.events.on_submit.fire(None)

    def update_base_image(self):
        if self.alive:
            try:
                timestamp, image, hold_for = next(self.image_source_frames)

                image_gray = image.convert("L")

                self.base_image = image_gray

                self.update_binarised_image()

                # tk.Widget.after(delay_ms(int), ...)
                self.top_level.after(int(hold_for.time_left*1000) or 1, self.update_base_image)
            except StopIteration:
                pass

    def update_binarised_image(self):
        # Try to acquire the lock and if failed, just skip this function, it's not a huge deal since
        # this is only updating the display image and the base image updates on a regular basis
        # which will then call update_binarised_image to refresh the display image.
        #
        # Don't block if lock is not free since this is running on the main thread, this issue
        # occurs else where as well and is a bit finicky.
        lock_acquired = self.busy.acquire(False)
        if lock_acquired:
            if self.base_image:
                try:
                    resized_image = self.base_image.resize(self.resize_to, resample=Image.BILINEAR)
                    image_array = np.array(resized_image)

                    thresh_max = self.threshold_slider_max.value
                    thresh_min = float(self.threshold_slider_min.value)/100 * thresh_max

                    image_array = cv2.Canny(image_array, thresh_min, thresh_max)
                    image_tk = ImageTk.PhotoImage(Image.fromarray(image_array))

                    self.image_label.configure(image=image_tk)
                    self.image_label.image = image_tk
                finally:
                    self.busy.release()

    def mouse_wheel(self, e):
        delta = e.delta * 1.3
        self.threshold_slider_max.value = self.threshold_slider_max.value + delta

    def body(self, image_source): #image_source_desc, image_source_type):
        top_level = self.top_level

        with self.busy:
            self.image_source = image_source

            self.default_threshold_val = comvis.otsu_threshold_val(image_source.read()[1])

            image_source_fps = None

            if isinstance(image_source, source_loader.LocalImages):
                image_source_fps = 2
            elif isinstance(image_source, source_loader.USBCameraSource):
                image_source_fps = -1 # -1 specifies as fast as possible

            screen_res = self.window_manager.screen_resolution
            image_source_size = self.image_source.size

            self.scale = scale_from_bounds(
                image_size=image_source_size,
                max_size=REL_SIZE_MAX * screen_res,
                min_size=REL_SIZE_MIN * screen_res
            )

            self.resize_to = (image_source_size * self.scale).round_to_int()

            # Widgets
            self.image_label = widgets.Label(top_level, width=self.resize_to.x, height=self.resize_to.y)
            self.image_label.pack()

            threshold_slider_frame = widgets.forms.Frame(top_level, padx="30", pady="10")
            threshold_slider_frame.pack(fill="both")
            threshold_slider_frame.columnconfigure(1, weight=1)

            widgets.Label(threshold_slider_frame, text="Max:", anchor="w") \
                .grid(row=0, column=0, sticky="w")
            self.threshold_slider_max = widgets.forms.Scale(threshold_slider_frame,
                from_=0,
                to=255,
                value=self.default_threshold_val
            )
            self.threshold_slider_max.grid(row=0, column=1, sticky="we")

            widgets.Label(threshold_slider_frame, text="Min (% of max):", anchor="w") \
                .grid(row=1, column=0, sticky="w")
            self.threshold_slider_min = widgets.forms.Scale(threshold_slider_frame,
                from_=0,
                to=100,
                value=50
            )
            self.threshold_slider_min.grid(row=1, column=1, sticky="we")

        # Resizing and recentering top_level

        top_level.geometry("{0}x{1}".format(*( self.resize_to + (0, 90) )))
        self.center()

        # top_level event bindings

        self.image_label.bind("<MouseWheel>", self.mouse_wheel)

        top_level.bind("<space>", lambda e: self.submit())
        top_level.bind("<Return>", lambda e: self.submit())
        top_level.bind(MOUSE_BUTTON_R, lambda e: self.submit())

        top_level.bind("<Escape>", lambda e: self.cancel())

        # Background tasks

        self.threshold_slider_max.on_change.bind(lambda widget, val: self.update_binarised_image())
        self.threshold_slider_min.on_change.bind(lambda widget, val: self.update_binarised_image())

        self.image_source_frames = iter(self.image_source.frames(fps=image_source_fps, loop=True))
        self.update_base_image()

    # def _clear(self):
    #     self.cancel()
