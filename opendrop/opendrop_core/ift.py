from opendrop.constants import OperationMode

from opendrop.opendrop_core.classes.structs import ExperimentalSetup

from opendrop.opendrop_core import tolerances

from opendrop.opendrop_core.ift_drops.Pendant import Pendant
from opendrop.opendrop_core.ift_drops.Sessile import Sessile

IMAGE_EXTENSION = ".png"

def parse_conf(conf):
    """
        Parses conf and returns an ExperimentalSetup object
    """

    user_input = conf["user_input"]
    threshold_val = conf["threshold_val"]
    drop_region = conf["regions"][0]
    needle_region = conf["regions"][1]

    experimental_setup = ExperimentalSetup(
        drop_density=user_input["physical_inputs"]["density_inner"],
        continuous_density=user_input["physical_inputs"]["density_outer"],
        needle_diameter_mm=user_input["physical_inputs"]["needle_diameter"],
        residuals_boole=user_input["plotting_checklist"]["residuals_boole"],
        profiles_boole=user_input["plotting_checklist"]["profiles_boole"],
        physical_quantities_boole=user_input["plotting_checklist"]["physical_quantities_boole"],
        image_source_desc=user_input["image_acquisition"]["image_source_desc"],
        image_source_type=user_input["image_acquisition"]["image_source_type"],
        number_of_frames=user_input["image_acquisition"]["num_frames"],
        wait_time=user_input["image_acquisition"]["wait_time"],
        save_images_boole=user_input["image_acquisition"]["save_images"],
        create_folder_boole=user_input["image_acquisition"]["create_new_dir"],
        filename=user_input["save_location"]["filename"] or "Extracted_data" + IMAGE_EXTENSION,
        directory_string=user_input["save_location"]["directory"],
        threshold_val=threshold_val,
        drop_region=drop_region,
        needle_region=needle_region,
    )

    return experimental_setup

def calculate(mode, conf):
    experimental_setup = parse_conf(conf)

    drop = mode == OperationMode.PENDANT and Pendant() or \
           mode == OperationMode.SESSILE and Sessile()

    if mode == OperationMode.PENDANT:
        drop = Pendant()
    elif mode == OperationMode.SESSILE:
        drop = Sessile()
    else:
        raise ValueError("Unsupported mode: {}".format(mode))

    print(mode, experimental_setup, dir(tolerances), drop)
