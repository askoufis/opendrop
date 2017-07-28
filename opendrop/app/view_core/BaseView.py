from opendrop.utility.events import PersistentEvent, EventsManager
from opendrop.utility.structs import Struct

import threading

class BaseView(object):
    TITLE = ""

    def __init__(self, window_manager, passthrough_kwargs):

        self.window_manager = window_manager
        self.top_level = window_manager.top_level
        self.alive = True
        self.busy = threading.Lock()

        self.events = EventsManager()
        self.core_events = EventsManager({
            "on_clear": PersistentEvent()
        })

        self.body(**passthrough_kwargs)
        
        self.top_level.update_idletasks()

    def body(self):
        # build the window
        pass

    def clear(self):
        # Wait to acquire busy lock, don't block since .clear() could be running on the main thread
        # where the Tk .mainloop() is also running on, if the main thread is blocked, program could
        # become unresponsive
        if self.busy.acquire(False) is False:
            self.top_level.after(0, self.clear)
            return

        # Do view specific clear
        self._clear()

        self.events.unbind_all()

        for child in self.top_level.winfo_children():
            child.destroy()

        self.top_level.update_idletasks()

        self.alive = False
        self.busy.release()

        self.core_events.on_clear.fire()

        self.core_events.unbind_all()

    def _clear(self):
        pass

    def center(self):
        self.top_level.update_idletasks()

        screen_w, screen_h = self.window_manager.screen_resolution
        window_w, window_h = self.top_level.winfo_width(), self.top_level.winfo_height()

        x = screen_w/2 - window_w/2
        y = screen_h/2 - window_h/2
        self.top_level.geometry("{0}x{1}+{2}+{3}".format(window_w, window_h, x, y))
