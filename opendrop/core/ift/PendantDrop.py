from opendrop.core.ift import calculators
from opendrop.utility import comvis

class PendantDrop(object):
    def __init__(self, drop_image, needle_image):
        # TODO: raise error when not enough edges found

        self.drop_image = drop_image
        self.drop_contour = comvis.detect_edges(drop_image)[0]
        self.drop_fit = None

        self.needle_image = needle_image
        self.needle_edges = comvis.detect_edges(needle_image)[:2]
        self.needle_diameter_px = calculators.needle_diameter(self.needle_edges)

    def fit(self, progress_callback=None):
        self.drop_fit = calculators.young_laplace(self.drop_contour, progress_callback)
