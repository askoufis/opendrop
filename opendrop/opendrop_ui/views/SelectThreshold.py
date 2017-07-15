import cv2
import numpy as np

from opendrop.constants import ImageSourceOption

from opendrop.opendrop_ui import widgets
from opendrop.opendrop_ui.view_manager import View
from opendrop.opendrop_ui.views.utility.scale_from_bounds import scale_from_bounds

from opendrop.resources import resources

from opendrop.shims import tkinter as tk

import opendrop.utility.coroutines as coroutines
import opendrop.utility.source_loader as source_loader
from opendrop.utility.vectors import Vector2

from PIL import Image, ImageTk

import threading, time

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

def otsu_threshold_val(image):
    """
        Takes in a Pillow.Image image argument and uses OpenCV to calculate the otsu threshold value
    """
    image_gray = image.convert("L")
    image_array_gray = np.array(image_gray)
    thresh_val, image_array_binarised = cv2.threshold(image_array_gray, 127, 255,
                                                      cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    return thresh_val


class SelectThreshold(View):
    def submit(self):
        thresh_val = self.threshold_slider.value

        self.events.submit(thresh_val)

    def cancel(self):
        self.events.submit(None)

    def update_base_image(self, image):
        with self.busy:
            if not self.alive:
                self.update_base_image_bind.unbind()
                return

            if image:
                image_gray = image.convert("L")
                image.close()

                self.base_image = image_gray

        self.update_binarised_image()

    def update_binarised_image(self, thresh_val=None):
        with self.busy:
            if self.base_image:
                resized_image = self.base_image.resize(self.resize_to, resample=Image.BILINEAR)
                image_array = np.array(resized_image)

                thresh_val = thresh_val or self.threshold_slider.value

                ret, image_array_binarised = cv2.threshold(image_array, float(thresh_val), 255, cv2.THRESH_BINARY)
                image_tk = ImageTk.PhotoImage(Image.fromarray(image_array_binarised))

                self.image_label.configure(image=image_tk)
                self.image_label.image = image_tk

    def mouse_wheel(self, e):
        delta = e.delta * 1.3
        self.threshold_slider.value = self.threshold_slider.value + delta

    def body(self, image_source): #image_source_desc, image_source_type):
        root = self.root

        with self.busy:
            self.image_source = image_source

            self.default_threshold_val = otsu_threshold_val(image_source.read()[1])

            image_source_fps = None

            if isinstance(image_source, source_loader.LocalImages):
                image_source_fps = 2
            elif isinstance(image_source, source_loader.USBCameraSource):
                image_source_fps = None # None specifies as fast as possible

            screen_res = self.view_manager.screen_resolution
            image_source_size = self.image_source.size

            self.scale = scale_from_bounds(
                image_size=image_source_size,
                max_size=REL_SIZE_MAX * screen_res,
                min_size=REL_SIZE_MIN * screen_res
            )

            self.resize_to = (image_source_size * self.scale).round_to_int()

            # Widgets
            self.image_label = widgets.Label(root, width=self.resize_to.x, height=self.resize_to.y)
            self.image_label.pack()

            threshold_slider_frame = widgets.forms.Frame(root, padx="30", pady="10")
            threshold_slider_frame.pack(fill="both")
            threshold_slider_frame.columnconfigure(1, weight=1)

            widgets.Label(threshold_slider_frame, text="Threshold:").grid(row=0, column=0)
            self.threshold_slider = widgets.forms.Scale(threshold_slider_frame,
                from_=0,
                to=255,
                value=self.default_threshold_val
            )
            self.threshold_slider.grid(row=0, column=1, sticky="we")

        # Resizing and recentering root

        root.geometry("{0}x{1}".format(*( self.resize_to + (0, 50) )))
        self.center()

        # Root event bindings

        self.image_label.bind("<MouseWheel>", self.mouse_wheel)

        root.bind("<space>", lambda e: self.submit())
        root.bind("<Return>", lambda e: self.submit())

        root.bind("<Escape>", lambda e: self.cancel())

        # Background tasks

        self.threshold_slider.on_change(self.update_binarised_image)
        self.update_base_image_bind = self.image_source.playback(
            fps=image_source_fps,
            loop=True
        ).bind(self.update_base_image)

    # def _clear(self):
    #     self.cancel()
