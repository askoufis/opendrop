from opendrop.app.view_core import BaseView
from opendrop.app import widgets

class HelloWorld(BaseView):
    TITLE = "Hello, world"

    def body(self):
        top_level = self.top_level

        top_level.geometry("200x100")

        self.center()

        widgets.Label(text = "Hello, world", font = ("Helvetica", "16"), background = "white") \
            .pack(expand = True, fill = "both")
