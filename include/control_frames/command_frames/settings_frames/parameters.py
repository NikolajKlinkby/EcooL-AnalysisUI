import os
import subprocess
import tkinter as tk
import json
from tkinter import ttk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import numpy as np
from threading import Thread
import time
import traceback
from inspect import signature
from inspect import getfullargspec
from include.FittingRoutine import FittingRoutine
import platform

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

from include.load import *
from include.control_frames.plot_frame import *

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

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

def isint(str):
    try:
        float(str)
        return True
    except ValueError:
        return False

class parameters(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.root = root
        self.container = container
        
        options = {'padx': 5, 'pady': 5}

        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky='nswe')

        # Create a vertical scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='nse')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas to hold the widgets
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw", tags='inner_frame')
        self.inner_frame.grid_propagate(False)

        self.entries = []

        self.header = []

        # Scan variable field
        self.scanlabel = tk.Label(self, text='Scan variable')
        self.scanlabel.grid(row=1, column=0, sticky='w')

        self.scanvariable = tk.StringVar()
        self.scanvariable.set('')

        self.scandropdown = tk.OptionMenu(self, self.scanvariable, self.scanvariable.get(), *[], command=self.on_scan_select)
        self.scandropdown.grid(row=1, column = 1, sticky=tk.E)

        # Bin size and generate hist line

        self.binsizelabel = tk.Label(self, text = r'Bin size (mu s)')
        self.binsizelabel.grid(row=0, column=0, sticky=tk.W)

        self.binsizevar = tk.StringVar()
        self.binsizevar.set('1.00')
        self.binsize = ttk.Entry(self, textvariable=self.binsizevar, validate='key', validatecommand=self.bin_validate)
        self.binsize.grid(row=0, column=0, sticky=tk.E)

        self.genhistbut = tk.Button(self, text='Gen. Hist', command=self.gen_histogram)
        self.genhistbut.grid(row=0, column=1, sticky=tk.E)

        # Function to update scroll region whenever widgets are added or removed
        self.inner_frame.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.update_canvas)

        self.bind('<Configure>', self.resize)

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2 / 50

        # place the window, giving it an explicit size
        self.scrollbar.place(in_=self, relx=1 - padx - scrollbarwidth, rely=0, 
            relwidth=scrollbarwidth, relheight=7/10)
        
        self.canvas.place(in_=self, relx=0, rely=0,
            relwidth=1- 2 * padx - scrollbarwidth, relheight=7/10)
        
        self.scanlabel.place(in_=self, relx=0, rely=7/10 + pady, 
            relwidth=3/10, relheight=1.5/10 - pady)
        
        self.scandropdown.place(in_=self, relx=3/10, rely=7/10 + pady,
            relwidth=7/10, relheight=1.5/10 - pady)
        
        self.binsizelabel.place(in_=self, relx=0, rely=8.5/10 + pady, 
            relwidth=4/10, relheight=1.5/10 - pady)
        
        self.binsize.place(in_=self, relx=4/10, rely=8.5/10 + pady,
            relwidth=3/10, relheight=1.5/10 - pady)
        
        self.genhistbut.place(in_=self, relx=1-3/10, rely=8.5/10 + pady,
            relwidth=3/10, relheight=1.5/10 - pady)
        
        self.update_header()

        self.update_rows()
    
    # Function to update scroll region whenever widgets are added or removed
    def update_canvas(self, event):
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.winfo_width())

    def update_scroll_region(self, event):
        self.update_canvas(event)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.winfo_width())

    def add_header(self):
        
        # Add table header
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = 0

        width = self.canvas.winfo_reqwidth()
        
        if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
            
            parameter_label = ttk.Label(self.inner_frame, text=f'Parameter', borderwidth=1, relief='solid')
            parameter_label.place(x=0, y=y, width=3/10*width, height=height)

            laser_label = ttk.Label(self.inner_frame, text=f'Laser', borderwidth=1, relief='solid')
            laser_label.place(x=3/10*width, y=y, width=2.7/10*width, height=height)

            no_laser_label = ttk.Label(self.inner_frame, text=f'No laser', borderwidth=1, relief='solid')
            no_laser_label.place(x=5.7/10*width, y=y, width=2.7/10*width, height=height)

            enabled_label = ttk.Label(self.inner_frame, text=f'Enabled', borderwidth=1, relief='solid')
            enabled_label.place(x=8.4/10*width, y=y, width=0.6/10*width, height=height)

            self.header = [parameter_label, laser_label, no_laser_label, enabled_label]

        elif self.root.histogram['scan_key'] == 'Delay (fs)_ctr':
            
            parameter_label = ttk.Label(self.inner_frame, text=f'Parameter', borderwidth=1, relief='solid')
            parameter_label.place(x=0, y=y, width=3/10*width, height=height)

            pumpprobe_label = ttk.Label(self.inner_frame, text=f'PumpProbe', borderwidth=1, relief='solid')
            pumpprobe_label.place(x=3/10*width, y=y, width=1.35/10*width, height=height)

            probe_label = ttk.Label(self.inner_frame, text=f'Probe', borderwidth=1, relief='solid')
            probe_label.place(x=4.35/10*width, y=y, width=1.35/10*width, height=height)

            pump_label = ttk.Label(self.inner_frame, text=f'Pump', borderwidth=1, relief='solid')
            pump_label.place(x=5.7/10*width, y=y, width=1.35/10*width, height=height)

            none_label = ttk.Label(self.inner_frame, text=f'None', borderwidth=1, relief='solid')
            none_label.place(x=7.05/10*width, y=y, width=1.35/10*width, height=height)

            enabled_label = ttk.Label(self.inner_frame, text=f'Enabled', borderwidth=1, relief='solid')
            enabled_label.place(x=8.4/10*width, y=y, width=0.6/10*width, height=height)

            self.header = [parameter_label, pumpprobe_label, probe_label, pump_label, none_label, enabled_label]

        else:

            parameter_label = ttk.Label(self.inner_frame, text=f'Parameter', borderwidth=1, relief='solid')
            parameter_label.place(x=0, y=y, width=3/10*width, height=height)

            pumpprobe_label = ttk.Label(self.inner_frame, text=f'i1', borderwidth=1, relief='solid')
            pumpprobe_label.place(x=3/10*width, y=y, width=1.35/10*width, height=height)

            probe_label = ttk.Label(self.inner_frame, text=f'i2', borderwidth=1, relief='solid')
            probe_label.place(x=4.35/10*width, y=y, width=1.35/10*width, height=height)

            pump_label = ttk.Label(self.inner_frame, text=f'i3', borderwidth=1, relief='solid')
            pump_label.place(x=5.7/10*width, y=y, width=1.35/10*width, height=height)

            none_label = ttk.Label(self.inner_frame, text=f'i4', borderwidth=1, relief='solid')
            none_label.place(x=7.05/10*width, y=y, width=1.35/10*width, height=height)

            enabled_label = ttk.Label(self.inner_frame, text=f'Enabled', borderwidth=1, relief='solid')
            enabled_label.place(x=8.4/10*width, y=y, width=0.6/10*width, height=height)

            self.header = [parameter_label, pumpprobe_label, probe_label, pump_label, none_label, enabled_label]
        
        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

    def update_header(self):
        self.canvas.update()

        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = 0

        width = self.canvas.winfo_reqwidth()

        if len(self.header) == 4:
            # Resize table header
            
            self.header[0].place(in_=self.inner_frame, x=0, y=y, width=3/10*width, height=height)

            self.header[1].place(in_=self.inner_frame, x=3/10*width, y=y, width=2.7/10*width, height=height)

            self.header[2].place(in_=self.inner_frame, x=5.7/10*width, y=y, width=2.7/10*width, height=height)

            self.header[3].place(in_=self.inner_frame, x=8.4/10*width, y=y, width=0.6/10*width, height=height)

            self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
            self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        elif len(self.header) == 6:
            # Resize table header
            
            self.header[0].place(in_=self.inner_frame, x=0, y=y, width=3/10*width, height=height)

            self.header[1].place(in_=self.inner_frame, x=3/10*width, y=y, width=1.35/10*width, height=height)

            self.header[2].place(in_=self.inner_frame, x=4.35/10*width, y=y, width=1.35/10*width, height=height)

            self.header[3].place(in_=self.inner_frame, x=5.7/10*width, y=y, width=1.35/10*width, height=height)

            self.header[4].place(in_=self.inner_frame, x=7.05/10*width, y=y, width=1.35/10*width, height=height)

            self.header[5].place(in_=self.inner_frame, x=8.4/10*width, y=y, width=0.6/10*width, height=height)

            self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
            self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

    def del_header(self):
        for i in self.header:
            i.destroy()
        self.header = []

    def add_row(self, param):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = (len(self.entries)+1) * height

        width = self.canvas.winfo_reqwidth()

        if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
        
            label = ttk.Label(self.inner_frame, text=param, background='white', borderwidth=1, relief='solid')
            label.place(x=0, y=y, width=3/10*width, height=height)
            
            entry1 = ttk.Entry(self.inner_frame, validate="key")
            entry1.place(x=3/10*width, y=y, width=2.7/10*width, height=height)
            entry1.insert(0,'[0:0]')
            entry1['validatecommand'] = (entry1.register(self.entry_validate),'%P', '%s', '%W')
            
            entry2 = ttk.Entry(self.inner_frame, validate="key")
            entry2.place(x=5.7/10*width, y=y, width=2.7/10*width, height=height)
            entry2.insert(0,'[0:0]')
            entry2['validatecommand'] = (entry2.register(self.entry_validate),'%P', '%s', '%W')
            
            checkbox_var = tk.IntVar()
            checkbox = tk.Checkbutton(self.inner_frame, variable=checkbox_var)
            checkbox.place(x=8.4/10*width, y=y, width=0.6/10*width, height=height)

            self.entries.append((label, entry1, entry2, checkbox, checkbox_var))

        else:

            label = ttk.Label(self.inner_frame, text=param, background='white', borderwidth=1, relief='solid')
            label.place(x=0, y=y, width=3/10*width, height=height)
            
            entry1 = ttk.Entry(self.inner_frame, validate="key")
            entry1.place(x=3/10*width, y=y, width=1.35/10*width, height=height)
            entry1.insert(0,'[0:0]')
            entry1['validatecommand'] = (entry1.register(self.entry_validate),'%P', '%s', '%W')
            
            entry2 = ttk.Entry(self.inner_frame, validate="key")
            entry2.place(x=4.35/10*width, y=y, width=1.35/10*width, height=height)
            entry2.insert(0,'[0:0]')
            entry2['validatecommand'] = (entry2.register(self.entry_validate),'%P', '%s', '%W')

            entry3 = ttk.Entry(self.inner_frame, validate="key")
            entry3.place(x=5.7/10*width, y=y, width=1.35/10*width, height=height)
            entry3.insert(0,'[0:0]')
            entry3['validatecommand'] = (entry3.register(self.entry_validate),'%P', '%s', '%W')

            entry4 = ttk.Entry(self.inner_frame, validate="key")
            entry4.place(x=7.05/10*width, y=y, width=1.35/10*width, height=height)
            entry4.insert(0,'[0:0]')
            entry4['validatecommand'] = (entry4.register(self.entry_validate),'%P', '%s', '%W')
            
            checkbox_var = tk.IntVar()
            checkbox = tk.Checkbutton(self.inner_frame, variable=checkbox_var)
            checkbox.place(x=8.4/10*width, y=y, width=0.6/10*width, height=height)

            self.entries.append((label, entry1, entry2, entry3, entry4, checkbox, checkbox_var))

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+1) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        
    def update_rows(self):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        width = self.canvas.winfo_reqwidth()

        count = 0
        
        for e in self.entries:
            y = (count+1) * height
            
            if len(e) == 5:

                e[0].place(x=0, y=y, width=3/10*width, height=height)
                e[1].place(x=3/10*width, y=y, width=2.7/10*width, height=height)
                e[2].place(x=5.7/10*width, y=y, width=2.7/10*width, height=height)
                e[3].place(x=8.4/10*width, y=y, width=0.6/10*width, height=height)

            else:

                e[0].place(x=0, y=y, width=3/10*width, height=height)
                e[1].place(x=3/10*width, y=y, width=1.35/10*width, height=height)
                e[2].place(x=4.35/10*width, y=y, width=1.35/10*width, height=height)
                e[3].place(x=5.7/10*width, y=y, width=1.35/10*width, height=height)
                e[4].place(x=7.05/10*width, y=y, width=1.35/10*width, height=height)
                e[5].place(x=8.4/10*width, y=y, width=0.6/10*width, height=height)

            count += 1

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

    def del_all_rows(self):
        for i in self.entries:
            if len(i) == 5:
                for j in range(4):
                    i[j].destroy()
            else:
                for j in range(6):
                    i[j].destroy()
        self.entries = []

    def entry_validate(self, val, prior_val, widget):
        try:
            # Allowing pasting ctrl+v
            if val in ['', '[]', '[', ']']:
                self.after(10, self.entry_ctrl_v, prior_val, widget)
                return True
            
            # Not allowing removing '[' or ']'
            elif val[0] != '[' and val[-1] != ']':
                self.root.nametowidget(widget).delete(0,tk.END)
                self.root.nametowidget(widget).insert(0,'['+val+']')
                return True
            elif val[0] != '[':
                self.root.nametowidget(widget).delete(0,tk.END)
                self.root.nametowidget(widget).insert(0,'['+val)
                return True
            elif val[-1] != ']':
                self.root.nametowidget(widget).delete(0,tk.END)
                self.root.nametowidget(widget).insert(0,val+']')
                return True
            
            # Checking up on the numbers
            elif len(val.split(":"))-1 != 1:
                return False
            elif not isfloat(val.split(":")[0][1:]) and val.split(":")[0][1:] != '':
                return False
            elif not isfloat(val.split(":")[0][1:]) and val.split(":")[0][1:] != '':
                return False
            else:
                return True
        except Exception as e:
            print(e)
            return False

    def entry_ctrl_v(self, prior_val, widget):
        if self.root.nametowidget(widget).get() in ['', '[]', '[', ']']:
            self.root.nametowidget(widget).delete(0,tk.END)
            self.root.nametowidget(widget).insert(0,prior_val)

    def bin_validate(self, val):
        if isfloat(self.binsizevar.get()):
            self.root.bin_size = 1000 * float(self.binsizevar.get())
            return True
        else:
            return False

    def on_scan_select(self, event):
        # Check if current variable is convertable
        if len(np.unique(self.root.parameters[self.scanvariable.get()], return_index=True)[0]) ==  len(np.unique(self.root.parameters[self.root.histogram['scan_key']], return_index=True)[0]):
            
            # Make map between keys.
            old_scan_val = np.unique(self.root.parameters[self.root.histogram['scan_key']], return_index=True)
            new_scan_val = np.array(self.root.parameters[self.scanvariable.get()])[old_scan_val[1]]

            # Check the mapping is linear
            if self.scan_unique_check(np.array([old_scan_val[0], new_scan_val]),np.unique([self.root.parameters[self.root.histogram['scan_key']],self.root.parameters[self.scanvariable.get()]], axis=1)):
                # Set new scan key

                if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                    for old_scan,new_scan in zip(old_scan_val[0], new_scan_val):
                        for key in self.root.histogram['time_keys']:
                            self.root.histogram[key + '_hist_1_'+str(new_scan)] = self.root.histogram.pop(key + '_hist_1_'+str(old_scan))
                            self.root.histogram[key + '_hist_0_'+str(new_scan)] = self.root.histogram.pop(key + '_hist_0_'+str(old_scan))
                else:
                    for old_scan,new_scan in zip(old_scan_val[0], new_scan_val):
                        for key in self.root.histogram['time_keys']:
                            self.root.histogram[key + '_hist_1_1_'+str(new_scan)] = self.root.histogram.pop(key + '_hist_1_1_'+str(old_scan))
                            self.root.histogram[key + '_hist_0_0_'+str(new_scan)] = self.root.histogram.pop(key + '_hist_0_0_'+str(old_scan))
                            self.root.histogram[key + '_hist_1_0_'+str(new_scan)] = self.root.histogram.pop(key + '_hist_1_0_'+str(old_scan))
                            self.root.histogram[key + '_hist_0_1_'+str(new_scan)] = self.root.histogram.pop(key + '_hist_0_1_'+str(old_scan))

                self.root.histogram['scan_key'] = self.scanvariable.get()

                # Write to file
                selection_to_load = self.root.folder_path+'/'+self.root.run_choosen
                f = open(os_format_string(selection_to_load+'/PythonAnalysis/hist.txt'), 'w')
                f.write(json.dumps(self.root.histogram, cls=NumpyEncoder))
                f.close()
            
                # Update histogram scan values
                self.root.Command.plotoptframe.histogram.load_update()

                # Update histogram plots
                self.update_histogram_plots(old_scan_val[0], new_scan_val)
                
                # Update result plots
                self.update_result_plots()

    def scan_unique_check(self, list1, list2):
        for i in range(len(list1[0])):
            if list1[0][i] != list2[0][i] or list1[1][i] != list2[1][i]:
                return False
        else:
            return True

    def update_scan_dropdown(self, var, string):
        var.set(string)
        self.on_scan_select(1)

    def schedule_check(self,t):
        if t.is_alive():
            self.after(50, lambda: self.schedule_check(t))

    def gen_histogram(self):
        # Handle if there are too many values
        if len(np.unique(self.root.parameters[self.scanvariable.get()])) > 999:
            self.cont = True
            toplevel = self.hist_proceed(self, len(np.unique(self.root.parameters[self.scanvariable.get()])))
            toplevel.wait_window(toplevel)
            
            # Continue
            if not self.cont:
                return
        
        t = self.ThreadClient(self.root.queue, self.gen_histogram_thread)
        t.start()
        self.schedule_check(t)

    def gen_histogram_thread(self):        
        self.root.disable_buttons()
        
        depletion = self.container.calculations.depcheck_var.get()
        depletion_flag = self.root.settings['depletion_flag']
        depletion_low = self.root.settings['depletion_low']
        depletion_high = self.root.settings['depletion_high']

        max_TDC_chanels = int(self.root.settings['max_TDC_chanels'])

        #Get depletion masks
        masks = []
        if depletion:
            # For non depleted
            if len(self.entries[0]) == 5:
                masks.append([depletion_flag,depletion_low[0],depletion_low[1],depletion_low[0],depletion_low[1]])
            elif len(self.entries[0]) == 7:
                masks.append([depletion_flag,depletion_low[0],depletion_low[1],depletion_low[0],depletion_low[1],
                                            depletion_low[0],depletion_low[1],depletion_low[0],depletion_low[1]])

        # Get masks to apply
        for entry in self.entries:
            if len(entry) == 5:
                if entry[4].get():
                    if isfloat(entry[1].get().split(":")[0][1:]) and \
                        isfloat(entry[1].get().split(":")[1][:-1]) and \
                        isfloat(entry[2].get().split(":")[0][1:]) and \
                        isfloat(entry[2].get().split(":")[1][:-1]):
                        if depletion and entry[0]['text'] not in np.array(masks)[:,0]:
                                masks.append([entry[0]['text'], entry[1].get().split(":")[0][1:], entry[1].get().split(":")[1][:-1], entry[2].get().split(":")[0][1:], entry[2].get().split(":")[1][:-1]])
                        else:
                            masks.append([entry[0]['text'], entry[1].get().split(":")[0][1:], entry[1].get().split(":")[1][:-1], entry[2].get().split(":")[0][1:], entry[2].get().split(":")[1][:-1]])
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
                    if depletion and entry[0]['text'] not in np.array(masks)[:,0]:
                        masks.append([entry[0]['text'], entry[1].get().split(":")[0][1:], entry[1].get().split(":")[1][:-1], entry[2].get().split(":")[0][1:], entry[2].get().split(":")[1][:-1],
                                     entry[3].get().split(":")[0][1:], entry[3].get().split(":")[1][:-1], entry[4].get().split(":")[0][1:], entry[4].get().split(":")[1][:-1]])
                    else:
                        masks.append([entry[0]['text'], entry[1].get().split(":")[0][1:], entry[1].get().split(":")[1][:-1], entry[2].get().split(":")[0][1:], entry[2].get().split(":")[1][:-1],
                                    entry[3].get().split(":")[0][1:], entry[3].get().split(":")[1][:-1], entry[4].get().split(":")[0][1:], entry[4].get().split(":")[1][:-1]])

                else:
                    print(time.strftime('%H:%M:%S', time.gmtime())+' Error using '+entry[0]['text']+' limits')

        # Generate new histogram
        self.root.histogram.clear()
        selection_to_load = self.root.folder_path+'/'+self.root.run_choosen
        # Hist limits
        hist_limits = [self.root.parameters['TDC.min'][0],self.root.parameters['TDC.max'][0]]
        if self.root.parameters['TDC.max'][0] - self.root.parameters['TDC.min'][0] > max_TDC_chanels:
            hist_limits[0] = self.root.parameters['TDC.max'][0] - max_TDC_chanels

        self.root.histogram = load_histogram([selection_to_load+'/JSON/'+self.root.run_choosen], write=selection_to_load+'/PythonAnalysis/hist.txt', 
                                             nr_bins=self.root.bin_size, overwrite=True, scan_key = self.scanvariable.get(), masks = masks,
                                             hist_limits=hist_limits)

        if depletion:
            # For depleted
            for m in range(len(masks)):
                if masks[m][0] == depletion_flag:
                    if len(self.entries[0]) == 5:
                        masks[m] = [depletion_flag,depletion_high[0],depletion_high[1],depletion_high[0],depletion_high[1]]
                    elif len(self.entries[0]) == 7:
                        masks[m] = [depletion_flag,depletion_high[0],depletion_high[1],depletion_high[0],depletion_high[1],
                                                    depletion_high[0],depletion_high[1],depletion_high[0],depletion_high[1]]

            # Generate depleted histogram
            self.root.histogram_deplete.clear()
            self.root.histogram_deplete = load_histogram([selection_to_load+'/JSON/'+self.root.run_choosen], write=selection_to_load+'/PythonAnalysis/hist_deplete.txt', 
                                             nr_bins=self.root.bin_size, overwrite=True, scan_key = self.scanvariable.get(), masks = masks,
                                             hist_limits=hist_limits)

        # Update calculations
        self.container.calculations.calculate()

        # Update histogram scan values
        self.root.Command.plotoptframe.histogram.load_update()
        
        # Delete histogram plots except for accumulated histogram
        self.delete_histogram_plots()
        self.update_histogram_plots()
        self.container.calculations.load_calc_files()

        # Update result plots
        self.update_result_plots()

        self.load_update()

        self.root.enable_buttons()
        
    def delete_histogram_plots(self):
        for item in self.root.tab_bar.winfo_children():
            if len(self.root.tab_bar.tab(item)['text'].split(' ')) > 1:
                if self.root.tab_bar.tab(item)['text'].split(' ')[1] in self.root.histogram['scan_key']:
                    if len(self.root.tab_bar.winfo_children()) > 1:
                        item.destroy()
                    else:
                        self.root.tab_bar.add(plot_frame(self.root.tab_bar, self.root), text="Empty Plot")
                        item.destroy()
                        return

    def update_histogram_plots(self, old_scan = np.array([None]), new_scan = np.array([None])):
        current_selection = self.root.tab_bar.index(self.root.tab_bar.select())

        for item in self.root.tab_bar.winfo_children():
            # Check if it is a prevoius data tab
            if self.privious_tab_check(self.root.tab_bar.tab(item)['text']):
                pass
            
            # Check if it is a parameter tab
            elif self.check_from_options(self.root.tab_bar.tab(item)['text'],self.root.parameters['flags']):
                pass
            
            # Check if it is a histogram
            elif len(self.root.tab_bar.tab(item)['text'].split(' ')) == 2:
                # Check for old scan value named tabs 
                if np.any(old_scan != None) and np.any(new_scan != None):
                    truth, index = self.list_check(self.root.tab_bar.tab(item)['text'].split(' ')[1],old_scan)
                    if truth:
                        # Rename tab
                        self.root.tab_bar.tab(self.root.tab_bar.index(item), text=self.root.tab_bar.tab(item)['text'].split(' ')[0]+' '+str(new_scan[index]))
                        
                        # Plot new

                        self.root.Command.plotoptframe.histogram.detector_list.selection_clear(0,'end')
                        self.root.Command.plotoptframe.histogram.scan_list.selection_clear(0,'end')
                        
                        _, det_ind = self.list_check('TDC1.'+self.root.tab_bar.tab(item)['text'].split(' ')[0],np.array(self.root.Command.plotoptframe.histogram.detector_list.get(0,'end')))
                        _, scan_ind = self.list_check(new_scan[index],np.array(self.root.Command.plotoptframe.histogram.scan_list.get(0,'end')))

                        self.root.Command.plotoptframe.histogram.detector_list.selection_set(det_ind)
                        self.root.Command.plotoptframe.histogram.scan_list.selection_set(scan_ind)
                        
                        self.root.tab_bar.select(self.root.tab_bar.index(item))
                        self.root.Command.plotoptframe.histogram.plot_hist()

                    elif self.root.tab_bar.tab(item)['text'].split(' ')[1] == 'all':
                        # Plot new
                        self.root.tab_bar.select(self.root.tab_bar.index(item))
                        self.root.Command.plotoptframe.histogram.plot_hist()
                
                # Check for scan value named tabs
                elif self.check_from_options(self.root.tab_bar.tab(item)['text'].split(' ')[1],self.root.parameters[self.root.histogram['scan_key']]) or \
                    self.root.tab_bar.tab(item)['text'].split(' ')[1] == 'all':
                    
                    self.root.Command.plotoptframe.histogram.detector_list.selection_clear(0,'end')
                    self.root.Command.plotoptframe.histogram.scan_list.selection_clear(0,'end')

                    _, det_ind = self.list_check('TDC1.'+self.root.tab_bar.tab(item)['text'].split(' ')[0],np.array(self.root.Command.plotoptframe.histogram.detector_list.get(0,'end')))
                    _, scan_ind = self.list_check(self.root.tab_bar.tab(item)['text'].split(' ')[1],np.array(self.root.Command.plotoptframe.histogram.scan_list.get(0,'end')))

                    self.root.Command.plotoptframe.histogram.detector_list.selection_set(det_ind)
                    self.root.Command.plotoptframe.histogram.scan_list.selection_set(scan_ind)
                    
                    # Plot new
                    self.root.tab_bar.select(self.root.tab_bar.index(item))
                    self.root.Command.plotoptframe.histogram.plot_hist()

        self.root.tab_bar.select(current_selection)

    def list_check(self, val, list):
        index = 0
        for v in list:
            if str(val) == str(v):
                return True, index
            index += 1
        else:
            return False, index

    def update_result_plots(self):
        current_selection = self.root.tab_bar.index(self.root.tab_bar.select())

        for item in self.root.tab_bar.winfo_children():
            # Check if it is a prevoius data tab
            if self.privious_tab_check(self.root.tab_bar.tab(item)['text']):
                pass

            # Check if it is a parameter tab
            elif self.check_from_options(self.root.tab_bar.tab(item)['text'],['Result']):
                self.root.tab_bar.select(self.root.tab_bar.index(item))
                self.root.Command.results.plot_results()
            
        self.root.tab_bar.select(current_selection)

    def privious_tab_check(self, text):
        if len(text.split('_')) > 1:
            if isint(text.split('_')[0]):
                return True
            else:
                return False
        else:
            return False

    def check_from_options(self,text,options):
        for opt in options:
            if text == str(opt):
                return True
        else:
            return False

    def load_update(self):
        # Reset dropdown and list
        self.scanvariable.set('')
        self.scandropdown['menu'].delete(0, 'end')
        self.del_all_rows()
        self.del_header()

        self.add_header()

        # New list
        for key in self.root.parameters['flags']:# Add variables to scan variable and list
            self.scandropdown['menu'].add_command(label=key, command=lambda x=key: self.update_scan_dropdown(self.scanvariable, x))
            self.add_row(key)
            
            if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                self.entries[-1][1].config(validate='none')
                self.entries[-1][1].delete(0,'end')
                self.entries[-1][2].config(validate='none')
                self.entries[-1][2].delete(0,'end')
                min = np.min(self.root.parameters[key])
                max = np.max(self.root.parameters[key])
                self.entries[-1][1].insert(0,'[' + str(min) + ':' + str(max) + ']')
                self.entries[-1][1].config(validate='key')
                self.entries[-1][2].insert(0,'[' + str(min) + ':' + str(max) + ']')
                self.entries[-1][2].config(validate='key')
            else:
                self.entries[-1][1].config(validate='none')
                self.entries[-1][1].delete(0,'end')
                self.entries[-1][2].config(validate='none')
                self.entries[-1][2].delete(0,'end')
                self.entries[-1][3].config(validate='none')
                self.entries[-1][3].delete(0,'end')
                self.entries[-1][4].config(validate='none')
                self.entries[-1][4].delete(0,'end')
                min = np.min(self.root.parameters[key])
                max = np.max(self.root.parameters[key])
                self.entries[-1][1].insert(0,'[' + str(min) + ':' + str(max) + ']')
                self.entries[-1][1].config(validate='key')
                self.entries[-1][2].insert(0,'[' + str(min) + ':' + str(max) + ']')
                self.entries[-1][2].config(validate='key')
                self.entries[-1][3].insert(0,'[' + str(min) + ':' + str(max) + ']')
                self.entries[-1][3].config(validate='key')
                self.entries[-1][4].insert(0,'[' + str(min) + ':' + str(max) + ']')
                self.entries[-1][4].config(validate='key')

            # Apply masks
            if 'masks' in self.root.histogram.keys():
                for mask in self.root.histogram['masks']:
                    if key == mask[0]:
                        if len(mask) == 5:
                            self.entries[-1][1].config(validate='none')
                            self.entries[-1][1].delete(0,'end')
                            self.entries[-1][1].insert(0,'[' + mask[1] + ':' + mask[2] + ']')
                            self.entries[-1][1].config(validate='key')
                            self.entries[-1][2].config(validate='none')
                            self.entries[-1][2].delete(0,'end')
                            self.entries[-1][2].insert(0,'[' + mask[3] + ':' + mask[4] + ']')
                            self.entries[-1][2].config(validate='key')
                            self.entries[-1][4].set(True)
                        elif len(mask) == 9:
                            self.entries[-1][1].config(validate='none')
                            self.entries[-1][1].delete(0,'end')
                            self.entries[-1][1].insert(0,'[' + mask[1] + ':' + mask[2] + ']')
                            self.entries[-1][1].config(validate='key')
                            self.entries[-1][2].config(validate='none')
                            self.entries[-1][2].delete(0,'end')
                            self.entries[-1][2].insert(0,'[' + mask[3] + ':' + mask[4] + ']')
                            self.entries[-1][2].config(validate='key')
                            self.entries[-1][3].config(validate='none')
                            self.entries[-1][3].delete(0,'end')
                            self.entries[-1][3].insert(0,'[' + mask[5] + ':' + mask[6] + ']')
                            self.entries[-1][3].config(validate='key')
                            self.entries[-1][4].config(validate='none')
                            self.entries[-1][4].delete(0,'end')
                            self.entries[-1][4].insert(0,'[' + mask[7] + ':' + mask[8] + ']')
                            self.entries[-1][4].config(validate='key')
                            self.entries[-1][6].set(True)
                        break
                else:
                    if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                        self.entries[-1][1].config(validate='none')
                        self.entries[-1][1].delete(0,'end')
                        self.entries[-1][2].config(validate='none')
                        self.entries[-1][2].delete(0,'end')
                        min = np.min(self.root.parameters[key])
                        max = np.max(self.root.parameters[key])
                        self.entries[-1][1].insert(0,'[' + str(min) + ':' + str(max) + ']')
                        self.entries[-1][1].config(validate='key')
                        self.entries[-1][2].insert(0,'[' + str(min) + ':' + str(max) + ']')
                        self.entries[-1][2].config(validate='key')
                    else:
                        self.entries[-1][1].config(validate='none')
                        self.entries[-1][1].delete(0,'end')
                        self.entries[-1][2].config(validate='none')
                        self.entries[-1][2].delete(0,'end')
                        self.entries[-1][3].config(validate='none')
                        self.entries[-1][3].delete(0,'end')
                        self.entries[-1][4].config(validate='none')
                        self.entries[-1][4].delete(0,'end')
                        min = np.min(self.root.parameters[key])
                        max = np.max(self.root.parameters[key])
                        self.entries[-1][1].insert(0,'[' + str(min) + ':' + str(max) + ']')
                        self.entries[-1][1].config(validate='key')
                        self.entries[-1][2].insert(0,'[' + str(min) + ':' + str(max) + ']')
                        self.entries[-1][2].config(validate='key')
                        self.entries[-1][3].insert(0,'[' + str(min) + ':' + str(max) + ']')
                        self.entries[-1][3].config(validate='key')
                        self.entries[-1][4].insert(0,'[' + str(min) + ':' + str(max) + ']')
                        self.entries[-1][4].config(validate='key')
            
        # Set scan variable
        self.scanvariable.set(self.root.histogram['scan_key'])

    class ThreadClient(Thread):
        def __init__(self, queue, fcn):
            Thread.__init__(self)
            self.queue = queue
            self.fcn = fcn
        def run(self):
            time.sleep(1)
            self.queue.put(self.fcn())

    class hist_proceed(tk.Toplevel):
        def __init__(_self, self, val, *args, **kwargs):
            super().__init__(self, *args, **kwargs)
            _self.title("Generate Histogram")

            # Create a label in the Toplevel window
            label = tk.Label(_self, text=f'There are {val} scan steps\nDo you wish to proceed')
            label.pack(padx=10, pady=10)

            # Create "Continue" and "Cancel" buttons in the Toplevel window
            continue_button = tk.Button(_self, text="Continue", command=lambda : _self.continue_action(self))
            cancel_button = tk.Button(_self, text="Cancel", command=lambda : _self.cancel_action(self))

            continue_button.pack(side=tk.LEFT, padx=5, pady=5)
            cancel_button.pack(side=tk.RIGHT, padx=5, pady=5)

        def continue_action(_self, self):
            _self.destroy()

        def cancel_action(_self, self):
            self.cont = False
            _self.destroy()