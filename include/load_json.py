import numpy as np
import json
import matplotlib.pyplot as plt
import os, sys
import FittingRoutine as fit
import time

from load import *

# Plotting preample
major = 6
minor = 3
width = 1
plt.rc('text', usetex=True)
plt.rc('text.latex', preamble=r'\usepackage{amsmath}')
plt.rc("axes", labelsize=14)  # 18
plt.rc("xtick", labelsize=12, top=True, direction="in")
plt.rc("ytick", labelsize=12, right=True, direction="in")
plt.rc("axes", titlesize=16)
plt.rc("legend", fontsize=14)
plt.rcParams['font.family'] = "serif"
plt.rcParams['axes.linewidth'] = width
plt.rcParams['xtick.minor.width'] = width
plt.rcParams['xtick.major.width'] = width
plt.rcParams['ytick.minor.width'] = width
plt.rcParams['ytick.major.width'] = width
plt.rcParams['xtick.major.size'] = major
plt.rcParams['xtick.minor.size'] = minor
plt.rcParams['ytick.major.size'] = major
plt.rcParams['ytick.minor.size'] = minor
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=["b", "r", "k", "grey", "magenta", "b", "r", "k", "grey", "magenta"],
                                             ls=["-", "-", "-", "-", "-", "--", "--", "--", "--", "--"])

def print_keys_in_dict(dict):
    for key in dict.keys():
        print(key, end='\t')
    print('')

if __name__ == '__main__':
    # Directories
    run_folder = '/media/nikolaj/C567-413B/Nikolaj/PhotonIntensity/Raw_Data/'
    write_folder = '/media/nikolaj/C567-413B/Nikolaj/PhotonIntensity/JSON_Data/'
    
    master = 150 # ms
    triggers = 300
    
    time_window = 7000
    
    coinc_keys = ['TDC1.U_B','TDC1.D_B']
    
    # Runs and energies to analyze
    runs = []
    for i in range(262,269): #20,23
        runs.append(str(i))
    
    overwrite_data = True
    
    # Loop over runs to ensure they exist.
    for run in runs:
        # Load the needed keys
        e_run = run_folder+'Run-'+run
        e_write = write_folder+'Run-'+run
        load_data(e_run, write_folder=e_write, overwrite=overwrite_data, nr_triggers=triggers, proc_time=master, coinc_keys=[coinc_keys], time_window=time_window)
    
