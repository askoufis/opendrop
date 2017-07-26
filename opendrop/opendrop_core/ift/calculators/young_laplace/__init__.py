from opendrop.opendrop_core.ift.calculators.fix_contour import fix_contour

from YoungLaplaceFit import YoungLaplaceFit

def young_laplace(contour, progress_callback=None):
    contour = fix_contour(contour) # Look at fix_contour.py for an explanation

    model = YoungLaplaceFit(contour, progress_callback)

    return model
