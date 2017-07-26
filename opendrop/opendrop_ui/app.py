from opendrop import opendrop_core

from opendrop.conf import PREFERENCES_FILENAME

from opendrop.constants import OperationMode

from opendrop.utility.events import Event, PersistentEvent

from opendrop.opendrop_ui import views

from opendrop.opendrop_ui.view_core import ViewService

from opendrop.opendrop_ui.view_core.devtools.view_hook import view_hook

from opendrop.utility.comms import Pipe

from opendrop.utility import coroutines
from opendrop.utility import source_loader

import json

import math

from opendrop.utility.vectors import BBox2

OPENDROP_OP_REQUIREMENTS = {
    OperationMode.PENDANT: {
        "regions": 2,
    },
    OperationMode.SESSILE: {
        "regions": 2,
    },
    OperationMode.CONAN: {
        "regions": 1,
    },
    OperationMode.CONAN_NEEDLE: {
        "regions": 1,
    },
}

class App(object):
    def __init__(self):
        # Store app state variables in context dict
        self.context = {}

        # Services
        self.view_service = ViewService()

        # Events
        self.on_exit = PersistentEvent()

        # Bindings
        self.view_service.windows["root"].on_exit_click.bind(self.exit)
        view_hook(self.view_service.windows["root"]) # DEBUG

        # Start the app
        self.entry()

        # Begin ViewService mainloop
        self.view_service.mainloop()

    @coroutines.co
    def main_menu(self):
        root = self.view_service.windows["root"]
        view = yield root.set(views.MainMenu)

        self.context["operation_mode"] = yield view.events.on_submit

        self.user_input()

    @coroutines.co
    def user_input(self):
        root = self.view_service.windows["root"]
        view = yield root.set(views.OpendropConfig)

        last_form = self.parse_preferences(self.load_preferences())

        if last_form:
            view.restore(last_form)

        user_input = yield view.events.on_submit

        if user_input:
            self.save_preferences(self.make_preferences(user_input))

            self.context["user_input"] = user_input

            self.image_source_prepare()
        else:
            self.main_menu()

    @coroutines.co
    def image_source_prepare(self):
        root = self.view_service.windows["root"]

        user_input = self.context["user_input"]

        image_source_desc = user_input["image_acquisition"]["image_source_desc"]
        image_source_type = user_input["image_acquisition"]["image_source_type"]

        image_source = source_loader.load(image_source_desc, image_source_type)

        release_resources_on_exit_bind = None
        def release_resources():
            release_resources_on_exit_bind.unbind()

            image_source.release()

        release_resources_on_exit_bind = self.on_exit.bind(release_resources)

        error = False
        try:
            view = yield root.set(views.SelectThreshold, image_source=image_source)

            thresh_vals = yield view.events.on_submit

            if thresh_vals:
                view = yield root.set(views.SelectRegion, image_source=image_source)

                num_regions = OPENDROP_OP_REQUIREMENTS[self.context["operation_mode"]]["regions"]
                regions = []

                for i in range(num_regions):
                    view.refresh()

                    region = yield view.events.on_submit

                    if region:
                        regions.append(region)
                    else:
                        break

                if len(regions) == num_regions:
                    self.context["threshold_min"] = thresh_vals[0]
                    self.context["threshold_max"] = thresh_vals[1]
                    self.context["regions"] = regions
                else:
                    error = True
            else:
                error = True
        finally:
            release_resources()

        if error:
            self.user_input()
        else:
            self.opendrop_run()

    @coroutines.co
    def opendrop_run(self):
        root = self.view_service.windows["root"]

        user_input = self.context["user_input"]

        drop_type = self.context["operation_mode"]

        threshold_min = self.context["threshold_min"]
        threshold_max = self.context["threshold_max"]

        regions = self.context["regions"]

        drop_region = regions[0]
        needle_region = regions[1]

        drop_density = user_input["physical_inputs"]["density_inner"]
        continuous_density = user_input["physical_inputs"]["density_outer"]
        needle_diameter = user_input["physical_inputs"]["needle_diameter"]

        image_source_desc = user_input["image_acquisition"]["image_source_desc"]
        image_source_type = user_input["image_acquisition"]["image_source_type"]
        num_frames = user_input["image_acquisition"]["num_frames"]
        frame_time = user_input["image_acquisition"]["wait_time"]

        save_images_boole = user_input["image_acquisition"]["save_images"]
        create_folder_boole = user_input["image_acquisition"]["create_new_dir"]
        filename = user_input["save_location"]["filename"] or "Extracted_data" + ".png"
        directory_string = user_input["save_location"]["directory"]

        pipe = opendrop_core.ift.main(
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
        )

        self.context["opendrop_pipe"] = pipe

        self.opendrop_output()

    def opendrop_output(self):
        pipe = self.context["opendrop_pipe"]

        def handle_pipe(v=None):
            if v != None:
                if v == Pipe.CLOSED:
                    return

                print(v)

            pipe.shift(name="console", blocking=True).bind_once(handle_pipe)

        handle_pipe()

        self.exit()


    def make_preferences(self, form_data):
        # TODO: Convert form_data to pref

        pref = form_data

        return pref

    def save_preferences(self, pref):
        with open(PREFERENCES_FILENAME, "w") as pref_file:
            json.dump(pref, pref_file, indent = 4)

    def load_preferences(self):
        try:
            with open(PREFERENCES_FILENAME, "r") as pref_file:
                pref = json.load(pref_file)
                return pref
        except IOError:
            return None

    def parse_preferences(self, pref):
        # TODO: Convert pref to form_data

        form_data = pref

        return form_data

    @coroutines.co
    def exit(self):
        yield self.view_service.end()
        self.on_exit.fire()

    def test(self):
        pipe = opendrop_core.ift.main(0, 0.0, 0.0, 0.0, ['/Users/Eugene/Documents/GitHub/opendrop/opendrop/test_images/water_in_air.png'], u'Local images', 1, 0, False, False, 'Extracted_data.png', u'', 35.0, 70, BBox2(250, 208, 767, 707), BBox2(369, 61, 646, 135))

        def handle_pipe(v=None):
            if v != None:
                if v == Pipe.CLOSED:
                    return

                print(v)

            pipe.shift(name="console", blocking=True).bind_once(handle_pipe)

        handle_pipe()

    entry = main_menu
