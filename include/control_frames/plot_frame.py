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

from include.control_frames.plot_frames.figure import *
from include.control_frames.plot_frames.plot_settings import *

class plot_frame(ttk.Frame):
    def __init__(self, parent, root, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        options = {'padx': 5, 'pady': 5}

        # Label frames
        self.figure = figure(self, root, text="Figure")
        self.figure.grid(**options, row = 0, column = 0)
        
        self.plot_settings = plot_settings(self, root, text="Plot settings")
        self.plot_settings.grid(**options, row = 0, column = 1)

        # show the frame on the container
        self.grid(**options)

        self.bind('<Configure>', self.resize)

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        # place the window, giving it an explicit size
        self.figure.place(in_=self, relx=padx, rely=pady, 
            relwidth=1 - 2 * padx, relheight=9/10 - 2 * pady)
        
        self.plot_settings.place(in_=self, relx=padx, rely=9/10 + pady,
            relwidth=1 - 2 * padx, relheight=1/10- 2 * pady)

        
