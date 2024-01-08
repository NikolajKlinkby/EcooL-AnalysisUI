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

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class calculations(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.root = root
        self.container = container
        
        options = {'padx': 5, 'pady': 5}

        # Photon and saturation and depletion
        self.photonlabel = tk.Label(self, text='#Photons')
        self.photonlabel.grid(row = 0, column = 0)

        self.photonentry = tk.Entry(self, background='white')
        self.photonentry.insert(0,'1')
        self.photonentry.grid(row = 0, column = 1)

        self.satlabel = tk.Label(self, text='Saturation')
        self.satlabel.grid(row = 1, column = 0)

        self.satentry = tk.Entry(self, background='white')
        self.satentry.insert(0,'0')
        self.satentry.grid(row = 1, column = 1)

        self.deplabel = tk.Label(self, text='Depletion')
        self.deplabel.grid(row = 1, column = 0)

        self.depcheck_var = tk.IntVar()
        self.depcheck = tk.Checkbutton(self, variable=self.depcheck_var, command=self.depletion_on_select)
        self.depcheck.grid(row = 1, column = 1)

        # Bakcground detector and calculation scheme
        self.back_label = tk.Label(self, text='Background Detector')
        self.back_label.grid(row=0, column=2)

        self.back_det_men_var = tk.StringVar()
        self.back_det_men_var.set('')
        self.back_det_men = ttk.OptionMenu(self, self.back_det_men_var, self.back_det_men_var.get(), *[])
        self.back_det_men.grid(row=1, column=2)

        self.calc_file_var = tk.StringVar()
        self.calc_file_var.set('')
        self.calc_file_men = ttk.OptionMenu(self, self.calc_file_var, self.calc_file_var.get(), *[], command=self.display_calc_file)
        self.calc_file_men.grid(row=2, column=2)

        # Reset calculation buttons
        self.reset_label = tk.Label(self, text='Reset calculation')
        self.reset_label.grid(row=2, column=0)

        self.resetbut = tk.Button(self, text='Reset', command=self.load_calc_files)
        self.resetbut['state'] = 'disabled'
        self.resetbut.grid(row=3, column=0)

        self.recalcbut= tk.Button(self, text='ReCalc', command=self.calculate)
        self.recalcbut['state'] = 'disabled'
        self.recalcbut.grid(row=4, column=0)

        self.file_entry = tk.Text(self)
        self.file_entry.insert('end', '')
        self.file_entry.grid(row=3, column=2)

        self.scrollbar = tk.Scrollbar(self, command=self.file_entry.yview)
        self.scrollbar.grid(row=3, column=2)
        self.file_entry.config(yscrollcommand=self.scrollbar.set)

        # Resize
        self.bind('<Configure>', self.resize)

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2 / 50

        # Photon and saturation
        self.photonlabel.place(in_=self, relx=1/10+padx, rely=pady, 
            relwidth=3/10-padx, relheight=2/15-2*pady/3)
        
        self.photonentry.place(in_=self, relx=0, rely=pady,
            relwidth=1/10, relheight=2/15-2*pady/3)
        
        self.satlabel.place(in_=self, relx=1/10+padx, rely=pady+2/15, 
            relwidth=3/10-padx, relheight=2/15-2*pady/3)
        
        self.satentry.place(in_=self, relx=0, rely=pady+2/15,
            relwidth=1/10, relheight=2/15-2*pady/3)
        
        self.deplabel.place(in_=self, relx=1/10+padx, rely=pady+4/15, 
            relwidth=3/10-padx, relheight=2/15-2*pady/3)
        
        self.depcheck.place(in_=self, relx=0, rely=pady+4/15,
            relwidth=1/10, relheight=2/15-2*pady/3)
        
        # Background detector and calculation scheme

        self.back_label.place(in_=self, relx=1/2, rely=pady,
            relwidth=1/2 - padx, relheight=1/5 - 2 * pady)
        
        self.back_det_men.place(in_=self, relx=1/2, rely=pady+1/5, 
            relwidth=1/2 - padx, relheight=1/5- 2 * pady)
        
        self.calc_file_men.place(in_=self, relx=1/2, rely=pady+2/5,
            relwidth=1/2 - padx, relheight=1/5 - 2 * pady)
        
        # Reset calculation buttons
        
        self.file_entry.place(in_=self, relx=1/3 + padx, rely=3/5,
            relwidth=2/3 - 2 * padx - scrollbarwidth, relheight=2/5)
        
        self.scrollbar.place(in_=self, relx=1 - padx - scrollbarwidth, rely=3/5,
            relwidth=scrollbarwidth, relheight=2/5)
        
        self.reset_label.place(in_=self, relx=padx, rely=2/5, 
            relwidth=2/5 - 2 * padx, relheight=1/5)
        
        self.resetbut.place(in_=self, relx=padx, rely=3/5,
            relwidth=1/3 - 2 * padx, relheight=1/5)
        
        self.recalcbut.place(in_=self, relx=padx, rely=4/5,
            relwidth=1/3 - 2 * padx, relheight=1/5)

    def load_calc_files(self):
        # Reset dropdown
        self.calc_file_var.set('')
        self.calc_file_men['menu'].delete(0, 'end')

        if 'scan_key' in self.root.histogram.keys():
            if self.root.histogram['scan_key'] == 'Wavelength_ctr':
                # New list
                for file in os.listdir(os.getcwd()+'/calculation_files/ekspla'):
                    self.calc_file_men['menu'].add_command(label=file[:file.rfind('.')], command=lambda x=file[:file.rfind('.')]: self.update_calc_dropdown(self.calc_file_var, x))

                    self.calc_file_var.set(file[:file.rfind('.')])

            elif self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                # New list
                for file in os.listdir(os.getcwd()+'/calculation_files/transmission'):
                    self.calc_file_men['menu'].add_command(label=file[:file.rfind('.')], command=lambda x=file[:file.rfind('.')]: self.update_calc_dropdown(self.calc_file_var, x))

                    self.calc_file_var.set(file[:file.rfind('.')])
            elif self.root.histogram['scan_key'] == 'Delay (fs)_ctr':
                # New list
                for file in os.listdir(os.getcwd()+'/calculation_files/delay_stage'):
                    self.calc_file_men['menu'].add_command(label=file[:file.rfind('.')], command=lambda x=file[:file.rfind('.')]: self.update_calc_dropdown(self.calc_file_var, x))

                    self.calc_file_var.set(file[:file.rfind('.')])
            else:
                # New list
                for file in os.listdir(os.getcwd()+'/calculation_files/others'):
                    self.calc_file_men['menu'].add_command(label=file[:file.rfind('.')], command=lambda x=file[:file.rfind('.')]: self.update_calc_dropdown(self.calc_file_var, x))

                    self.calc_file_var.set(file[:file.rfind('.')])
        else:
            # New list
            for file in os.listdir(os.getcwd()+'/calculation_files/others'):
                self.calc_file_men['menu'].add_command(label=file[:file.rfind('.')], command=lambda x=file[:file.rfind('.')]: self.update_calc_dropdown(self.calc_file_var, x))

                self.calc_file_var.set(file[:file.rfind('.')])

        self.display_calc_file()

    def update_calc_dropdown(self, var, string):
        var.set(string)
        self.display_calc_file()

    def display_calc_file(self):
        state = self.file_entry['state']
       
        # Reset
        self.file_entry.configure(state='normal')
        self.file_entry.delete(1.0,'end')

        # Get file
        file = self.calc_file_var.get()
        for dir, _, fil in os.walk(os.getcwd()+'/calculation_files'):
            for f in fil:
                if file in f:
                    file = dir+'/'+f
               
        # Read
        with open(file, 'r') as f:
            self.file_entry.insert('end',f.read())
            
        self.file_entry.configure(state=state)
        
    def load_update(self):
        # Enable buttons
        self.resetbut['state'] = 'normal'
        self.recalcbut['state'] = 'normal'

        # Reset dropdown
        self.back_det_men_var.set('')
        self.back_det_men['menu'].delete(0, 'end')

        # New list
        for key in self.root.histogram['time_keys']:# Add variables to scan variable and list
            self.back_det_men['menu'].add_command(label=key, command=tk._setit(self.back_det_men_var, key))

            self.back_det_men_var.set(key)
        
        self.load_calc_files()

        # Depletion
        if self.root.histogram.keys() == self.root.histogram_deplete.keys():
            self.depcheck_var.set(1)
        
        # Calculate 
        selection_to_load = self.root.folder_path+'/'+self.root.run_choosen+'/PythonAnalysis/calculations.txt'
        if os.path.exists(selection_to_load):
            f = open(selection_to_load, 'r')
            self.root.calculations = json.loads(f.read())
            f.close()
            self.container.datapathsettings.calclabel.config(text = 'Calc: V')
        else:
            self.root.calculations = dict()

    def calculate_thread(self):
        self.root.calculations = dict()
        
        selection_to_load = self.root.folder_path+'/'+self.root.run_choosen+'/PythonAnalysis/calculations.txt'
        self.root.disable_buttons()
        
        print(time.strftime('%H:%M:%S', time.gmtime())+' Calculating')
        try:
            exec(self.file_entry.get(1.0,'end'))
            
            self.container.datapathsettings.calclabel.config(text = 'Calc: V')
            self.root.Command.results.update_lists_in_row()
            
            print(time.strftime('%H:%M:%S', time.gmtime())+' Calculations done')
            
            # Write to file
            f = open(selection_to_load, 'w')
            f.write(json.dumps(self.root.calculations, cls=NumpyEncoder))
            f.close()

        except Exception as error:
            print(time.strftime('%H:%M:%S', time.gmtime())+'An error occurred:')
            print(type(error).__name__, "-", error)

        self.root.enable_buttons()

    def calculate(self):
        t = self.ThreadClient(self.root.queue, self.calculate_thread)
        t.start()
        self.schedule_check(t)

    def depletion_on_select(self):
        self.container.parameters.gen_histogram()

    def schedule_check(self,t):
        if t.is_alive():
            self.after(50, lambda: self.schedule_check(t))

    class ThreadClient(Thread):
        def __init__(self, queue, fcn):
            Thread.__init__(self)
            self.queue = queue
            self.fcn = fcn
        def run(self):
            time.sleep(1)
            self.queue.put(self.fcn())