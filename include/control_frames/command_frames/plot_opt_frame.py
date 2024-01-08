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

from include.control_frames.command_frames.plot_opt_frames.parameters import *
from include.control_frames.command_frames.plot_opt_frames.histogram import *

class plot_opt_frame(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        options = {'padx': 5, 'pady': 5}

        # Label frames
        self.parameters = parameters(self, root, text="Parameter")
        self.parameters.grid(**options, row = 0, column = 0)
        
        self.histogram = histogram(self, root, text="Histogram")
        self.histogram.grid(**options, row = 0, column = 1)

        # show the frame on the container
        self.grid(**options)

        self.bind('<Configure>', self.resize)

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        # place the window, giving it an explicit size
        self.parameters.place(in_=self, relx=padx, rely=pady, 
            relwidth=1/2 - 2 * padx, relheight=1- 2 * pady)
        
        self.histogram.place(in_=self, relx=1/2 + padx, rely=pady,
            relwidth=1/2- 2 * padx, relheight=1- 2 * pady)
