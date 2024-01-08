import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
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

from include.control_frames.command_frames.settings_frames.data_path_settings import *
from include.control_frames.command_frames.settings_frames.calculations import *
from include.control_frames.command_frames.settings_frames.parameters import *
from include.control_frames.command_frames.settings_frames.windows import *

class settings_frame(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.container = container
        
        options = {'padx': 5, 'pady': 5}

        # Label frames
        self.datapathsettings = data_path_settings(self, root, text="Data path settings")
        self.datapathsettings.grid(**options, row = 0, column = 0)
        
        self.calculations = calculations(self, root, text="Calculations")
        self.calculations.grid(**options, row = 0, column = 1)
        
        self.parameters = parameters(self, root, text="Parameters")
        self.parameters.grid(**options, row = 1, column = 0)
        
        self.windows = windows(self, root, text="Windows")
        self.windows.grid(**options, row = 1, column = 1)

        # show the frame on the container
        self.grid(**options)

        self.bind('<Configure>', self.resize)

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        # place the window, giving it an explicit size
        self.datapathsettings.place(in_=self, relx=padx, rely=pady, 
            relwidth=1/2 - 2 * padx, relheight=2/5- 2 * pady)
        
        self.calculations.place(in_=self, relx=1/2 + padx, rely=pady,
            relwidth=1/2- 2 * padx, relheight=2/5- 2 * pady)
        
        self.parameters.place(in_=self, relx=padx, rely=2/5+pady,
            relwidth=1/2- 2 * padx, relheight=3/5- 2 * pady)
        
        self.windows.place(in_=self, relx=1/2 + padx, rely=2/5+pady,
            relwidth=1/2- 2 * padx, relheight=3/5- 2 * pady)                 
