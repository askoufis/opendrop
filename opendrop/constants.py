import os

from collections import namedtuple

from opendrop.utility.enums import enum

import platform

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Using namedtuples as enums

OperationMode = namedtuple("OperationMode",
    ("PENDANT", "SESSILE", "CONAN", "CONAN_NEEDLE"))(*range(4))

ImageSourceOption = namedtuple("ImageSourceOptions",
    ("FLEA3", "USB_CAMERA", "LOCAL_IMAGES")) \
    ("Flea3", "USB camera", "Local images")

# On macOS, right-button is <Button-2>, on Windows and Unix, it's <Button-3>
MOUSE_BUTTON_R = platform.system() == "Darwin" and "<Button-2>" or "<Button-3>"
