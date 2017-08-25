import math

from opendrop.constants import OperationMode

from opendrop.core.classes.structs import ExperimentalSetup

from opendrop.core import tolerances

from opendrop.utility import coroutines
from opendrop.utility import source_loader
from opendrop.utility import syringe_pump

from opendrop.core.ift import image_fillet

from opendrop.core.ift.DropLogger import DropLogger
from opendrop.core.ift.PendantDrop import PendantDrop
from opendrop.core.ift.SessileDrop import SessileDrop

from opendrop.utility.comms import Pipe

from serial import SerialException

from six.moves import zip

import cv2

import time

# TODO: allow user to input gravity
GRAVITY = 9.80035 # gravitational acceleration in Melbourne, Australia

IMAGE_EXTENSION = ".png"

def main(
    drop_type,
    drop_density,
    continuous_density,
    needle_diameter,
    constant_volume,
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

    # Only used when constant_volume is true
    previous_volume = 0
    current_volume = 0

    pump = None
    if constant_volume:
        pump = syringe_pump.SyringePump("/dev/ttyUSB0")
        pump.setDiameter(10)
        pump.setAccumUnits("UL")

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

        print("+------+----------+----------+----------+----------+----------+----------+\n")

        if constant_volume:
            # Probably want to take user input for this
            # Threshold is in micro litres
            threshold = 0.01
            # Volume is in micro litres
            volume = drop.calculate_volume_and_area()[0]
            print("Drop volume for frame {0} is {1:01.6f} uL.".format(i, volume))

            # Update both current and previous volume on the first frame
            if (i == 1):
                previous_volume = volume
                current_volume = volume
            else:
                current_volume = volume

            volume_difference = current_volume - previous_volume

            if abs(volume_difference) > threshold:
                print("Difference between current drop volume and initial is {0} uL.".format(volume_difference))

                # Volume has increased
                if volume_difference > 0:
                    pump_direction = "withdraw"

                # Volume has decreased
                elif volume_difference < 0:
                    pump_direction = "infuse"

                # We want the volume adjustment to take place in half the
                # frame time so we have some leeway
                # Rate is in micro litres per minute
                rate = 60 * (abs(volume) / (frame_time* 0.5))
                units = "MM"

                pump.setVolumeToDispense(volume_difference)

                # Diameter is specified in mm. We want user input for this.
                pump.setDirection(pump_direction)
                pump.setRate(rate, units)

                pump.run()

        time.sleep(hold_for.time_left)

    return drop_logger

if __name__ == '__main__':
    raise NotImplementedError #main()
