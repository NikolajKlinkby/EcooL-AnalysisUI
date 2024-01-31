import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import numpy as np
import time
import json
from threading import Thread
import traceback
from inspect import signature
from inspect import getfullargspec
from include.FittingRoutine import FittingRoutine
import platform

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def os_format_string(string):
    _string = string.split('/')
    if platform.system() == 'Windows':
        string = ''
        for s in _string:
            string = os.path.join(string, s)
        if string[1] == ':':
            string = string[:2] + os.path.sep + string[2:]
    else:
        string = '/'
        for s in _string:
            string = os.path.join(string, s)
    return string

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


class settingstool(tk.Toplevel):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.title("Settings")
        self.geometry(f'{int(root.winfo_width()/3)}x{int(root.winfo_height()/3)}')

        self.root = root
        self.settings_widgets = dict()

        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self, background='white')
        self.canvas.grid(row=0, column=0, sticky='nswe')

        # Create a vertical scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='nse')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas to hold the widgets
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw", tags='inner_frame')
        self.inner_frame.grid_propagate(False)
        
        # Loop through settings and attach the widgets
        width = int(root.winfo_width()/3)
        height = int(root.winfo_height()/3)

        padx = 5 / width
        pady = 5 / height
        
        self.widget_pr_page = 10

        for row, key in enumerate(self.root.settings.keys()):

            # Count horizontal spaze to use
            coloumns = 0
            if isinstance(self.root.settings[key], (list,tuple)):
                coloumns += len(self.root.settings[key])
            else:
                coloumns += 1
            col = 0

            # Label of setting
            label = tk.Label(self.inner_frame, text=key)
            label.grid(row=0, column=0)
            
            widgets = [label]

            if isinstance(self.root.settings[key], (list,tuple)):
                for e in self.root.settings[key]:
                    entry = ttk.Entry(self.inner_frame)
                    entry.insert(0, e)
                    col += 1
                    widgets.append(entry)
            else:
                entry = ttk.Entry(self.inner_frame)
                entry.insert(0, self.root.settings[key])
                entry.grid(row=0, column=0)
                widgets.append(entry)
            
            self.settings_widgets[key] = widgets

        # Button
        self.safebut = tk.Button(self, text='Safe', command=self.save)
        self.safebut.grid()
        self.safebut.place(in_=self, relx=padx, rely=9/10+pady, 
                            relwidth=1 - 2 * padx, relheight=1/10 - 2 * pady)
        
        # Function to update scroll region whenever widgets are added or removed
        self.inner_frame.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.update_canvas)
        
        self.bind('<Configure>', self.resize)
        self.protocol("WM_DELETE_WINDOW", lambda : self.destroy())

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2/50

        # place the window, giving it an explicit size
        self.scrollbar.place(in_=self, relx=1 - padx - scrollbarwidth, rely=0, 
            relwidth=scrollbarwidth, relheight=9/10 - 2 * pady)
        
        self.canvas.place(in_=self, relx=0, rely=0,
            relwidth=1- 2 * padx - scrollbarwidth, relheight=9/10 - 2 * pady)
        
        self.safebut.place(in_=self, relx=padx, rely=9/10+pady, 
                            relwidth=1 - 2 * padx, relheight=1/10 - 2 * pady)
        
        # Resize the settings entries
        height = self.canvas.winfo_reqheight()
        width = self.canvas.winfo_reqwidth()

        padx = 5 / width
        pady = 5 / height

        for row, key in enumerate(self.settings_widgets.keys()):

            # Count horizontal spaze to use
            coloumns = 0
            if isinstance(self.settings_widgets[key], (list,tuple)):
                coloumns += len(self.settings_widgets[key])
            else:
                coloumns += 1
            col = 0

            # Label of setting
            self.settings_widgets[key][0].place(x=col/coloumns*width, y=(row/self.widget_pr_page)*height+pady, 
                        width=1/4*width - 2 * padx, height=1/self.widget_pr_page*height - 2 * pady)

            for entry in self.settings_widgets[key][1:]:
                entry.place(x=(1/4+3*col/coloumns/4)*width, y=(row/self.widget_pr_page)*height+pady, 
                                width=(3/coloumns/4)*width - 2 * padx, height=(1/self.widget_pr_page)*height- 2 * pady)
                col += 1
        
        self.canvas.itemconfigure("inner_frame", height=(len(self.settings_widgets.keys())+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
    
    def update_canvas(self, event):
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.winfo_width())

    def update_scroll_region(self, event):
        self.update_canvas(event)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.winfo_width())

    def save(self):
        for key in self.settings_widgets.keys():
            set = []
            for entry in self.settings_widgets[key][1:]:
                set.append(entry.get())
            
            if len(set) == 1:
                self.root.settings[key] = set[0]
            else:
                self.root.settings[key] = set

        f = open(os_format_string(os.getcwd()+'/settings_files/settings.txt'), 'w')
        f.write(json.dumps(self.root.settings, cls=NumpyEncoder))
        f.close()
        