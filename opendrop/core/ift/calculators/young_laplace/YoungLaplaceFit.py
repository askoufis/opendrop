from collections import namedtuple

import itertools

from opendrop.core import tolerances

from opendrop.core.ift.calculators.fix_contour import fix_contour

from opendrop.core.ift.calculators.young_laplace import best_guess
from opendrop.core.ift.calculators.young_laplace import de
from opendrop.core.ift.calculators.young_laplace import interpolate

import math

from math import cos, sin

import numpy as np

from scipy import integrate

FITTING_STOP = namedtuple("FITTING_STOP", [
    "CONVERGENCE_IN_PARAMETERS",
    "CONVERGENCE_IN_GRADIENT",
    "CONVERGENCE_IN_OBJECTIVE",
    "MAXIMUM_STEPS_EXCEEDED",
])(1, 2, 4, 8)

def clamp(x, min_, max_):
    return max(min_, min(x, max_))

# test for convergence in parameters
def convergence_in_parameters(scaled_delta):
    max_delta = abs(scaled_delta).max()

    if max_delta < tolerances.DELTA_TOL:
        return FITTING_STOP.CONVERGENCE_IN_PARAMETERS
    else:
        return 0

# test for convergence in gradient
def convergence_in_gradient(v):
    max_gradient = abs(v).max()

    if max_gradient < tolerances.GRADIENT_TOL:
        return FITTING_STOP.CONVERGENCE_IN_GRADIENT
    else:
        return 0

# test for convergence in objective function
def convergence_in_objective(objective_function):
    if objective_function < tolerances.OBJECTIVE_TOL:
        return FITTING_STOP.CONVERGENCE_IN_OBJECTIVE
    else:
        return 0

# test maximum steps
def maximum_steps_exceeded(steps):
    if steps >= tolerances.MAXIMUM_FITTING_STEPS:
        return FITTING_STOP.MAXIMUM_STEPS_EXCEEDED
    else:
        return 0

# test whether routine has converged
def trip_flags(scaled_delta, v, objective_function, steps):
    flags  = convergence_in_parameters(scaled_delta)
    flags |= convergence_in_gradient(v)
    flags |= convergence_in_objective(objective_function)
    flags |= maximum_steps_exceeded(steps)

    return flags

# the function g(s) used in finding the arc length for the minimal distance
def f_Newton(e_r, e_z, phi, dphi_ds, RP):
    f = - (e_r * cos(phi) + e_z * sin(phi)) / (RP + dphi_ds * (e_r * sin(phi) - e_z * cos(phi)))
    return f

class YoungLaplaceFit(object):
    parameter_dimensions = 5

    def __init__(self, contour, progress_callback = None):
        contour = fix_contour(contour) # Look at fix_contour.py for an explanation
        self.base_contour = contour

        self._profile_size = None
        self._params = None
        self._steps = 200

        self.theoretical_data = None

        self.arc_lengths = None
        self.residuals = None

        self.progress_callback = progress_callback

        self.fit_contour(contour)

    # interpolates the theoretical profile data
    def profile(self, s):
        if self.theoretical_data is None:
            raise ValueError(
                "Not all parameters have been specified, profile has not yet been generated"
            )

        if s < 0:
            raise ValueError("'s' value outside domain, got {}".format(s))

        if s > self.profile_size:
            # if the profile is called outside of the current region, expand it by 20% (why 20% ??)
            self.profile_size = 1.2 * s

        step_size = self.profile_size / self.steps

        n1 = int(s / step_size)
        n2 = n1 + 1

        t = s / step_size - n1

        vec1 = np.array(self.theoretical_data[n1])
        vec2 = np.array(self.theoretical_data[n2])

        bond_number = self.bond

        dvec1 = np.array(de.ylderiv(vec1, 0, bond_number))
        dvec2 = np.array(de.ylderiv(vec2, 0, bond_number))

        value = interpolate.cubic_spline(vec1, vec2, dvec1, dvec2, step_size, t)

        return value

    # generates a new drop profile
    def update_profile(self):
        if all(v is not None for v in (self.profile_size, self.steps, self.get_params())):
            s_data_points = np.linspace(0, self.profile_size, self.steps + 1)

            # EPS = .000001 # need to use Bessel function Taylor expansion below
            x_vec_initial = [.000001, 0., 0., 0., 0., 0.]

            self.theoretical_data = integrate.odeint(de.ylderiv, x_vec_initial, s_data_points,
                                                           args=(self.bond,))
        else:
            self.theoretical_data = None

    def get_params(self):
        return self._params

    def set_params(self, new_params):
        if len(new_params) != self.parameter_dimensions:
            raise ValueError(
                "Parameter array incorrect dimensions, expected {0}, got {1}"
                .format(self.parameter_dimensions, len(new_params))
            )

        self._params = new_params

        self.update_profile() # generate new profile when the parameters are changed

    @property
    def profile_size(self):
        return self._profile_size

    @profile_size.setter
    def profile_size(self, value):
        if not value > 0:
            raise ValueError("Maximum arc length must be positive, got {}".format(value))

        self._profile_size = float(value)
        self.update_profile() # generate new profile when the maximum arc length is changed

    @property
    def steps(self):
        return self._steps

    @steps.setter
    def steps(self, value):
        if not value > 1:
            raise ValueError("Number of points must be > 1, got {}".format(value))

        if not isinstance(value, int):
            raise ValueError(
                "Number of points must be of type 'int', got '{}'".format(type(value).__name__)
            )

        self._steps = value

        self.update_profile() # generate new profile when the maximum arc length is changed

    @property
    def bond(self):
        return self.get_params()[3]

    @property
    def apex_radius(self):
        return self.get_params()[2]

    @property
    def apex_x(self):
        return self.get_params()[0]

    def guess_contour(self, contour):
        [apex_x, apex_y, apex_radius] = best_guess.fit_circle(contour)

        bond_number = best_guess.bond_number(contour, apex_x, apex_y, apex_radius)

        omega_rotation = 0.0  # initial rotation angle (TODO: should revisit this, needle angle maybe?)

        self.set_params([apex_x, apex_y, apex_radius, bond_number, omega_rotation])
        # maybe calculate_profile_size() to determine initial range - although current version can handle range being too small
        self.profile_size = 4.0 # ??

    def fit_contour(self, contour):
        self.guess_contour(contour) # Intialises parameters to a first best guess

        degrees_of_freedom = len(contour) - self.parameter_dimensions + 1

        RHO = 0.25 # ??
        SIGMA = 0.75 # ??

        lmbda = 0  # initialise value of lambda

        for step in itertools.count():
            A, v, s_new, arc_lengths, residuals = self.calculate_A_v_S(contour)

            A_plus_lambdaI = A + lmbda * np.diag(np.diag(A))

            inv = np.linalg.inv(A_plus_lambdaI)

            delta = -np.dot(inv, v).T

            if step > 0:
                R = (s_old - s_new) / (np.dot(delta, (-2 * v - np.dot(A.T, delta.T))))

                if R < RHO:
                    nu = clamp(2 - (s_new - s_old) / (np.dot(delta, v)), 2, 10)

                    if lmbda == 0:
                        lmbdaC = 1 / abs(inv).max()
                        lmbda = lmbdaC  # calculate lambda_c and set lambda
                        nu = nu / 2

                    lmbda = nu * lmbda  # rescale lambda

                if R > SIGMA:
                    if lmbda != 0:
                        lmbda /= 2
                        if lmbda < lmbdaC:
                            lmbda = 0

            if step == 0 or s_new < s_old: # if objective reduces accept (or if first run)
                self.set_params(self.get_params() + (delta)[0])

                self.arc_lengths = arc_lengths
                self.residuals = residuals

                s_old = s_new

            objective_function = s_new / degrees_of_freedom

            if self.progress_callback:
                self.progress_callback(step, objective_function, self.get_params())

            stop_flags = trip_flags(delta[0] / self.get_params(), v, objective_function, step)

            if stop_flags:
                return stop_flags

    def calculate_A_v_S(self, contour):
        num_points = len(contour)
        num_parameters = len(self.get_params())

        A = np.zeros((num_parameters, num_parameters))

        v = np.zeros((num_parameters, 1))

        S = 0.0

        arc_lengths = np.zeros(num_points)
        residuals = np.zeros(num_points)

        s_left = 0.05 * self.profile_size
        s_right = 0.05 * self.profile_size

        for i, point in enumerate(contour):
            x, y  = point

            jac_row_i, s_left, s_right, s_i, residual = self.row_jacobian(x, y, s_left, s_right) # calculate the Jacobian and residual for each point

            residuals[i] = residual
            arc_lengths[i] = s_i

            S += residual**2

            # Since 'v' is a column array, can't just do v += jac_row_i * residual_vector[i]
            v[:, 0] += jac_row_i * residual

            for j in range(0, num_parameters):
                for k in range(0, j+1):
                    A[j][k] += jac_row_i[j] * jac_row_i[k]

        # Mirror bottom triangle to top triangle
        A[np.triu_indices(num_parameters, 1)] = A.T[np.triu_indices(num_parameters, 1)]

        return A, v, S, arc_lengths, residuals

    # calculates a Jacobian row for the data point xy = x, y
    def row_jacobian(self, x, y, s_left, s_right):
        [xP, yP, RP, BP, wP] = self.get_params()

        if ((x - xP) * cos(wP) - (y - yP) * sin(wP)) < 0:
            s_0 = s_left
        else:
            s_0 = s_right

        xs, ys, dx_dBs, dy_dBs, e_r, e_z, s_i = self.minimum_arclength(x, y, s_0) # functions at s*

        next_s_left = s_left
        next_s_right = s_right

        if ((x - xP) * cos(wP) - (y - yP) * sin(wP)) < 0:
            next_s_left = s_i
        else:
            next_s_right = s_i

        e_i = math.copysign(math.sqrt(e_r**2 + e_z**2), e_r)              # actual residual
        sgnx = math.copysign(1, ((x - xP) * cos(wP) - (y - yP) * sin(wP))) # calculates the sign for ddi_dX0
        ddi_dxP = -( e_r * sgnx * cos(wP) + e_z * sin(wP) ) / e_i             # derivative w.r.t. X_0 (x at apex)
        ddi_dyP = -(-e_r * sgnx * sin(wP) + e_z * cos(wP) ) / e_i                    # derivative w.r.t. Y_0 (y at apex)
        ddi_dRP = -( e_r * xs + e_z * ys) / e_i  # derivative w.r.t. RP (apex radius)
        ddi_dBP = - RP * (e_r * dx_dBs + e_z * dy_dBs) / e_i   # derivative w.r.t. Bo  (Bond number)
        ddi_dwP = (e_r * sgnx * (- (x - xP) * sin(wP) - (y - yP) * cos(wP)) + e_z * ( (x - xP) * cos(wP) - (y - yP) * sin(wP))) / e_i

        return np.array([ ddi_dxP, ddi_dyP, ddi_dRP, ddi_dBP, ddi_dwP]), next_s_left, next_s_right, s_i, e_i

    # calculates the minimum theoretical point to the point (x,y)
    def minimum_arclength(self, x, y, s_i):
        [xP, yP, RP, BP, wP] = self.get_params() # unpack parameters

        wP_nrot = np.array([
            [cos(wP), -sin(wP)],
            [sin(wP),  cos(wP)]
        ])

        r, z = np.dot(wP_nrot, [x - xP, y - yP])

        r = abs(r)

        flag_bump = 0
        # f_i = 10000 # need to give this a more sensible value
        for step in itertools.count():
            xs, ys, phi_s, dx_dBs, dy_dBs, dphi_dBs = self.profile(s_i)

            e_r = r - RP * xs
            e_z = z - RP * ys

            #e_r = abs((x - xP) * cos(wP) - (y - yP) * sin(wP)) - RP * xs
            #e_z =    ((x - xP) * sin(wP) + (y - yP) * cos(wP)) - RP * ys

            dphi_ds = 2 - BP * ys - sin(phi_s) / xs

            s_next = s_i - f_Newton(e_r, e_z, phi_s, dphi_ds, RP)

            #f_iplus1 = RP * (e_r * cos(phi_s) + e_z * sin(phi_s))

            if s_next < 0: # arc length outside integrated region
                s_next = 0
                flag_bump += 1

            if flag_bump >= 2: # has already been pushed back twice - abort
                break

            if abs(s_next - s_i) < tolerances.ARCLENGTH_TOL:
                break

            # # this was to check if the residual was very small
            # if abs(f_iplus1 - f_i) < RESIDUAL_TOL:
            #     loop = False

            if step >= tolerances.MAXIMUM_ARCLENGTH_STEPS:
                print("'s' failed to converge in {0} steps... (s_next = {1})".format(step, s_next))
                break

            s_i = s_next

            # f_i = f_iplus1
        # drop_data.s_0 = s_i
        # drop_data.s_previous = s_i
        return xs, ys, dx_dBs, dy_dBs, e_r, e_z, s_i
