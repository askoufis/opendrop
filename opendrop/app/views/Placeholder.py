from opendrop.app.view_core import BaseView
from opendrop.app import widgets

class Placeholder(BaseView):
    TITLE = "Placeholder"

    def body(self, text="Hello, world"):
        top_level = self.top_level

        top_level.geometry("200x100")

        self.center()

        widgets.Label(text=text, font=("Helvetica", "16"), background="white") \
            .pack(expand=True, fill="both")
