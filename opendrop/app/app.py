import json

import matplotlib as mpl
from matplotlib import ticker

import numpy as np

from opendrop import core

from opendrop.conf import PREFERENCES_FILENAME

from opendrop.constants import ImageSourceOption, OperationMode

from opendrop.utility.events import Event, PersistentEvent

from opendrop.app import views

from opendrop.app.view_core import ViewService

from opendrop.app.view_core.devtools.view_hook import view_hook

from opendrop.utility.comms import Pipe

from opendrop.utility import coroutines
from opendrop.utility import source_loader

# Debug
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
        image_source_frame_time = user_input["image_acquisition"]["wait_time"]

        if image_source_type == ImageSourceOption.LOCAL_IMAGES:
            image_source = source_loader.load(image_source_desc, image_source_type,
                                              interval=image_source_frame_time)
        else:
            image_source = source_loader.load(image_source_desc, image_source_type)

        def release_image_source():
            if release_image_source.image_source_released is False:
                image_source.release()

                release_image_source.image_source_released = True

        release_image_source.image_source_released = False

        self.on_exit.bind_once(release_image_source)

        error = False

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
                self.context["image_source_resource"] = image_source
            else:
                error = True
        else:
            error = True

        if error:
            release_image_source()
            self.user_input()
        else:
            self.opendrop_run()

    @coroutines.co
    def opendrop_run(self):
        root = self.view_service.windows["root"]

        view = yield root.set(views.Placeholder, text="Fitting...")

        user_input = self.context["user_input"]

        drop_type = self.context["operation_mode"]

        threshold_min = self.context["threshold_min"]
        threshold_max = self.context["threshold_max"]

        regions = self.context["regions"]

        image_source = self.context["image_source_resource"]

        drop_region = regions[0]
        needle_region = regions[1]

        drop_density = user_input["physical_inputs"]["density_inner"]
        continuous_density = user_input["physical_inputs"]["density_outer"]
        needle_diameter = user_input["physical_inputs"]["needle_diameter"]
        constant_volume_boole = user_input["physical_inputs"]["constant_volume"]

        num_frames = user_input["image_acquisition"]["num_frames"]
        frame_time = user_input["image_acquisition"]["wait_time"]

        save_images_boole = user_input["image_acquisition"]["save_images"]
        create_folder_boole = user_input["image_acquisition"]["create_new_dir"]
        filename = user_input["save_location"]["filename"] or "Extracted_data" + ".png"
        directory_string = user_input["save_location"]["directory"]

        # pipe = Pipe()
        #
        # def handle_pipe(v=None):
        #     if v is not None:
        #         if v is Pipe.CLOSED:
        #             self.exit()
        #             return
        #
        #         print(v)
        #
        #     pipe.shift(name="console", blocking=True).bind_once(handle_pipe)
        #
        # handle_pipe()

        # core.ift.main(pipe,
        #     drop_type,
        #     drop_density,
        #     continuous_density,
        #     needle_diameter,
        #     image_source_desc,
        #     image_source_type,
        #     num_frames,
        #     frame_time,
        #     save_images_boole,
        #     create_folder_boole,
        #     filename,
        #     directory_string,
        #     threshold_min,
        #     threshold_max,
        #     drop_region,
        #     needle_region
        # )

        #('<opendrop.utility.comms.Pipe object at 0x10409c090>', '0', '1000.0', '0.0', '0.7176', '<opendrop.utility.source_loader.LocalImages object at 0x10834a550>', '5', '1', '50', '255', '(282, 194, 751, 723)', '(418, 26, 599, 75)')
        drop_log = core.ift.main(
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
        )

        image_source.release()

        self.context["results"] = drop_log

        self.show_output()

    @coroutines.co
    def show_output(self):
        drop_log = self.context["results"]

        df = drop_log.output_data()

        # print(df.to_string())

        physical_quants_fig = mpl.figure.Figure(
            figsize=(7, 5), tight_layout={"w_pad":0.2, "h_pad":0.2}
        )

        # When just 1 data point, set x-max to 1 instead of x min = 0, x-max = 0
        xlim=(df.index.min(), max(df.index.max(), 1))

        ift_plot = physical_quants_fig.add_subplot(3, 1, 1,
            xlabel="Time (s)", xlim=xlim,
            ylabel="Interfacial tension (mN/m)"
        )

        volume_plot = physical_quants_fig.add_subplot(3, 1, 2,
            xlabel="Time (s)", xlim=xlim,
            ylabel="Volume ("u"\u00B5""L)"
        )

        area_plot = physical_quants_fig.add_subplot(3, 1, 3,
            xlabel="Time (s)", xlim=xlim,
            ylabel="Area (mm"u"\u00B2"")"
        )

        ift_plot.plot(df.index, df["gamma_ift_mn"], "o-b")
        # ift_plot.yaxis.set_major_locator(ticker.MultipleLocator(2))
        # ift_plot.yaxis.set_minor_locator(ticker.MultipleLocator(1))

        volume_plot.plot(df.index, df["volume"], "o-r")

        area_plot.plot(df.index, df["area"], "o-g")

        drop_fit_figs = []

        for drop in drop_log.drops.values:
            drop_fit_fig = mpl.figure.Figure(tight_layout=True)

            drop.draw_profile_plot(drop_fit_fig)

            drop_fit_figs.append(drop_fit_fig)

        root = self.view_service.windows["root"]

        view = yield root.set(views.OpendropResults,
            physical_quants_fig=physical_quants_fig,
            drop_fit_figs=drop_fit_figs
        )

        #self.exit()


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
        images = ['/Users/Eugene/Documents/GitHub/opendrop/opendrop/sequence/water_in_air001.png', '/Users/Eugene/Documents/GitHub/opendrop/opendrop/sequence/water_in_air002.png', '/Users/Eugene/Documents/GitHub/opendrop/opendrop/sequence/water_in_air003.png', '/Users/Eugene/Documents/GitHub/opendrop/opendrop/sequence/water_in_air004.png', '/Users/Eugene/Documents/GitHub/opendrop/opendrop/sequence/water_in_air005.png']
        image_source = source_loader.load(images[:5], "Local images")

        pipe = Pipe()

        def handle_pipe(v=None):
            if v is not None:
                if v is Pipe.CLOSED:
                    image_source.release()
                    return

                print(v)

            pipe.shift(name="console", blocking=True).bind_once(handle_pipe)

        handle_pipe()

        results = core.ift.main(0, 1000.0, 0.0, 0.7176, image_source, 5, 1, 50, 255, BBox2(282, 194, 751, 723), BBox2(418, 26, 599, 75))
        self.context["results"] = results
        #self.exit()
        self.show_output()

    entry = main_menu #test #main_menu #test
