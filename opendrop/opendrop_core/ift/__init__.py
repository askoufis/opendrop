import math

from opendrop.constants import OperationMode

from opendrop.opendrop_core.classes.structs import ExperimentalSetup

from opendrop.opendrop_core import tolerances

from opendrop.utility import coroutines
from opendrop.utility import source_loader

from opendrop.opendrop_core.ift import image_fillet

from opendrop.opendrop_core.ift.DropLogger import DropLogger
from opendrop.opendrop_core.ift.PendantDrop import PendantDrop
from opendrop.opendrop_core.ift.SessileDrop import SessileDrop

from opendrop.utility.comms import Pipe

from six.moves import zip

import threading

import cv2

IMAGE_EXTENSION = ".png"

@coroutines.co
def _main(pipe,
    drop_type,
    drop_density,
    continuous_density,
    needle_diameter,
    image_source_desc,
    image_source_type,
    num_frames,
    frame_time,
    save_images_boole,
    create_folder_boole,
    filename,
    directory_string,
    threshold_min,
    threshold_max,
    drop_region,
    needle_region
):
    drop_class = drop_type == OperationMode.PENDANT and PendantDrop or \
                 drop_type == OperationMode.SESSILE and SessileDrop

    if drop_class is False:
        raise ValueError("Unsupported mode: {}".format(mode))

    drop_logger = DropLogger(drop_class)

    print("trying to acquire camera")
    image_source = source_loader.load(image_source_desc, image_source_type)

    for i, (timestamp, image, wait_lock) in zip(range(1, num_frames + 1),
                                                image_source.frames(num_frames=num_frames,
                                                                    interval=frame_time)
                                             ):
        pipe.push("Processing frame {0} of {1}...".format(i, num_frames), name="console")
        drop_image, needle_image = image_fillet.prepare(image,
            drop_region,
            needle_region,
            threshold_min,
            threshold_max
        )

        drop = drop_logger.add_drop_from_image(timestamp, drop_image, needle_image)

        pipe.push(
            "+------+----------+----------+----------+----------+----------+----------+" "\n" \
            "| Step |  Error   | x-centre | z-centre | Apex R_0 |   Bond   | w degree |",
            name="console"
        )

        def print_fit_progress(step, objective, params):
            out = "| {0: >4d} | {1: >8.4f} | {1: >8.4f} | {1: >8.4f} | {1: >8.4f} | {1: >8.5f} " \
                  "| {1: >8.5f} |"

            x_apex, y_apex, radius_apex, bond_number, omega_rotation = params

            out = out.format(step, objective, x_apex, y_apex, radius_apex, bond_number,
                             math.degrees(omega_rotation))

            pipe.push(out, name="console")

        drop.fit(print_fit_progress)

        pipe.push("+------+----------+----------+----------+----------+----------+----------+",
                  name="console")

        yield wait_lock

    # Calculate IFT

    pipe.close()

def main(*conf):
    pipe = Pipe()

    # Drop fitting can hold up a thread, run it in new one
    threading.Thread(target=_main, args=(pipe,) + conf).start()

    return pipe

if __name__ == '__main__':
    raise NotImplementedError #main()
