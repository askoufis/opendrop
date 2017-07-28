class DropLogger(object):
    def __init__(self, drop_class):
        self.drop_class = drop_class

        self.unfitted_drops = {}
        self.fitted_drops = {}

    def _add_drop(self, timestamp, drop):
        self.unfitted_drops[timestamp] = drop

    def add_drop_from_image(self, timestamp, drop_image, needle_image):
        new_drop = self.drop_class(drop_image, needle_image)

        self._add_drop(timestamp, new_drop)

        return new_drop

    def fit_drops(self):
        for timestamp, drop in list(self.unfitted_drops.items()):
            drop.fit()

            del self.unfitted_drops[timestamp]
            self.fitted_drops[timestamp] = drop

    def output_data(self):
        pass
