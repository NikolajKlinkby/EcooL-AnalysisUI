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

class figure(tk.LabelFrame):
    def __init__(self, parent, root, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.root = root
        self.container = parent
        
        options = {'padx': 5, 'pady': 5}

        # Figure
        self.fig = plt.Figure()
    
        # creating the Tkinter canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master = self)  
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()
    
        # creating the Matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
    
        # placing the toolbar on the Tkinter window
        self.canvas.get_tk_widget().pack()

        self.bind('<Configure>', self.resize)
    
    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2 / 50

        self.canvas.get_tk_widget().place(in_=self, relx = 0, rely = 0,
                          relwidth = 1, relheight = 1)