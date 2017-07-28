# Uhh, contour needs to have +y axis upwards instead of downwards and points need to be ordered in
# order of increasing y-value for the fitting functions to work. I'm not sure why..
def fix_contour(contour):
    contour = contour.copy()

    contour[:, 1] *= -1

    contour = contour[contour[:, 1].argsort()]

    return contour
