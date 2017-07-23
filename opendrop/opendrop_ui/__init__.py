# from collections import namedtuple
# import json
#
# import threading
#
# from opendrop import VERSION
# from opendrop.conf import PREFERENCES_FILENAME
# from opendrop.resources import resources
#
# from opendrop.constants import OperationMode
#
# from opendrop.utility import coroutines
# from opendrop.utility import source_loader

from opendrop.opendrop_ui.app import App
#
# from opendrop.opendrop_ui import views
#
# OPENDROP_OP_REQUIREMENTS = {
#     OperationMode.PENDANT: {
#         "regions": 2,
#     },
#     OperationMode.SESSILE: {
#         "regions": 2,
#     },
#     OperationMode.CONAN: {
#         "regions": 1,
#     },
#     OperationMode.CONAN_NEEDLE: {
#         "regions": 1,
#     },
# }
#
# def make_preferences(form_data):
#
#     # TODO: Convert form_data to pref
#
#     pref = form_data
#
#     return pref
#
# def save_preferences(pref):
#     with open(PREFERENCES_FILENAME, "w") as pref_file:
#         json.dump(pref, pref_file, indent = 4)
#
# def load_preferences():
#     try:
#         with open(PREFERENCES_FILENAME, "r") as pref_file:
#             pref = json.load(pref_file)
#
#             return pref
#     except IOError:
#         return None
#
# def parse_preferences(pref):
#     # TODO: Convert pref to form_data
#
#     form_data = pref
#
#     return form_data
#
# @coroutines.co
# def select_regions(context, num_regions, image_source):
#     window_manager = context["window_manager"]
#
#     regions = []
#
#     for i in range(num_regions):
#         view = yield window_manager.set_view(views.SelectRegion,
#             image_source=image_source,
#         )
#
#         response = yield view.events.submit
#
#         if response:
#             regions.append(response)
#         else:
#             regions = None
#             yield None
#             yield coroutines.EXIT
#
#     yield regions
#
# @coroutines.co
# def select_threshold(context, image_source):
#     window_manager = context["window_manager"]
#
#     view = yield window_manager.set_view(views.SelectThreshold,
#         image_source=image_source
#     )
#
#     threshold_val = yield view.events.submit
#
#     yield threshold_val
#
# # Main UI flow
#
# @coroutines.co
# def entry(context):
#     #yield test(context)
#     yield main_menu(context)
#
# @coroutines.co
# def test(context):
#     view = yield context["window_manager"].set_view(views.SelectRegion, image_source_desc = 0, image_source_type = "USB camera")
#     yield view.events.blah
#
# @coroutines.co
# def main_menu(context):
#     window_manager = context["window_manager"]
#     view = yield window_manager.set_view(views.MainMenu)
#
#     @coroutines.co
#     def controller():
#         operation_mode = yield view.events.submit
#
#         context["operation_mode"] = operation_mode
#
#         yield user_input(context)
#
#     controller_co = controller()
#
#     def exit():
#         print("EXIT 1")
#         controller_co.close()
#
#     view.core_events.view_cleared.bind(exit)
#
#     yield controller_co
#
# def user_input(context):
#     window_manager = context["window_manager"]
#
#     @coroutines.co
#     def controller():
#         view = yield window_manager.set_view(views.UserInput)
#
#         # Load preferences
#         # TODO: handle if preferences are corrupted
#         pref = load_preferences()
#         pref_form = parse_preferences(pref)
#
#         # Restore preferences
#         if pref_form:
#             view.restore_form(pref_form)
#
#         # Wait for user response
#         response_form = yield view.events.submit
#
#         if response_form is None: # User cancelled, return to main menu
#             yield main_menu(context)
#             yield coroutines.EXIT
#
#         # Save preferences
#         pref = make_preferences(response_form)
#         save_preferences(pref)
#
#         # Extract image source fields from response form
#         image_source_desc = response_form["image_acquisition"]["image_source"]
#         image_source_type = response_form["image_acquisition"]["image_source_type"]
#
#         # Ask user to select threshold value and select regions
#         err = 0
#         with source_loader.load(image_source_desc, image_source_type) as image_source:
#             threshold_val = yield select_threshold(context, image_source=image_source)
#
#             if threshold_val is None:
#                 err = 1
#             else:
#                 num_regions = OPENDROP_OP_REQUIREMENTS[context["operation_mode"]]["regions"]
#
#                 regions = yield select_regions(context,
#                     num_regions,
#                     image_source=image_source,
#                 )
#
#                 if regions is None:
#                     err = 1
#
#         if err:
#             yield user_input(context)
#             yield coroutines.EXIT
#
#         # Plug to interface
#
#     reply = controller()
#
#     def exit():
#         print("EXIT 2")
#         reply(2)
#
#     window_manager.events.app_exit.bind(exit)
#
#     return reply
#
# @coroutines.co
# def user_input_old(context):
#     view = yield context["window_manager"].set_view(views.UserInput)
#
#     # Load preferences
#     # TODO: handle if preferences are corrupted
#     pref = load_preferences()
#     pref_form = parse_preferences(pref)
#
#     # Restore preferences
#     if pref_form:
#         view.restore_form(pref_form)
#
#     # Wait for user response
#     response_form = yield view.events.submit
#
#     if response_form is None: # User cancelled, return to main menu
#         yield main_menu(context)
#         yield coroutines.EXIT
#
#     # Save preferences
#     pref = make_preferences(response_form)
#     save_preferences(pref)
#
#     # Extract image source fields from response form
#     image_source_desc = response_form["image_acquisition"]["image_source"]
#     image_source_type = response_form["image_acquisition"]["image_source_type"]
#
#     # Ask user to select threshold value and select regions
#     err = 0
#     with source_loader.load(image_source_desc, image_source_type) as image_source:
#         threshold_val = yield select_threshold(context, image_source=image_source)
#
#         if threshold_val is None:
#             err = 1
#         else:
#             num_regions = OPENDROP_OP_REQUIREMENTS[context["operation_mode"]]["regions"]
#
#             regions = yield select_regions(context,
#                 num_regions,
#                 image_source=image_source,
#             )
#
#             if regions is None:
#                 err = 1
#
#     if err:
#         yield user_input(context)
#         yield coroutines.EXIT
#
#     # Plug to interface
#

# End of UI

def main():

    app = App()

    def exit_handler():
        print("Exited.")

    app.on_exit.bind(exit_handler)

    # window_manager = view_hook(ViewManager(default_title="Opendrop {}".format(VERSION)))
    #
    # exit = PersistentEvent()
    #
    # context = {"window_manager": window_manager, "exit": exit}
    #
    # def exit_handler(code):
    #     print("Exit with {}".format(code))
    #     window_manager.exit()
    #
    # exit.bind(exit_handler)
    #
    # entry(context)
    #
    # window_manager.mainloop()

if __name__ == '__main__':
    main()
