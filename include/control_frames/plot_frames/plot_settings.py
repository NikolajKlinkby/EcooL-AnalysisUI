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
import matplotlib.text as plttxt
import matplotlib.lines as pltlines
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

class plot_settings(tk.LabelFrame):
    def __init__(self, parent, root, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.root = root
        self.container = parent
        self.window = {}
        
        options = {'padx': 5, 'pady': 5}

        # Checkbuttons
        self.zero_line = tk.Checkbutton(self, text='Zero line', command=self.zero_line_change)
        self.zero_line.grid(row = 0, column = 0)

        self.popup = tk.Checkbutton(self, text='Popup figure')
        self.popup.grid(row = 0, column = 0)

        self.retain_x_zoom = tk.Checkbutton(self, text='Retain x-zoom')
        self.retain_x_zoom.grid(row = 0, column = 0)

        self.retain_y_zoom = tk.Checkbutton(self, text='Retain y-zoom')
        self.retain_y_zoom.grid(row = 0, column = 0)

        self.window_data = tk.Checkbutton(self, text='Window data', command=self.show_window)
        self.window_data.grid(row = 0, column = 0)

        # x-limits
        self.xmin_label = tk.Label(self, text='x-min', borderwidth=1, relief='solid')
        self.xmin_label.grid()

        self.xmin_entry = tk.Entry(self, validate='key')
        self.xmin_entry.grid()
        self.xmin_entry['validatecommand'] = (self.xmin_entry.register(self.entry_validate),'%P')

        self.xmax_label = tk.Label(self, text='x-min', borderwidth=1, relief='solid')
        self.xmin_label.grid()

        self.xmax_entry = tk.Entry(self, validate='key')
        self.xmax_entry.grid()
        self.xmax_entry['validatecommand'] = (self.xmax_entry.register(self.entry_validate),'%P')

        self.x_zoom_but = tk.Button(self, text='x-zoom', command=self.xzoom)

        self.bind('<Configure>', self.resize)
    
    
    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2 / 50

        self.zero_line.place(in_ = self, relx = 0, rely = 0,
                             relwidth = 1/10, relheight = 1/2)
        
        self.popup.place(in_ = self, relx = 0, rely = 1/2,
                             relwidth = 1/10, relheight = 1/2)
        
        self.retain_x_zoom.place(in_ = self, relx = 1/10, rely = 0,
                             relwidth = 1/10, relheight = 1/2)
        
        self.retain_y_zoom.place(in_ = self, relx = 1/10, rely = 1/2,
                             relwidth = 1/10, relheight = 1/2)
        
        self.window_data.place(in_ = self, relx = 2/10, rely = 0,
                             relwidth = 1/10, relheight = 1/2)
        
        self.xmin_label.place(in_ = self, relx = 3/10, rely = 0,
                             relwidth = 1/10, relheight = 1/2)
        
        self.xmin_entry.place(in_ = self, relx = 3/10, rely = 1/2,
                             relwidth = 1/10, relheight = 1/2)
        
        self.xmax_label.place(in_ = self, relx = 4/10, rely = 0,
                             relwidth = 1/10, relheight = 1/2)
        
        self.xmax_entry.place(in_ = self, relx = 4/10, rely = 1/2,
                             relwidth = 1/10, relheight = 1/2)
        
        self.x_zoom_but.place(in_ = self, relx = 5/10, rely = 0,
                             relwidth = 1/10, relheight = 1/2)
        
    def xzoom(self):
        for ax in self.container.figure.fig.axes:
            if self.xmin_entry.get() == '' or self.xmax_entry.get() == '':
                pass
            elif float(self.xmin_entry.get()) >= float(self.xmax_entry.get()):
                print('xmax must be greater than xmin')
            else:
                ax.set_xlim(float(self.xmin_entry.get()), float(self.xmax_entry.get()))
        self.container.figure.fig.axes[-1].set_xticklabels(self.container.figure.fig.axes[-1].get_xticks())
        self.container.figure.canvas.draw()

    def show_window(self):
        
        if isinstance(self.window, plttxt.Text):
            self.window.remove()
            self.window = {}
            self.container.figure.canvas.draw()
        
        elif len(self.container.figure.fig.axes) > 0:

            text = 'Counts in windows\n'
            
            edges = np.array(self.root.histogram['edges'])*1e-3
            edges = edges[:-1]
            
            # Read off background numbers
            text += '\n\t\tBackground\n'
            back_det = self.root.Command.settingsframe.calculations.back_det_men_var.get()
            back_mask = (edges > 1000) * (edges < 1000)
            for entry in self.root.Command.settingsframe.windows.entries_back:
                if entry[0]['text'] == back_det:
                    back_mask = (edges > float(entry[1].get())) * (edges < float(entry[2].get()))
                    if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                        laser_on = np.sum(np.array(self.root.histogram[back_det + '_hist_1_acc'])[back_mask])
                        laser_off = np.sum(np.array(self.root.histogram[back_det + '_hist_0_acc'])[back_mask])
                        
                        text += f"Laser on\t{int(laser_on/(laser_on+laser_off)*100)}\%\t{int(laser_on)}\n"
                        text += f"Laser off\t{int(laser_off/(laser_on+laser_off)*100)}\%\t{int(laser_off)}\n"
                    else:
                        pumpprobe = np.sum(np.array(self.root.histogram[back_det + '_hist_1_1_acc'])[back_mask])
                        pump = np.sum(np.array(self.root.histogram[back_det + '_hist_0_1_acc'])[back_mask])
                        probe = np.sum(np.array(self.root.histogram[back_det + '_hist_1_0_acc'])[back_mask])
                        none = np.sum(np.array(self.root.histogram[back_det + '_hist_0_0_acc'])[back_mask])
                        
                        text += f"Both\t{int(pumpprobe/(pumpprobe+pump+probe+none)*100)}\%\t{int(pumpprobe)}\n"
                        text += f"Pump\t{int(pump/(pumpprobe+pump+probe+none)*100)}\%\t{int(pump)}\n"
                        text += f"Probe\t{int(probe/(pumpprobe+pump+probe+none)*100)}\%\t{int(probe)}\n"
                        text += f"None\t{int(none/(pumpprobe+pump+probe+none)*100)}\%\t{int(none)}\n"

            for entry in self.root.Command.settingsframe.windows.entries:
                det = entry[5].get()
                text += f'\n\t\t{entry[0].get()}\n'
                mask = (edges > float(entry[2].get())) * (edges < float(entry[3].get()))

                if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                    laser_on = np.sum(np.array(self.root.histogram[det + '_hist_1_acc'])[mask])
                    laser_off = np.sum(np.array(self.root.histogram[det + '_hist_0_acc'])[mask])
                    
                    text += f"Laser on\t{int(laser_on/(laser_on+laser_off)*100)}\%\t{int(laser_on)}\n"
                    text += f"Laser off\t{int(laser_off/(laser_on+laser_off)*100)}\%\t{int(laser_off)}\n"
                else:
                    pumpprobe = np.sum(np.array(self.root.histogram[det + '_hist_1_1_acc'])[mask])
                    pump = np.sum(np.array(self.root.histogram[det + '_hist_0_1_acc'])[mask])
                    probe = np.sum(np.array(self.root.histogram[det + '_hist_1_0_acc'])[mask])
                    none = np.sum(np.array(self.root.histogram[det + '_hist_0_0_acc'])[mask])
                    
                    text += f"Both\t{int(pumpprobe/(pumpprobe+pump+probe+none)*100)}\%\t{int(pumpprobe)}\n"
                    text += f"Pump\t{int(pump/(pumpprobe+pump+probe+none)*100)}\%\t{int(pump)}\n"
                    text += f"Probe\t{int(probe/(pumpprobe+pump+probe+none)*100)}\%\t{int(probe)}\n"
                    text += f"None\t{int(none/(pumpprobe+pump+probe+none)*100)}\%\t{int(none)}\n"
            
            self.window = self.container.figure.fig.axes[0].text(0.025, 0.5, text, fontsize = self.root.font_size, transform=self.container.figure.fig.axes[0].transAxes,
                bbox = dict(facecolor = 'white', alpha = 1))
            self.container.figure.canvas.draw()

    def zero_line_change(self):
        for ax in self.container.figure.fig.axes:
            zero_line = True
            for child in ax.get_children():
                if isinstance(child, pltlines.Line2D):
                    if np.all(np.array(child.get_ydata()) == 0) and len(child.get_ydata()) == 2:

                        ax.lines.remove(child)
                        del child
                        zero_line = False
                        self.container.figure.canvas.draw()
            
            if zero_line:
                ax.axhline(0, color='k')
                self.container.figure.canvas.draw()

    def entry_validate(self, val):
        if val == '':
            return True
        else:
            try:
                float(val)
                return True
            except:
                return False