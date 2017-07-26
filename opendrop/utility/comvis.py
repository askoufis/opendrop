# Additional functions utilising OpenCV

import cv2
import numpy as np
import PIL.Image

# cv2.__version__ is a string of format "major.minor.patch"
# convert it to a tuple of int's (major, minor, patch)
CV2_VERSION = tuple(int(v) for v in cv2.__version__.split("."))

def detect_edges(image):
    """
        Calls cv2.findContours() on passed image in a way that is compatible with OpenCV 3.x or 2.x
        versions. Passed image is a numpy.array.

        Returns a numpy array of the countours in descending arc length order.
    """

    if CV2_VERSION >= (3, 2, 0):
        # In OpenCV 3.2, cv2.findContours() does not modify the passed image and instead returns the
        # modified image as the first, of the three, return values.
        _, contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    else:
        contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # Each contour has shape (n, 1, 2) where 'n' is the number of points. Presumably this is so each
    # point is a size 2 column vector, we don't want this so reshape it to a (n, 2)
    contours = [contour.reshape(contour.shape[0], 2) for contour in contours]

    # Sort the contours by arc length, descending order
    contours.sort(key=lambda c: cv2.arcLength(c, False), reverse=True)

    return contours

def otsu_threshold_val(image):
    """
        Takes in an image argument (can be np.array or PIL.Image) and uses OpenCV to calculate the
        otsu threshold and returns this value.
    """

    if isinstance(image, np.ndarray):
        image = PIL.Image.fromarray(image)
    elif isinstance(image, PIL.Image.Image):
        pass # Do nothing, function expects image to be a PIL.Image
    else:
        raise TypeError("Unsupported type '{}'".format(type(image).__name__))

    image_gray = image.convert("L")
    image_array_gray = np.array(image_gray)
    thresh_val, image_array_binarised = cv2.threshold(image_array_gray, 127, 255,
                                                      cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    return thresh_val
