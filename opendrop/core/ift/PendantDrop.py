import numpy as np

from opendrop.core.ift import calculators

from opendrop.core.ift.calculators.young_laplace import de

from opendrop.utility import comvis

from scipy import integrate

from six.moves import zip

# TODO: allow to enter gravity
GRAVITY = 9.80035 # gravitational acceleration in Melbourne, Australia

class PendantDrop(object):
    def __init__(self, needle_image, needle_diameter_measured_mm, drop_image, drop_density,
                 continuous_density):
        self.fitted = False

        # TODO: raise error when not enough edges found
        self.needle_image = needle_image

        self.needle_edges_px = comvis.detect_edges(needle_image)[:2]
        self.needle_diameter_px = calculators.needle_diameter(self.needle_edges_px)

        self.needle_diameter = needle_diameter_measured_mm

        self.pixel_to_mm = needle_diameter_measured_mm/self.needle_diameter_px

        self.drop_image = drop_image

        self.drop_contour_px = comvis.detect_edges(drop_image)[0]

        # TODO: need to fix so can convert all units to mm first but some how it fails to fit
        # when scaled down
        self.drop_contour = self.drop_contour_px # * self.pixel_to_mm

        self.drop_fit = None

        self.drop_density = drop_density
        self.continuous_density = continuous_density

    def fit(self, progress_callback=None):
        self.drop_fit = calculators.young_laplace(self.drop_contour, progress_callback)

        self.fitted = True

    def calculate_ift(self, gravity):
        if not self.fitted:
            raise ValueError(
                "Drop is not yet fitted, first call .fit() before calculating ift"
            )

        delta_rho = self.drop_density - self.continuous_density

        bond_number = self.drop_fit.bond
        apex_radius_m = self.drop_fit.apex_radius * 1e-3 * self.pixel_to_mm # 1e-3 convert mm to m

        gamma_ift_n = delta_rho * gravity * apex_radius_m**2 / bond_number

        gamma_ift_mn = gamma_ift_n * 1e3 # 1e3 convert N to mN

        return gamma_ift_mn

    def calculate_volume_and_area(self):
        if not self.fitted:
            raise ValueError(
                "Drop is not yet fitted, first call .fit() before calculating volume and area"
            )

        s_needle = max(abs(self.drop_fit.arc_lengths))
        s_data_points = np.linspace(0, s_needle, self.drop_fit.steps + 1)

        apex_radius_px = self.drop_fit.apex_radius
        bond_number = self.drop_fit.bond

        # EPS = .000001 # need to use Bessel function Taylor expansion below
        x_vec_initial = [.000001, 0., 0., 0., 0.]

        vol_sur = integrate.odeint(
            de.dataderiv, x_vec_initial, s_data_points, args=(bond_number,)
        )[-1,-2:]

        vol_sur *= [self.pixel_to_mm**3, self.pixel_to_mm**2]

        return vol_sur * [apex_radius_px**3, apex_radius_px**2]

    def draw_profile_plot(self, figure):
        profile_subplot = figure.add_subplot(1, 2, 1)
        residual_subplot = figure.add_subplot(1, 2, 2)

        profile_subplot.set_title("Profile")
        residual_subplot.set_title("Residuals")

        height, width = self.drop_image.shape[:2]

        height_mm = height * self.pixel_to_mm
        width_mm = width * self.pixel_to_mm

        extent = [0, width_mm, 0, height_mm]

        # Need to flip the image up-down since on the plot, +y is made upwards (by origin="lower")
        # where in the image, +y is downwards
        profile_subplot.imshow(np.flipud(self.drop_image), origin='lower', cmap="gray", extent=extent, aspect="equal")
        # profile_subplot.axis(extent) #, aspect=1)

        s_points = self.drop_fit.steps

        profile_line_left = profile_subplot.plot(
            np.zeros(s_points+1), np.zeros(s_points+1), "--r", linewidth = 2.0
        )[0]
        profile_line_right = profile_subplot.plot(
            np.zeros(s_points+1), np.zeros(s_points+1), "--r", linewidth = 2.0
        )[0]

        x_apex, y_apex, radius_apex, bond_number, omega_rotation = self.drop_fit.get_params()

        rotation_matrix = [
            [np.cos(omega_rotation), -np.sin(omega_rotation)],
            [np.sin(omega_rotation),  np.cos(omega_rotation)]
        ]

        reflect_rotation_matrix = np.dot([[-1, 0], [0, 1]], rotation_matrix)

        s_needle = max(abs(self.drop_fit.arc_lengths)) # ??

        def theoretical_profile(s_needle):
            delta_s = self.drop_fit.profile_size / s_points

            n_floor = int(s_needle / delta_s)

            data = np.array(self.drop_fit.theoretical_data)[:,:2]

            final_data_point = self.drop_fit.profile(s_needle)[:2]

            data[n_floor+1:] = final_data_point # trim the final data point

            return data

        profile = theoretical_profile(s_needle)

        profile_left = np.dot(profile, reflect_rotation_matrix)
        profile_right = np.dot(profile, rotation_matrix)

        # Need to +height because messy reasons to do with the axis of the data points from
        # YoungLaplaceFit
        drop_x_left = x_apex + radius_apex * profile_left[:, 0]
        drop_y_left = y_apex + radius_apex * profile_left[:, 1] + height

        drop_x_right = x_apex + radius_apex * profile_right[:, 0]
        drop_y_right = y_apex + radius_apex * profile_right[:, 1] + height

        drop_x_left *= self.pixel_to_mm
        drop_y_left *= self.pixel_to_mm
        drop_x_right *= self.pixel_to_mm
        drop_y_right *= self.pixel_to_mm

        profile_line_left.set_xdata(drop_x_left)
        profile_line_left.set_ydata(drop_y_left)

        profile_line_right.set_xdata(drop_x_right)
        profile_line_right.set_ydata(drop_y_right)

        # Make reisudal plot
        apex_x = self.drop_fit.apex_x

        x_data = np.copysign(self.drop_fit.arc_lengths, self.drop_fit.base_contour[:, 0] - apex_x)

        residual_data = residual_subplot.plot(x_data, self.drop_fit.residuals, "bo")[0]

        residual_data.axes.autoscale_view(True,True,True)
