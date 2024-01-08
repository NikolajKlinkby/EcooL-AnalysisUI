import os
import subprocess
import tkinter as tk
import time
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
def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

class parameters(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.root = root
        self.container = container
        
        options = {'padx': 5, 'pady': 5}

        # Listbox
        self.param_list = tk.Listbox(self, selectmode=tk.SINGLE, exportselection=0)
        self.param_list.grid(row=0, column=0)

        self.scrollbar = tk.Scrollbar(self, command=self.param_list.yview)
        self.scrollbar.grid(row=0, column=0)
        self.param_list.config(yscrollcommand=self.scrollbar.set)

        # Checkboxes
        self.hist_check_var = tk.IntVar()
        self.hist_check = tk.Checkbutton(self, text='Hist.', variable=self.hist_check_var, command=self.hist_check_validate)
        self.hist_check.grid(row=1, column=0)
        self.hist_check_var.set(1)

        self.time_check_var = tk.IntVar()
        self.time_check = tk.Checkbutton(self, text='Time', variable=self.time_check_var, command=self.time_check_validate)
        self.time_check.grid(row=1, column=1)
        self.time_check_var.set(0)

        self.limited_check_var = tk.IntVar()
        self.limited_check = tk.Checkbutton(self, text='Limited', variable=self.limited_check_var)
        self.limited_check.grid(row=1, column=2)
        self.limited_check_var.set(0)

        # Plot button
        self.plotparambut = tk.Button(self, text='Plot param', command=self.plot_param)
        self.grid(row = 1, column=3)
        self.plotparambut['state'] = 'disabled'

        self.bind('<Configure>', self.resize)
    
    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2 / 50

        # place the window, giving it an explicit size
        self.param_list.place(in_=self, relx=padx, rely=0,
            relwidth=1 - 2 * padx - scrollbarwidth, relheight=4/5-3*pady)
        
        self.scrollbar.place(in_=self, relx=1 - padx - scrollbarwidth, rely=0,
            relwidth=scrollbarwidth, relheight=4/5-3*pady)
        
        self.hist_check.place(in_=self, relx=0, rely=4/5-2*pady,
            relwidth=1.5/8, relheight=1/5+pady)
        
        self.time_check.place(in_=self, relx=1.5/8, rely=4/5-2*pady,
            relwidth=1.5/8, relheight=1/5+pady)
        
        self.limited_check.place(in_=self, relx=3/8, rely=4/5-2*pady,
            relwidth=2/8-padx, relheight=1/5+pady)
        
        self.plotparambut.place(in_=self, relx=5/8, rely=4/5-2*pady,
            relwidth=3/8-padx, relheight=1/5+pady)

    def time_check_validate(self):
        if self.time_check_var.get() == self.hist_check_var.get():
            self.hist_check_var.set((self.time_check_var.get() + 1) % 2)

    def hist_check_validate(self):
        if self.time_check_var.get() == self.hist_check_var.get():
            self.time_check_var.set((self.hist_check_var.get() + 1) % 2)

    def plot_param(self):
        tab_name = self.param_list.get(self.param_list.curselection()[0])
        
        # See if the window already exists
        for item in self.root.tab_bar.winfo_children():
            if tab_name == self.root.tab_bar.tab(item)['text']:
                self.root.tab_bar.select(item)
                
                # Plot stuff in the window
                self._plot_param(item)

                return
        
        # Create a new window
        self.root.create_new_tab(tab_name)

        # Plot stuff in the window
        for item in self.root.tab_bar.winfo_children():
            if tab_name == self.root.tab_bar.tab(item)['text']:
                self.root.tab_bar.select(item)
                
                self._plot_param(item)

                return

    def _plot_param(self, item):
        # Clear axes
        for i, ax in enumerate(item.figure.fig.axes):
            item.figure.fig.delaxes(ax)

        # Create axis
        fig_ax = item.figure.fig.add_subplot(1,1,1)
        
        # Plot data
        plot_key = self.param_list.get(self.param_list.curselection()[0])
        for key in self.root.parameters['flags']:
            if plot_key in key:
                
                mask1 = np.ones(len(self.root.parameters[plot_key]), dtype=bool)
                mask2 = np.ones(len(self.root.parameters[plot_key]), dtype=bool)
                mask3 = np.ones(len(self.root.parameters[plot_key]), dtype=bool)
                mask4 = np.ones(len(self.root.parameters[plot_key]), dtype=bool)

                # Make mask from limits
                if self.limited_check_var.get():
                    # Loop over parameters
                    for entry in self.root.Command.settingsframe.parameters.entries:
                        param_list = np.array(self.root.parameters[entry[0]['text']])
                        if len(entry) == 5:
                            if entry[4].get():
                                if isfloat(entry[1].get().split(":")[0][1:]) and \
                                    isfloat(entry[1].get().split(":")[1][:-1]) and \
                                    isfloat(entry[2].get().split(":")[0][1:]) and \
                                    isfloat(entry[2].get().split(":")[1][:-1]):
                                    
                                    min = float(entry[1].get().split(':')[0][1:])
                                    max = float(entry[1].get().split(':')[1][:-1])
                                    mask1 = mask1 * (param_list >= min) * (param_list <= max)
                                    min = float(entry[2].get().split(':')[0][1:])
                                    max = float(entry[2].get().split(':')[1][:-1])
                                    mask2 = mask2 * (param_list >= min) * (param_list <= max)
                
                                else:
                                    print(time.strftime('%H:%M:%S', time.gmtime())+' Error using '+entry[0]['text']+' limits')

                        elif entry[6].get() and len(entry) == 7:
                            if isfloat(entry[1].get().split(":")[0][1:]) and \
                                isfloat(entry[1].get().split(":")[1][:-1]) and \
                                isfloat(entry[2].get().split(":")[0][1:]) and \
                                isfloat(entry[2].get().split(":")[1][:-1]) and \
                                isfloat(entry[3].get().split(":")[0][1:]) and \
                                isfloat(entry[3].get().split(":")[1][:-1]) and \
                                isfloat(entry[4].get().split(":")[0][1:]) and \
                                isfloat(entry[4].get().split(":")[1][:-1]):
                                
                                min = float(entry[1].get().split(':')[0][1:])
                                max = float(entry[1].get().split(':')[1][:-1])
                                mask1 = mask1 * (param_list >= min) * (param_list <= max)
                                min = float(entry[2].get().split(':')[0][1:])
                                max = float(entry[2].get().split(':')[1][:-1])
                                mask2 = mask2 * (param_list >= min) * (param_list <= max)
                                min = float(entry[3].get().split(':')[0][1:])
                                max = float(entry[3].get().split(':')[1][:-1])
                                mask3 = mask3 * (param_list >= min) * (param_list <= max)
                                min = float(entry[4].get().split(':')[0][1:])
                                max = float(entry[4].get().split(':')[1][:-1])
                                mask4 = mask4 * (param_list >= min) * (param_list <= max)
            
                if self.root.parameters['scan_key'] == 'Wavelength_ctr' or self.root.parameters['scan_key'] == 'Requested Transmission_ctr':                
                    laser_on = np.array(self.root.parameters['ADC.Laser_on'], dtype=bool)
                    laser_off = np.array(self.root.parameters['ADC.Laser_off'], dtype=bool)
                    
                    # Histogram setting
                    if self.hist_check_var.get():
                        fig_ax.hist(np.array(self.root.parameters[plot_key])[mask1*laser_on], 100, label='Laser On')
                        fig_ax.hist(np.array(self.root.parameters[plot_key])[mask2*laser_off], 100, label='Laser Off')
                        fig_ax.set_xlabel(plot_key)
                        fig_ax.set_ylabel('Counts')

                    # Time setting
                    elif self.time_check_var.get():
                        fig_ax.plot(np.array(self.root.parameters['Event'])[mask1*laser_on], np.array(self.root.parameters[plot_key])[mask1*laser_on], '.', label='Laser On')
                        fig_ax.plot(np.array(self.root.parameters['Event'])[mask2*laser_off], np.array(self.root.parameters[plot_key])[mask2*laser_off], '.', label='Laser Off')
                        fig_ax.set_xlabel('Event')
                        fig_ax.set_ylabel(plot_key)
                
                else:
                    pumpprobe = np.array(self.root.parameters['ADC.Probe_on'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_on'], dtype=bool)
                    probe = np.array(self.root.parameters['ADC.Probe_on'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_off'], dtype=bool)
                    pump = np.array(self.root.parameters['ADC.Probe_off'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_on'], dtype=bool)
                    none = np.array(self.root.parameters['ADC.Probe_off'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_off'], dtype=bool)
                    
                    # Histogram setting
                    if self.hist_check_var.get():
                        fig_ax.hist(np.array(self.root.parameters[plot_key])[mask1*pumpprobe], 100, label='Pump Probe')
                        fig_ax.hist(np.array(self.root.parameters[plot_key])[mask2*probe], 100, label='Probe')
                        fig_ax.hist(np.array(self.root.parameters[plot_key])[mask3*pump], 100, label='Pump')
                        fig_ax.hist(np.array(self.root.parameters[plot_key])[mask4*none], 100, label='None')
                        fig_ax.set_xlabel(plot_key)
                        fig_ax.set_ylabel('Counts')

                    # Time setting
                    elif self.time_check_var.get():
                        fig_ax.plot(np.array(self.root.parameters['Event'])[mask1*pumpprobe], np.array(self.root.parameters[plot_key])[mask1*pumpprobe], 'o', label='Pump Probe')
                        fig_ax.plot(np.array(self.root.parameters['Event'])[mask2*probe], np.array(self.root.parameters[plot_key])[mask2*probe], 'o', label='Probe')
                        fig_ax.plot(np.array(self.root.parameters['Event'])[mask3*pump], np.array(self.root.parameters[plot_key])[mask3*pump], 'o', label='Pump')
                        fig_ax.plot(np.array(self.root.parameters['Event'])[mask4*none], np.array(self.root.parameters[plot_key])[mask4*none], 'o', label='None')
                        fig_ax.set_xlabel('Event')
                        fig_ax.set_ylabel(plot_key)

                fig_ax.axhline(0, color='k')
                fig_ax.legend(loc=1)
                fig_ax.minorticks_on()
                fig_ax.set_position([0.05,0.1,0.94,0.89])

                # Update settings
                item.plot_settings.xmin_entry.delete(0,'end')
                item.plot_settings.xmin_entry.insert(0,fig_ax.get_xlim()[0])
                item.plot_settings.xmax_entry.delete(0,'end')
                item.plot_settings.xmax_entry.insert(0,fig_ax.get_xlim()[1])

                item.plot_settings.zero_line.select()

                item.figure.canvas.draw()

    def load_update(self):
        # Reset dropdown and list
        self.param_list.delete(0, tk.END)

        for key in self.root.parameters['flags']:
            self.param_list.insert(tk.END, key)

        self.param_list.selection_set(0, 0)

        self.plotparambut['state'] = 'normal'