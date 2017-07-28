from opendrop.core.ift import calculators

import pandas as pd

class DropLogger(object):
    def __init__(self, drop_class, drop_density, continuous_density, needle_diameter_measured_mm,
                 gravity):
        # Drop characteristics
        self.drop_class = drop_class

        self.drop_density = drop_density
        self.continuous_density = continuous_density
        self.needle_diameter_measured_mm = needle_diameter_measured_mm

        # Gravity
        self.gravity = gravity

        self.drops = {}

    def _add_drop(self, timestamp, drop):
        self.drops[timestamp] = drop

    def add_drop_from_image(self, timestamp, needle_image, drop_image):
        new_drop = self.drop_class(needle_image, self.needle_diameter_measured_mm,
                                   drop_image, self.drop_density, self.continuous_density)

        self._add_drop(timestamp, new_drop)

        return new_drop

    def output_data(self):
        columns = ["gamma_ift_mn", "pixel_to_mm", "volume", "area", "worthington", "params"]

        index = []
        data = {column: [] for column in columns}

        for timestamp, drop in self.drops.items():
            if not drop.fitted:
                print(
                    "[WARNING] drop (timestamp={}s) not fitted, ommitting from output"
                    .format(timestamp)
                )

            gamma_ift_mn = drop.calculate_ift(self.gravity)

            pixel_to_mm = drop.pixel_to_mm

            volume, area = drop.calculate_volume_and_area()

            worthington = calculators.worthington(
                drop.drop_density,
                drop.continuous_density,
                drop.needle_diameter,
                self.gravity,
                volume,
                gamma_ift_mn
            )

            index.append(timestamp)

            data["gamma_ift_mn"].append(gamma_ift_mn)
            data["pixel_to_mm"].append(pixel_to_mm)
            data["volume"].append(volume)
            data["area"].append(area)
            data["worthington"].append(worthington)
            data["params"].append(drop.drop_fit.get_params())

        df = pd.DataFrame(
            data=data,
            index=pd.Index(index, name="timestamp")
        )

        # Make sure index is sorted in ascending order
        df.sort_index(inplace=True)

        return df
