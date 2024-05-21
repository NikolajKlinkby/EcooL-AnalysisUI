import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import numpy as np
import time
from threading import Thread
import traceback
from inspect import signature
from inspect import getfullargspec
from include.FittingRoutine import FittingRoutine

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

class histogram(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.root = root
        self.container = container
        
        options = {'padx': 5, 'pady': 5}

        # Listbox detectors
        self.detector_list = tk.Listbox(self, selectmode=tk.SINGLE, exportselection=0)
        self.detector_list.grid(row=0, column=0)

        self.detector_scrollbar = tk.Scrollbar(self, command=self.detector_list.yview)
        self.detector_scrollbar.grid(row=0, column=0)
        self.detector_list.config(yscrollcommand=self.detector_scrollbar.set)
        
        # Bind clicks
        self.detector_list.bind('<<ListboxSelect>>', self.on_detector_select)

        # Listbox scan
        self.scan_list = tk.Listbox(self, selectmode=tk.SINGLE, exportselection=0)
        self.scan_list.grid(row=0, column=0)

        self.scan_scrollbar = tk.Scrollbar(self, command=self.scan_list.yview)
        self.scan_scrollbar.grid(row=0, column=0)
        self.scan_list.config(yscrollcommand=self.scan_scrollbar.set)
        
        # Bind clicks
        self.scan_list.bind('<<ListboxSelect>>', self.on_scan_select)

        # Dropdown
        self.scale_opt_var = tk.StringVar()
        self.scale_opt_var.set('linear')
        self.scale_opt_men = tk.OptionMenu(self, self.scale_opt_var, *['linear', 'log'], command=self.axis_change)
        self.scale_opt_men.grid(row=1, column=0)

        # Check
        self.window_check = ttk.Checkbutton(self, text='Show windows', command=self.plot_windows)
        self.window_check.grid(row=1, column=1)
        self.window_check.state(['selected'])

        # Plot
        self.plot_hist_but = tk.Button(self, text='Plot Hist.', command=self.plot_hist)
        self.plot_hist_but.grid(row=1, column=2)
        self.plot_hist_but['state'] = 'disabled'

        self.bind('<Configure>', self.resize)
    
    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2 / 50

        # place the window, giving it an explicit size
        self.detector_list.place(in_=self, relx=padx, rely=0,
            relwidth=2/3 - 2 * padx - scrollbarwidth, relheight=4/5-3*pady)
        
        self.detector_scrollbar.place(in_=self, relx=2/3 - padx - scrollbarwidth, rely=0,
            relwidth=scrollbarwidth, relheight=4/5-3*pady)
        
        self.scan_list.place(in_=self, relx=2/3+padx, rely=0,
            relwidth=1/3 - 2 * padx - scrollbarwidth, relheight=4/5-3*pady)
        
        self.scan_scrollbar.place(in_=self, relx=1 - padx - scrollbarwidth, rely=0,
            relwidth=scrollbarwidth, relheight=4/5-3*pady)
        
        self.scale_opt_men.place(in_=self, relx=0, rely=4/5-2*pady,
            relwidth=1.25/4, relheight=1/5+pady)
        
        self.window_check.place(in_=self, relx=1.25/4, rely=4/5-2*pady,
            relwidth=1.75/4, relheight=1/5+pady)
        
        self.plot_hist_but.place(in_=self, relx=3/4, rely=4/5-2*pady,
            relwidth=1/4, relheight=1/5+pady)
         
    def on_detector_select(self, event):
        pass

    def on_scan_select(self, event):
        pass
    
    def plot_windows(self):
        for item in self.root.tab_bar.winfo_children():
            for key in self.root.histogram['time_keys']:
                if key[key.find('.')+1:] in self.root.tab_bar.tab(item)['text']:
                    
                    for i, entry in enumerate(self.detector_list.get(0, 'end')):
                        if key == entry:
                            self.detector_list.activate(i)
                    
                    for i, entry in enumerate(self.scan_list.get(0, 'end')):
                        if self.root.tab_bar.tab(item)['text'][self.root.tab_bar.tab(item)['text'].rfind(' ')+1:] == entry:
                            self.scan_list.activate(i)
                    
                    # Plot stuff in the window
                    self._plot_hist(item)
    
    def axis_change(self, event):
        self.plot_windows()
    
    def plot_hist(self):
        tab_name = self.detector_list.get(self.detector_list.curselection()[0])
        tab_name = tab_name[tab_name.find('.')+1:] + ' ' + str(self.scan_list.get(self.scan_list.curselection()[0]))
        
        # See if the window already exists
        for item in self.root.tab_bar.winfo_children():
            if tab_name == self.root.tab_bar.tab(item)['text']:
                self.root.tab_bar.select(item)
                
                # Plot stuff in the window
                self._plot_hist(item)

                return
        
        # Create a new window
        self.root.create_new_tab(tab_name)

        # Plot stuff in the window
        for item in self.root.tab_bar.winfo_children():
            if tab_name == self.root.tab_bar.tab(item)['text']:
                self.root.tab_bar.select(item)
                
                self._plot_hist(item)

                return

    def _plot_hist(self, item):
        # Clear axes
        for i, ax in enumerate(item.figure.fig.axes):
            item.figure.fig.delaxes(ax)

        # Create axis
        hist_ax = item.figure.fig.add_subplot(1,1,1)
        
        # Plot data
        plot_key = self.detector_list.get(self.detector_list.curselection()[0])
        scan_step = self.scan_list.get(self.scan_list.curselection()[0])
        for key in self.root.histogram['time_keys']:
            if plot_key in key:
                
                edges = np.array(self.root.histogram['edges'])*1e-3

                # Hist settings
                # Plot windows
                if self.window_check.instate(['selected']):
                    for entry in self.root.Command.settingsframe.windows.entries:
                        if plot_key == entry[5].get():
                            try:
                                mask = (edges[1:] > float(entry[2].get())) * (edges[:-1] < float(entry[3].get()))
                                max = 0

                                if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                                    if scan_step == 'all':
                                        max = np.max(np.array(self.root.histogram[plot_key + '_hist_1_acc'])[mask]+np.array(self.root.histogram[plot_key + '_hist_0_acc'])[mask])
                                    else:
                                        max = np.max(np.array(self.root.histogram[plot_key + '_hist_1_' + str(scan_step)])[mask]+np.array(self.root.histogram[plot_key + '_hist_0_' + str(scan_step)])[mask])
                                else:
                                    if scan_step == 'all':
                                        max = np.max(np.array(self.root.histogram[plot_key + '_hist_0_0_acc'])[mask]+np.array(self.root.histogram[plot_key + '_hist_1_1_acc'])[mask]+
                                                    np.array(self.root.histogram[plot_key + '_hist_1_0_acc'])[mask]+np.array(self.root.histogram[plot_key + '_hist_0_1_acc'])[mask])
                                    else:
                                        max = np.max(np.array(self.root.histogram[plot_key + '_hist_0_0_' + str(scan_step)])[mask]+np.array(self.root.histogram[plot_key + '_hist_1_1_' + str(scan_step)])[mask]+
                                                    np.array(self.root.histogram[plot_key + '_hist_1_0_' + str(scan_step)])[mask]+np.array(self.root.histogram[plot_key + '_hist_0_1_' + str(scan_step)])[mask])

                                hist_ax.add_patch(Rectangle((float(entry[2].get()), 0), float(entry[3].get())-float(entry[2].get()), max, color='red', alpha=0.5))

                                hist_ax.text(0.5*(float(entry[2].get())+float(entry[3].get())), max, entry[0].get(), ha='center')
                            except:
                                print(time.strftime('%H:%M:%S', time.gmtime())+' Window '+entry[0].get()+' not in histogram range')

                    for entry in self.root.Command.settingsframe.windows.entries_back:
                        if plot_key == entry[0]['text']:
                            try:
                                mask = (edges[1:] > float(entry[1].get())) * (edges[:-1] < float(entry[2].get()))
                                max = 0

                                if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                                    if scan_step == 'all':
                                        max = np.max(np.array(self.root.histogram[plot_key + '_hist_1_acc'])[mask]+np.array(self.root.histogram[plot_key + '_hist_0_acc'])[mask])
                                    else:
                                        max = np.max(np.array(self.root.histogram[plot_key + '_hist_1_' + str(scan_step)])[mask]+np.array(self.root.histogram[plot_key + '_hist_0_' + str(scan_step)])[mask])
                                else:
                                    if scan_step == 'all':
                                        max = np.max(np.array(self.root.histogram[plot_key + '_hist_0_0_acc'])[mask]+np.array(self.root.histogram[plot_key + '_hist_1_1_acc'])[mask]+
                                                    np.array(self.root.histogram[plot_key + '_hist_1_0_acc'])[mask]+np.array(self.root.histogram[plot_key + '_hist_0_1_acc'])[mask])
                                    else:
                                        max = np.max(np.array(self.root.histogram[plot_key + '_hist_0_0_' + str(scan_step)])[mask]+np.array(self.root.histogram[plot_key + '_hist_1_1_' + str(scan_step)])[mask]+
                                                    np.array(self.root.histogram[plot_key + '_hist_1_0_' + str(scan_step)])[mask]+np.array(self.root.histogram[plot_key + '_hist_0_1_' + str(scan_step)])[mask])

                                hist_ax.add_patch(Rectangle((float(entry[1].get()), 0), float(entry[2].get())-float(entry[1].get()), max, color='blue', alpha=0.5))

                                hist_ax.text(0.5*(float(entry[1].get())+float(entry[2].get())), max, 'Background', ha='center')
                            except:
                                print(time.strftime('%H:%M:%S', time.gmtime())+' Background window not in histogram range')

                # Scale
                hist_ax.set_yscale(self.scale_opt_var.get())

                # Plot
                if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                    if scan_step == 'all':
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_1_acc']), edges, label='Laser On')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_0_acc']), edges, label='Laser Off')
                        if (plot_key + '_hist_1_acc') in self.root.histogram_deplete.keys() and (plot_key + '_hist_0_acc') in self.root.histogram_deplete.keys():
                            hist_ax.stairs(np.array(self.root.histogram_deplete[plot_key + '_hist_1_acc']), edges, label='Laser On Depleted')
                            hist_ax.stairs(np.array(self.root.histogram_deplete[plot_key + '_hist_0_acc']), edges, label='Laser Off Depleted')
                    else:
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_1_' + str(scan_step)]), edges, label='Laser On')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_0_' + str(scan_step)]), edges, label='Laser Off')
                        if (plot_key + '_hist_1_' + str(scan_step)) in self.root.histogram_deplete.keys() and (plot_key + '_hist_0_' + str(scan_step)) in self.root.histogram_deplete.keys():
                            hist_ax.stairs(np.array(self.root.histogram_deplete[plot_key + '_hist_1_' + str(scan_step)]), edges, label='Laser On Depleted')
                            hist_ax.stairs(np.array(self.root.histogram_deplete[plot_key + '_hist_0_' + str(scan_step)]), edges, label='Laser Off Depleted')
                else:
                    if scan_step == 'all':
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_1_1_acc']), edges, label='Pump Probe')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_0_0_acc']), edges, label='None')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_1_0_acc']), edges, label='Probe')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_0_1_acc']), edges, label='Pump')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_1_1_acc'])
                                       -np.array(self.root.histogram[plot_key + '_hist_1_0_acc'])
                                       -np.array(self.root.histogram[plot_key + '_hist_0_1_acc'])
                                       +np.array(self.root.histogram[plot_key + '_hist_0_0_acc']), edges, label='Signal')
                    else:
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_1_1_' + str(scan_step)]), edges, label='Pump Probe')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_0_0_' + str(scan_step)]), edges, label='None')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_0_1_' + str(scan_step)]), edges, label='Pump')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_1_0_' + str(scan_step)]), edges, label='Probe')
                        hist_ax.stairs(np.array(self.root.histogram[plot_key + '_hist_1_1_' + str(scan_step)])
                                       -np.array(self.root.histogram[plot_key + '_hist_1_0_' + str(scan_step)])
                                       -np.array(self.root.histogram[plot_key + '_hist_0_1_' + str(scan_step)])
                                       +np.array(self.root.histogram[plot_key + '_hist_0_0_' + str(scan_step)]), edges, label='Signal')

                hist_ax.legend(loc=1)
                hist_ax.axhline(0, color='k')
                hist_ax.minorticks_on()
                hist_ax.set_ylabel('Counts')
                hist_ax.set_xlabel('Time (mu s)')
                hist_ax.set_xlim(edges[0],edges[-1])
                hist_ax.set_position([0.075,0.1,0.915,0.885])

                # Update settings
                item.plot_settings.xmin_entry.delete(0,'end')
                item.plot_settings.xmin_entry.insert(0,str(edges[0]))
                item.plot_settings.xmax_entry.delete(0,'end')
                item.plot_settings.xmax_entry.insert(0,str(edges[-1]))

                item.plot_settings.zero_line.select()

                item.figure.canvas.draw()

    def load_update(self):
        # Reset dropdown and list
        self.detector_list.delete(0, tk.END)
        self.scan_list.delete(0, tk.END)
        self.scan_list.insert(tk.END, 'all')

        for key in self.root.histogram['time_keys']:
            self.detector_list.insert(tk.END, key)
        
        scan_list = np.unique(self.root.parameters[self.root.parameters['scan_key']])
        
        if len(scan_list) > 200:
            for key in scan_list[::int(len(scan_list)/100)]:
                self.scan_list.insert(tk.END, key)
        else:
            for key in scan_list:
                self.scan_list.insert(tk.END, key)

        self.detector_list.selection_set(0, 0)
        self.scan_list.selection_set(0, 0)

        self.plot_hist_but['state'] = 'normal'