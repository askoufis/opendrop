from opendrop.constants import ImageSourceOption

from opendrop.opendrop_ui.view_manager import View
from opendrop.opendrop_ui.views.utility.scale_from_bounds import scale_from_bounds

import opendrop.utility.source_loader as source_loader
from opendrop.utility.vectors import Vector2

import cv2
from opendrop.shims import tkinter_ as tk
from PIL import Image, ImageTk

WIDTH_MIN, WIDTH_MAX = 0.4, 0.5
HEIGHT_MIN, HEIGHT_MAX = 0.4, 0.5

REL_SIZE_MIN = Vector2(WIDTH_MIN, HEIGHT_MIN)
REL_SIZE_MAX = Vector2(WIDTH_MAX, HEIGHT_MAX)

DEFAULT_THRESHOLD = 40
MAX_THRESHOLD = 255


class SelectThreshold(View):
    def submit(self):
        self.events.submit(float(self.slider.get()))

    def cancel(self):
        self.events.submit(None)

    def set_image_source(self, image_source_desc, image_source_type):
        if image_source_type == ImageSourceOption.LOCAL_IMAGES:
            self.image_source = source_loader.load(image_source_desc, image_source_type)
        elif image_source_type == ImageSourceOption.USB_CAMERA:
            raise NotImplementedError("USBCamera not supported yet")
        elif image_source_type == ImageSourceOption.FLEA3:
            raise NotImplementedError("Flea3 not supported yet")

        screen_res = self.view_manager.screen_resolution
        image_source_size = self.image_source.size

        scale = scale_from_bounds(
            image_size = image_source_size,
            max_size = REL_SIZE_MAX * screen_res,
            min_size = REL_SIZE_MIN * screen_res
        )

        self.resize_to = (image_source_size * scale).round_to_int()

    def update_frame(self, slider_val):
        _, new = cv2.threshold(self.cv_image_resized, float(slider_val), MAX_THRESHOLD, cv2.THRESH_BINARY)
        self.tk_img = ImageTk.PhotoImage(image=Image.fromarray(new))
        self.display.configure(image=self.tk_img)

    def body(self, image_source_desc, image_source_type):
        root = self.root

        self.set_image_source(image_source_desc, image_source_type)

        cv_image = cv2.imread(self.image_source.filenames[0], cv2.IMREAD_GRAYSCALE)
        self.cv_image_resized = cv2.resize(cv_image, (self.resize_to.x, self.resize_to.y), cv2.INTER_LINEAR)

        self.image_frame = tk.Frame(root, width=self.resize_to[0], height=self.resize_to[1])
        self.image_frame.grid(row=0, column=0)

        _, default = cv2.threshold(self.cv_image_resized, DEFAULT_THRESHOLD, MAX_THRESHOLD, cv2.THRESH_BINARY)
        self.tk_img = ImageTk.PhotoImage(image=Image.fromarray(default))

        self.display = tk.Label(self.image_frame, image=self.tk_img)
        self.display.grid(row=0, column=0)

        self.slider = tk.Scale(root, to=MAX_THRESHOLD, orient=tk.HORIZONTAL, command=self.update_frame, length=self.resize_to.x - 10)
        self.slider.set(DEFAULT_THRESHOLD)
        self.slider.grid(column=0,row=1)

        root.geometry("%dx%d"%(self.resize_to.x, self.resize_to.y + 50))
        root.resizable(width=False, height=False)
        self.center()

        root.bind("<space>", lambda e: self.submit())
        root.bind("<Return>", lambda e: self.submit())
        root.bind("<Escape>", lambda e: self.cancel())

    def _clear(self):
        self.image_source.release()
