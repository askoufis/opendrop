from math import pi

def worthington(drop_density, continuous_density, needle_diameter_mm, gravity, vol_ul, ift_mn):
    """
        Calculates the Worthington number for a given set of parameters
    """

    delta_rho = drop_density - continuous_density

    worthington_number =  delta_rho * gravity * vol_ul*1e-9/(pi*ift_mn*1e-3*needle_diameter_mm*1e-3)

    return worthington_number
