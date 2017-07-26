from opendrop.utility import coroutines

from opendrop.utility.events import Event

from opendrop.opendrop_ui.view_core.ResolutionTuple import ResolutionTuple

class WindowManager(object):
    def __init__(self, top_level):
        self.top_level = top_level

        self.current_view = None

        # Events
        self.on_view_change = Event()
        self.on_exit_click = Event()

        # Protocol bindings
        self.top_level.protocol("WM_DELETE_WINDOW", self.on_exit_click.fire)

    @coroutines.co
    def set(self, view_cls, **passthrough_kwargs):
        yield self.clear(silent = True)

        new_view = view_cls(self, passthrough_kwargs)

        self.top_level.title(new_view.TITLE)

        self.current_view = new_view

        self.on_view_change.fire(new_view)

        yield new_view

    @coroutines.co
    def clear(self, silent = False):
        if self.current_view:
            self.current_view.clear()
            # Wait until view is cleared
            yield self.current_view.core_events.on_clear

        self.current_view = None

        if not silent:
            self.on_view_change.fire(None)

        self.reset()

    def reset(self):
        self.top_level.configure(padx=0, pady=0)

    @property
    def screen_resolution(self):
        return ResolutionTuple(self.top_level.winfo_screenwidth(), self.top_level.winfo_screenheight())
