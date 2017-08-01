import cv2
import numpy as np

def grayscale(image):
    """
        Takes an image currently in RGB format and uses cv2.cvtColor() to convert to GRAY, if image
        is already GRAY, returns the image unaffected.
    """
    if len(image.shape) == 3:
        if image.shape[-1] == 3: # 3 channels
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    return image

def rgb(image):
    """
        Takes an image currently in GRAY format and uses cv2.cvtColor() to convert to RGB, if image
        is already RGB, returns the image unaffected.
    """
    if len(image.shape) == 2: # Grayscale
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

    return image

def highlight_edges(image, thresh_min, thresh_max, col):
    image_edges = rgb(cv2.Canny(grayscale(image), thresh_min, thresh_max))

    image_edges = (image_edges * col) / 255

    # blend image_edges_arr on top of image_arr in an additive manner
    # first convert to int before adding to prevent overflow of uint8
    blend = image.astype(int) + image_edges.astype(int)

    return blend.clip(0, 255).astype(np.uint8)

def onionskin(images, opacity=0.3):
    unpacked_images = []

    # unpack and store in reverse order
    for image in images:
        unpacked_images.insert(0, image)

    onionskin = unpacked_images.pop(0)

    for image in unpacked_images:
        onionskin = onionskin*(1 - opacity) + image*opacity

    return onionskin.astype(np.uint8)
