from YoungLaplaceFit import YoungLaplaceFit

def young_laplace(contour, progress_callback=None):
    model = YoungLaplaceFit(contour, progress_callback)

    return model
