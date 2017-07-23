from opendrop import opendrop_core

from opendrop.conf import PREFERENCES_FILENAME

from opendrop.constants import OperationMode

from opendrop.utility.events import Event, PersistentEvent

from opendrop.opendrop_ui import views

from opendrop.opendrop_ui.view_core import ViewService

from opendrop.opendrop_ui.view_core.devtools.view_hook import view_hook

from opendrop.utility import coroutines
from opendrop.utility import source_loader

import json

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

        # Present the main menu to the user
        self.main_menu()

        # Begin ViewService mainloop
        self.view_service.mainloop()

    @coroutines.co
    def exit(self):
        yield self.view_service.end()
        self.on_exit.fire()

    @coroutines.co
    def main_menu(self):
        root = self.view_service.windows["root"]
        view = yield root.set(views.MainMenu)

        self.context["operation_mode"] = yield view.events.on_submit

        self.user_input()

    @coroutines.co
    def user_input(self):
        root = self.view_service.windows["root"]
        view = yield root.set(views.UserInput)

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

        try:
            view = yield root.set(views.SelectThreshold, image_source=image_source)

            threshold_val = yield view.events.on_submit

            if threshold_val:
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
                    self.context["threshold_val"] = threshold_val
                    self.context["regions"] = regions

                    self.opendrop_results()
                else:
                    self.user_input()
            else:
                self.user_input()
        finally:
            release_resources()

    @coroutines.co
    def opendrop_results(self):
        print(self.context)

        mode = self.context["operation_mode"]
        conf = {
            "user_input": self.context["user_input"],
            "threshold_val": self.context["threshold_val"],
            "regions": self.context["regions"]
        }

        opendrop_core.main(mode, conf)

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
