from opendrop.utility.structs import Struct

class ExperimentalSetup(Struct):
    attributes = (
        "drop_density",
        "continuous_density",
        "needle_diameter_mm",
        "residuals_boole",
        "profiles_boole",
        "physical_quantities_boole",
        "image_source_desc",
        "image_source_type",
        "number_of_frames",
        "wait_time",
        "save_images_boole",
        "create_folder_boole",
        "filename",
        "directory_string",
        "time_string",
        "local_files",
        "threshold_val",
        "drop_region",
        "needle_region",
    )

    default = None
