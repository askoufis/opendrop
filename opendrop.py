#!/usr/bin/env python
#coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function
# from modules.classes import ExperimentalDrop, DropData, Tolerances
# from modules.static_setup_class import ExperimentalSetup
# # from modules.ui import initialise_ui
# from modules.user_interface import call_user_input
# # from modules.load import load_data
# from modules.extract_data import extract_drop_profile
# from modules.initialise_parameters import initialise_parameters
# # from modules.fit_data import fit_raw_experiment
# # from modules.user_set_regions


from modules.classes import ExperimentalSetup, ExperimentalDrop, DropData, Tolerances
from modules.PlotManager import PlotManager
from modules.ExtractData import ExtractedData
import modules.syringe_pump

from modules.user_interface import call_user_input
from modules.read_image import get_image
from modules.select_regions import set_regions
from modules.extract_profile import extract_drop_profile
from modules.initialise_parameters import initialise_parameters
from modules.analyse_needle import calculate_needle_diameter
from modules.fit_data import fit_experimental_drop
from modules.generate_data import generate_full_data
# from modules. import add_data_to_lists



import os
import numpy as np
import Tkinter as tk
import tkFont

import timeit
import time

np.set_printoptions(suppress=True)
np.set_printoptions(precision=3)

DELTA_TOL = 1.e-6
GRADIENT_TOL = 1.e-6
MAXIMUM_FITTING_STEPS = 10
OBJECTIVE_TOL = 1.e-4
ARCLENGTH_TOL = 1.e-6
MAXIMUM_ARCLENGTH_STEPS = 10
NEEDLE_TOL = 1.e-4
NEEDLE_STEPS = 20



def main():
    clear_screen()
    fitted_drop_data = DropData()
    tolerances = Tolerances(
        DELTA_TOL,
        GRADIENT_TOL,
        MAXIMUM_FITTING_STEPS,
        OBJECTIVE_TOL,
        ARCLENGTH_TOL,
        MAXIMUM_ARCLENGTH_STEPS,
        NEEDLE_TOL,
        NEEDLE_STEPS)
    user_inputs = ExperimentalSetup()
    call_user_input(user_inputs)

    n_frames = user_inputs.number_of_frames
    extracted_data = ExtractedData(n_frames, fitted_drop_data.parameter_dimensions)
    raw_experiment = ExperimentalDrop()

    if user_inputs.interfacial_tension_boole:
        plots = PlotManager(user_inputs.wait_time, n_frames)

    get_image(raw_experiment, user_inputs, -1)
    set_regions(raw_experiment, user_inputs)

    initial_volume = 0
    current_volume = 0

    # Probably want to take user input for this
    # Threshold is in micro litres
    threshold = 0.01
    pump = None

    if (n_frames > 1):
        pump = syringe_pump.SyringePump("/dev/ttyUSB0")
        # Diameter is in mm. We want user input for this too at some point.
        pump.setDiameter(10)
        # Accumulator units are dependent on the diameter value given, so we'll
        # force it to be uL for now.
        pump.setAccumUnits("UL")

    for i in range(n_frames):
        print("\nProcessing frame %d of %d..." % (i+1, n_frames))
        time_start = timeit.default_timer()
        raw_experiment = ExperimentalDrop()
        get_image(raw_experiment, user_inputs, i) # save image in here...
        extract_drop_profile(raw_experiment, user_inputs)

        # On the first frame only
        if i == 0:
            extracted_data.initial_image_time = raw_experiment.time
            filename = user_inputs.filename[:-4] + '_' + user_inputs.time_string + ".csv"
            export_filename = os.path.join(user_inputs.directory_string, filename)
        initialise_parameters(raw_experiment, fitted_drop_data)
        calculate_needle_diameter(raw_experiment, fitted_drop_data, tolerances)
        # fit_experimental_drop(raw_experiment, fitted_drop_data, tolerances)
        fit_experimental_drop(raw_experiment, fitted_drop_data, user_inputs, tolerances)
        generate_full_data(extracted_data, raw_experiment, fitted_drop_data, user_inputs, i)
        data_vector = extracted_data.time_IFT_vol_area(i)

        # Volume is in micro litres
        if user_inputs.constant_volume_boole:
            volume = data_vector.area[i]
            print("Drop volume for frame {0} is {1:01.6f} uL.".format(i, volume))

            if i == 0:
                initial_volume = volume
                current_volume = volume
            else:
                current_volume = volume

            volume_difference = initial_volume - current_volume

            if abs(volume_difference) > threshold:
                print("Difference between current drop volume and initial is {0} uL.".format(volume_difference))

                # If the volume has increased
                if volume_difference > 0:
                    pump_direction = "withdraw"

                # If the volume has decreased
                elif volume_difference < 0:
                    pump_direction = "infuse"

                # We want the volume adjustment to take place in half the
                # frame time so we have some leeway
                rate = 60 * (abs(volume) / (int(user_inputs.wait_time) * 1.5))
                # Rate is in micro litres per minute
                units = "MM"

                # This makes the pump automatically stop after the desired
                # volume has been dispensed
                pump.setVolumeToDispense(volume_difference)

                pump.setDirection(pump_direction)
                pump.setRate(rate, units)

                pump.run()

        if user_inputs.interfacial_tension_boole:
            plots.append_data_plot(data_vector, i)

        if i != (n_frames - 1):
            time_loop = timeit.default_timer() - time_start
            pause_wait_time(time_loop, user_inputs.wait_time)

        extracted_data.export_data(export_filename,i)
#    cheeky_pause()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause_wait_time(elapsed_time, requested_time):
    if elapsed_time > requested_time:
        print('WARNING: Fitting took longer than desired wait time')
    else:
        time.sleep(requested_time - elapsed_time)

def cheeky_pause():
    import Tkinter
    import tkMessageBox
    import cv2
    #    cv2.namedWindow("Pause")
    #    while 1:
    #        k = cv2.waitKey(1) & 0xFF
    #        if (k==27):
    #            break
    #root = Tkinter.Tk()
    #    B = Tkinter.Button(top, text="Exit",command = cv2.destroyAllWindows())
    #    B = Tkinter.Button(root, text="Exit",command = root.destroy())
    #
    #    B.pack()
    #    root.mainloop()

    root = Tkinter.Tk()
    frame = Tkinter.Frame(root)
    frame.pack()

    button = Tkinter.Button(frame)
    button['text'] ="Good-bye."
    button['command'] = root.destroy()#close_window(root)
    button.pack()

    root.mainloop()

def quit_(root):
    root.quit()

#def close_window(root):
#    root.destroy()


if __name__ == '__main__':
    main()
    root = tk.Tk()
    # quit button
    buttonFont = tkFont.Font(family='Helvetica', size=48, weight='bold') #This isn't working for some reason (??)
    quit_button = tk.Button(master=root, font=buttonFont,text='Quit',height=4,width=15,
                            command=lambda: quit_(root),bg='blue',fg='white',activeforeground='white',activebackground='red')
    quit_button.pack()
    root.mainloop()
