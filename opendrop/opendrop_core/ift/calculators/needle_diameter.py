import itertools

import numpy as np

from opendrop.opendrop_core import tolerances

from opendrop.opendrop_core.ift.calculators.fix_contour import fix_contour

from six.moves import zip

def needle_diameter(needle_profile):
    # Look at fix_contour.py for an explanation
    needle_profile = [fix_contour(edge) for edge in needle_profile]

    p0 = needle_profile[0][0]

    # Set top left point of needle_profile to (0, 0)
    needle_profile -= p0

    [x0, x1, theta] = optimise_needle(needle_profile)

    needle_diameter = abs((x1 - x0) * np.sin(theta))

    return needle_diameter

def optimise_needle(needle_profile):
    edge0 = needle_profile[0]
    edge1 = needle_profile[1]

    x0 = edge0[0][0]
    x1 = edge1[0][0]

    theta = 1.57 # TODO: PI/2 ??
    params = [x0, x1, theta]

    for step in itertools.count():
        residuals, jac = build_resids_jac(needle_profile, *params)

        jtj = np.dot(jac.T, jac)
        jte = np.dot(jac.T, residuals)

        delta = -np.dot(np.linalg.inv(jtj), jte).T

        params += delta

        if (abs(delta/params) < tolerances.NEEDLE_TOL).all() or step > tolerances.NEEDLE_STEPS:
            break

    return params

def build_resids_jac(needle_profile, x0, x1, theta):
    edge0, edge1 = needle_profile

    edge0_res, edge0_jac = edge_resids_jac(edge0, x0, theta)
    edge1_res, edge1_jac = edge_resids_jac(edge1, x1, theta)

    residuals = np.hstack((edge0_res, edge1_res))

    num_points = edge0_jac.shape[0] + edge1_jac.shape[0]

    jac = np.zeros((num_points, 3))

    jac[:len(edge0_jac), :2] = edge0_jac
    jac[len(edge0_jac):, 0] = edge1_jac[:, 0]
    jac[len(edge0_jac):, 2] = edge1_jac[:, 1]

    return [residuals, jac]

def edge_resids_jac(edge, x0, theta):
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)

    residuals = np.array([(point[0] - x0) * sin_theta - point[1] * cos_theta for point in edge])

    jac = np.array([
        [-sin_theta, (point[0] - x0) * cos_theta + point[1] * sin_theta] for point in edge
    ])

    return [residuals, jac]
