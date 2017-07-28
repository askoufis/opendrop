# Called "fillet", because this module prepares/fillet's the image to be used by core.ift

import PIL.Image

import numpy as np

import cv2

IMAGE_EXTENSION = ".png"
BLUR_SIZE = 3

def crop(image, bbox):
    return image[bbox.y0:bbox.y1, bbox.x0:bbox.x1]

def prepare(image, drop_region, needle_region, threshold_min, threshold_max=None):
    if threshold_max is None: # Only 4 arguments passed, so threshold_min not specified
        threshold_max = threshold_min
        threshold_min = 0.5 * threshold_max

    if isinstance(image, PIL.Image.Image):
        image = np.array(image)

    image = cv2.GaussianBlur(image,(BLUR_SIZE,BLUR_SIZE),0)

    image = cv2.Canny(image, threshold_min, threshold_max)

    drop_image = crop(image, drop_region)
    needle_image = crop(image, needle_region)

    return drop_image, needle_image
