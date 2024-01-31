import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import numpy as np
from threading import Thread
import queue
import json
import traceback
from inspect import signature
from inspect import getfullargspec
from include.FittingRoutine import FittingRoutine
import platform

if platform.system() == 'Windows':
    import ctypes
elif platform.system() == 'Linux':
    import dbus

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

from include.control_frames.plot_frame import *
from include.control_frames.command_frame import *
from include.comparetool import *
from include.fittingtool import *
from include.settingstool import *

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

# %%
"""                                              Classes                                                             """
class ControlWindow(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "Data Analysis Program")
        
        # Scaling
        scalefactor = 1
        if platform.system() == 'Windows':
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            scalefactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        elif platform.system() == 'Linux':
            namespace = "org.gnome.Mutter.DisplayConfig"
            dbus_path = "/org/gnome/Mutter/DisplayConfig"

            session_bus = dbus.SessionBus()
            obj = session_bus.get_object(namespace, dbus_path)
            interface = dbus.Interface(obj, dbus_interface=namespace)

            current_state = interface.GetCurrentState()
            logical_monitors = current_state[2]
            _, _, scalefactor, _, _, _, _ = logical_monitors[0]


        # Geometry
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        geometry = "%ix%i" % (screen_width, screen_height)
        self.geometry(geometry)
        
        # Font size 
        default_font = tk.font.nametofont("TkDefaultFont")
        text_font = tk.font.nametofont("TkTextFont")
        fixed_font = tk.font.nametofont("TkFixedFont")
        self.font_size = int(13*72* screen_height*scalefactor/(1504*96))+(((13*72*screen_height*scalefactor) % (1504*96)) > 0)
        default_font.configure(size=self.font_size)
        text_font.configure(size=self.font_size)
        fixed_font.configure(size=self.font_size)

        '''             Initial window            '''
        # Initial attempt to set paths
        self.home_dir = os.path.expanduser('~')
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.src_dir = self.current_dir[:-8]+'/src'
        self.dat_file_path = self.current_dir
        
        '''             Menu bar            '''
        menu_bar = tk.Menu()
        self.config(menu=menu_bar)
        menu_bar.add_command(label='  Exit  ', command=lambda: self.quit())
        menu_bar.add_command(label='  Settings  ', command=lambda: self.settings_popup())
        menu_bar.add_command(label='  Compare Tool  ', command=lambda: self.comparetool())
        menu_bar.add_command(label='  Fitting Tool  ', command=lambda: self.fittingtool())

        """             Initial paramaters            """
        self.folder_path = '~/'
        self.run_choosen = ''
        self.bin_size = 1000 # in ns
        self.histogram = dict()
        self.histogram_deplete = dict()
        self.calculations = dict()
        self.windows = dict()
        self.settings = dict()
        self.plotdict = dict()
        self.parameters = dict()
        self.empty_tab = True
        self.queue = queue.Queue()

        # Settings
        if os.path.exists(os.getcwd()+'/settings_files/settings.txt'):
            f = open(os_format_string(os.getcwd()+'/settings_files/settings.txt'), 'r')
            self.settings = json.loads(f.read())
            f.close()
        else:
            self.settings['depletion_flag'] = 'ADC.Photodiode'
            self.settings['depletion_low'] = ['0', '100']
            self.settings['depletion_high'] = ['100', '10000']
            self.settings['max_TDC_chanels'] = '3125000'
            
            f = open(os_format_string(os.getcwd()+'/settings_files/settings.txt'), 'w')
            f.write(json.dumps(self.settings, cls=NumpyEncoder))
            f.close()

        if 'folder_path' not in self.settings.keys():
            self.folder_path = os.getcwd()
        else:
            self.folder_path = self.settings['folder_path']


        '''                 Frames                '''
        
        self.config(relief='groove')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)
        self.rowconfigure(0, weight=1)
        
        self.Command = command_frame(self, self)

        self.tab_bar = ttk.Notebook(self)
        
        self.PlotFrame = plot_frame(self.tab_bar, self)
        
        # Add frames to tab
        self.tab_bar.add(self.PlotFrame, text="Empty Plot")
        self.tab_bar.grid(padx = 5, pady = 5, row=0, column=1, sticky=tk.N+tk.W+tk.E+tk.S)

        self.tab_bar.bind('<Button-3>', self.close_tab)

        self.bind('<Configure>', self.resize)

        self.protocol("WM_DELETE_WINDOW", lambda : self.quit())

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        # place the window, giving it an explicit size
        self.Command.place(in_=self, relx=0, rely=0, 
            relwidth=1/3, relheight=1)
        
        self.tab_bar.place(in_=self, relx=1/3 + padx, rely=pady,
            relwidth=2/3 - 2 * padx, relheight=1 - 2 * pady)
        
    def close_tab(self, event):
        if len(self.tab_bar.winfo_children()) > 1:
            clicked_tab = self.tab_bar.tk.call(self.tab_bar._w, "identify", "tab", event.x, event.y)
            active_tab = self.tab_bar.index(self.tab_bar.select())

            if clicked_tab == active_tab:
                for item in self.tab_bar.winfo_children():
                    if self.tab_bar.index(item) == clicked_tab:
                        item.destroy()
                        return
    
    def create_new_tab(self, text):
        new_tab = plot_frame(self.tab_bar, self)
        self.tab_bar.add(new_tab, text=text)
        self.tab_bar.select()

        if self.empty_tab:
            self.PlotFrame.destroy()
            self.empty_tab = False

    def disable_buttons(self):
        self.Command.settingsframe.datapathsettings.browsebut['state'] = 'disabled'
        self.Command.settingsframe.datapathsettings.loadbut['state'] = 'disabled'
        self.Command.settingsframe.datapathsettings.updatebut['state'] = 'disabled'
        self.Command.settingsframe.datapathsettings.forcebut['state'] = 'disabled'
        self.Command.settingsframe.datapathsettings.runlist.configure(state="disabled")

        self.Command.settingsframe.calculations.resetbut['state'] = 'disabled'
        self.Command.settingsframe.calculations.recalcbut['state'] = 'disabled'
        self.Command.settingsframe.calculations.file_entry['state'] = 'disabled'
        self.Command.settingsframe.calculations.back_det_men.configure(state="disabled")
        self.Command.settingsframe.calculations.calc_file_men.configure(state="disabled")

        self.Command.settingsframe.parameters.scandropdown.configure(state="disabled")
        self.Command.settingsframe.parameters.genhistbut['state'] = 'disabled'
        
        self.Command.plotoptframe.histogram.scale_opt_men.configure(state="disabled")
        self.Command.plotoptframe.histogram.window_check['state'] = 'disabled'
        self.Command.plotoptframe.histogram.plot_hist_but['state'] = 'disabled'

        self.Command.plotoptframe.parameters.plotparambut['state'] = 'disabled'
        
        self.Command.results.plotresultbut['state'] = 'disabled'

    def enable_buttons(self):
        self.Command.settingsframe.datapathsettings.browsebut['state'] = 'normal'
        self.Command.settingsframe.datapathsettings.loadbut['state'] = 'normal'
        self.Command.settingsframe.datapathsettings.updatebut['state'] = 'normal'
        self.Command.settingsframe.datapathsettings.forcebut['state'] = 'normal'
        self.Command.settingsframe.datapathsettings.runlist.configure(state="normal")

        self.Command.settingsframe.calculations.resetbut['state'] = 'normal'
        self.Command.settingsframe.calculations.recalcbut['state'] = 'normal'
        self.Command.settingsframe.calculations.file_entry['state'] = 'normal'
        self.Command.settingsframe.calculations.back_det_men.configure(state="normal")
        self.Command.settingsframe.calculations.calc_file_men.configure(state="normal")

        self.Command.settingsframe.parameters.scandropdown.configure(state="normal")
        self.Command.settingsframe.parameters.genhistbut['state'] = 'normal'
        
        self.Command.plotoptframe.histogram.scale_opt_men.configure(state="normal")
        self.Command.plotoptframe.histogram.window_check['state'] = 'normal'
        self.Command.plotoptframe.histogram.plot_hist_but['state'] = 'normal'

        self.Command.plotoptframe.parameters.plotparambut['state'] = 'normal'
        
        self.Command.results.plotresultbut['state'] = 'normal'

    def comparetool(self):
        comparetool(self, self)

    def fittingtool(self):
        fittingtool(self, self)

    def settings_popup(self):
        settingstool(self, self)