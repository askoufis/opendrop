# Uhh, contour needs to have +y axis upwards instead of downwards and points need to be ordered in
# order of increasing y-value for the fitting functions to work. I'm not sure why..
def fix_contour(contour):
    contour = contour.copy()

    height = contour[:, 1].max()
    contour[:, 1] = height - contour[:, 1]

    contour = contour[contour[:, 1].argsort()]

    return contour
