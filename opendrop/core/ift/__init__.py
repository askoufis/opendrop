import math

from opendrop.constants import OperationMode

from opendrop.core.classes.structs import ExperimentalSetup

from opendrop.core import tolerances

from opendrop.utility import coroutines
from opendrop.utility import source_loader

from opendrop.core.ift import image_fillet

from opendrop.core.ift.DropLogger import DropLogger
from opendrop.core.ift.PendantDrop import PendantDrop
from opendrop.core.ift.SessileDrop import SessileDrop

from opendrop.utility.comms import Pipe

from six.moves import zip

import cv2

import time

from matplotlib import pyplot as plt

# TODO: allow user to input gravity
GRAVITY = 9.80035 # gravitational acceleration in Melbourne, Australia

IMAGE_EXTENSION = ".png"

def main(
    drop_type,
    drop_density,
    continuous_density,
    needle_diameter,
    image_source,
    num_frames,
    frame_time,
    threshold_min,
    threshold_max,
    drop_region,
    needle_region
):
    drop_class = drop_type == OperationMode.PENDANT and PendantDrop or \
                 drop_type == OperationMode.SESSILE and SessileDrop

    if drop_class is False:
        raise ValueError("Unsupported mode: {}".format(drop_type))

    drop_logger = DropLogger(drop_class, drop_density, continuous_density, needle_diameter, GRAVITY)

    for i, (timestamp, image, hold_for) in zip(range(1, num_frames + 1),
                                               image_source.frames(num_frames=num_frames,
                                                                   interval=frame_time)
                                              ):
        print(
            "Processing frame {0} of {1}... (timestamp = {2:.2f}s)".format(i, num_frames, timestamp)
        )

        needle_image, drop_image = image_fillet.prepare(image,
            drop_region,
            needle_region,
            threshold_min,
            threshold_max
        )

        drop = drop_logger.add_drop_from_image(timestamp, needle_image, drop_image)

        print(
            "+------+----------+----------+----------+----------+----------+----------+" "\n" \
            "| Step |  Error   | x-centre | z-centre | Apex R_0 |   Bond   | w degree |"
        )

        def print_fit_progress(step, objective, params):
            out = "| {0: >4d} | {1: >8.4f} | {1: >8.4f} | {1: >8.4f} | {1: >8.4f} | {1: >8.5f} " \
                  "| {1: >8.5f} |"

            x_apex, y_apex, radius_apex, bond_number, omega_rotation = params

            out = out.format(step, objective, x_apex, y_apex, radius_apex, bond_number,
                             math.degrees(omega_rotation))

            print(out)

        drop.fit(print_fit_progress)

        # Debug
        drop.draw_profile_plot(plt.figure())

        print("+------+----------+----------+----------+----------+----------+----------+\n")

        time.sleep(hold_for.time_left)

    return drop_logger

if __name__ == '__main__':
    raise NotImplementedError #main()
