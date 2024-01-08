import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import constants
from PIL import Image, ImageTk
import numpy as np
from threading import Thread
import traceback
from inspect import signature
from inspect import getfullargspec
from include.FittingRoutine import FittingRoutine

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

from include.control_frames.command_frames.settings_frame import *
from include.control_frames.command_frames.plot_opt_frame import *
from include.control_frames.command_frames.results_frame import *
from include.control_frames.command_frames.status_frame import *

class command_frame(ttk.Frame):
    def __init__(self, container, root):
        super().__init__(container)

        options = {'padx': 5, 'pady': 5}

        # Label frames
        self.settingsframe = settings_frame(self, root, text="Settings")
        self.settingsframe.grid(**options, column = 0, row = 0, sticky=tk.N+tk.W+tk.E)
        
        self.plotoptframe = plot_opt_frame(self, root, text="Plot options")
        self.plotoptframe.grid(**options, column = 0, row = 1, sticky=tk.W+tk.E)
        
        self.results = results_frame(self, root, text="Results")
        self.results.grid(**options, column = 0, row = 2, sticky=tk.W+tk.E)
        self.results.load_settings_menu()
        
        self.status = status_frame(self, root, text="Status")
        self.status.grid(**options, column = 0, row = 3, sticky=tk.S+tk.W+tk.E)

        # show the frame on the container
        self.grid(**options, row=0, column=0, sticky=tk.N+tk.E+tk.W+tk.S)

        self.bind('<Configure>', self.resize)

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        # place the window, giving it an explicit size
        self.settingsframe.place(in_=self, relx=padx, rely=pady, 
            relwidth=1 - 2 * padx, relheight=3/7- 2 * pady)
        
        self.plotoptframe.place(in_=self, relx=padx, rely=3/7+pady,
            relwidth=1- 2 * padx, relheight=1/7- 2 * pady)
        
        self.results.place(in_=self, relx=padx, rely=4/7+pady,
            relwidth=1- 2 * padx, relheight=2/7- 2 * pady)
        
        self.status.place(in_=self, relx=padx, rely=6/7+pady,
            relwidth=1- 2 * padx, relheight=1/7- 2 * pady)
        