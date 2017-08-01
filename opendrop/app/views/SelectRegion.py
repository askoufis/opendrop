import numpy as np

from opendrop.constants import ImageSourceOption, MOUSE_BUTTON_R

from opendrop.app import widgets
from opendrop.app.view_core import BaseView
from opendrop.app.views.utility.scale_from_bounds import scale_from_bounds

from opendrop.resources import resources

from opendrop.shims import tkinter as tk

from opendrop.utility import coroutines
from opendrop.utility import image_tools
from opendrop.utility import source_loader
from opendrop.utility.vectors import Vector2, BBox2

from PIL import Image, ImageTk

widgets = widgets.preconfigure({
    "forms": {
        "RegionSelector": {
            "box_bd": "#00ff7f",
            "box_active_bd": "#ff4040",
            "box_bd_width": 2,
        }
    }
})

WIDTH_MIN, WIDTH_MAX = 0.4, 0.5
HEIGHT_MIN, HEIGHT_MAX = 0.4, 0.5

REL_SIZE_MIN = Vector2(WIDTH_MIN, HEIGHT_MIN)
REL_SIZE_MAX = Vector2(WIDTH_MAX, HEIGHT_MAX)

class SelectRegion(BaseView):
    TITLE = "Select regions"

    def submit(self):
        region = self.selector.value

        if not region.size == (0, 0):
            region = (region / self.scale).round_to_int()

            self.events.on_submit.fire(region)

    def cancel(self):
        self.events.on_submit.fire(None)

    def update_image_loop(self, frames_gen):
        if self.alive:
            try:
                timestamp, image, hold_for = next(frames_gen)

                self.update_image(image)

                self.top_level.after(int(hold_for.time_left*1000) or 1,
                    self.update_image_loop, frames
                )
            except StopIteration:
                pass

    def update_image(self, image):
        image = image.resize(self.resize_to, resample=Image.BILINEAR)

        image_tk = ImageTk.PhotoImage(image)

        self.selector.configure(image=image_tk)

    def body(self, image_source): #image_source_desc, image_source_type):
        top_level = self.top_level

        with self.busy:
            screen_res = self.window_manager.screen_resolution

            self.scale = scale_from_bounds(
                image_size=image_source.size,
                max_size=REL_SIZE_MAX * screen_res,
                min_size=REL_SIZE_MIN * screen_res
            )

            self.resize_to = (image_source.size * self.scale).round_to_int()

            # Widgets

            self.selector = widgets.forms.RegionSelector(top_level, size = self.resize_to)
            self.selector.pack()

        # Resizing and recentering top_level

        top_level.geometry("{0}x{1}".format(*self.resize_to))
        self.center()

        # top_level event bindings

        top_level.bind("<space>", lambda e: self.submit())
        top_level.bind("<Return>", lambda e: self.submit())
        top_level.bind(MOUSE_BUTTON_R, lambda e: self.submit())

        top_level.bind("<Escape>", lambda e: self.cancel())

        # Preview image update background tasks

        if isinstance(image_source, source_loader.LocalImages):
            onionskin = image_tools.onionskin(np.array(im) for t, im, w in image_source.frames())

            onionskin = Image.fromarray(onionskin)

            self.update_image(onionskin)
        elif isinstance(image_source, source_loader.USBCameraSource):
            # fps=-1 specifies as fast as possible playback
            frames_gen = iter(image_source.frames(fps=-1, loop=True))

            self.update_image_loop(frames_gen)

    # def _clear(self):
    #     self.image_source.release()

    def refresh(self):
        self.selector.value = BBox2()
