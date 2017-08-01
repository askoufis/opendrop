from opendrop.constants import ImageSourceOption, MOUSE_BUTTON_R

from opendrop.app import widgets
from opendrop.app.view_core import BaseView
from opendrop.app.views.utility.scale_from_bounds import scale_from_bounds

from opendrop.resources import resources

from opendrop.shims import tkinter as tk

from opendrop.utility import coroutines
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

    def update_image(self):
        if self.alive:
            try:
                timestamp, image, hold_for = next(self.image_source_frames)

                resized_image = image.resize(self.resize_to, resample=Image.BILINEAR)
                image_tk = ImageTk.PhotoImage(resized_image)

                self.selector.configure(image=image_tk)

                # tk.Widget.after(delay_ms(int), ...)
                self.top_level.after(int(hold_for.time_left*1000) or 1, self.update_image)
            except StopIteration:
                pass

    def body(self, image_source): #image_source_desc, image_source_type):
        top_level = self.top_level

        with self.busy:
            self.image_source = image_source

            image_source_fps = None

            if isinstance(image_source, source_loader.LocalImages):
                # TODO: instead of cycling the images, add some kind of onion layer effect thingy
                image_source_fps = 2
            elif isinstance(image_source, source_loader.USBCameraSource):
                image_source_fps = -1 # None specifies as fast as possible

            screen_res = self.window_manager.screen_resolution
            image_source_size = self.image_source.size

            self.scale = scale_from_bounds(
                image_size=image_source_size,
                max_size=REL_SIZE_MAX * screen_res,
                min_size=REL_SIZE_MIN * screen_res
            )

            self.resize_to = (image_source_size * self.scale).round_to_int()

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

        # Background tasks

        self.image_source_frames = iter(self.image_source.frames(fps=image_source_fps, loop=True))
        self.update_image()

    # def _clear(self):
    #     self.image_source.release()

    def refresh(self):
        self.selector.value = BBox2()
