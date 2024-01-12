import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import numpy as np
import json
import time
from threading import Thread
import traceback
from inspect import signature
from inspect import getfullargspec
from src.FittingRoutine import FittingRoutine

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

def isint(str):
    try:
        float(str)
        return True
    except ValueError:
        return False

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
    
class results_frame(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.container = container
        self.root = root

        # Lists to choose from
        self.type_options = []
        self.calculated_options = []
        self.detector_options = []
        self.index_options = []
        
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

        # Add table header
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = (len(self.entries)+1) * height

        width = self.canvas.winfo_reqwidth()/1.5
        
        self.type_label = ttk.Label(self.inner_frame, text=f'Type', borderwidth=1, relief='solid')
        self.type_label.place(x=0, y=y, width=3/14*width, height=height)

        self.detector_label = ttk.Label(self.inner_frame, text=f'Detector/Window', borderwidth=1, relief='solid')
        self.detector_label.place(x=3/14*width, y=y, width=5/14*width, height=height)

        self.index_label = ttk.Label(self.inner_frame, text=f'Index', borderwidth=1, relief='solid')
        self.index_label.place(x=8/14*width, y=y, width=2/14*width, height=height)

        self.error_label = ttk.Label(self.inner_frame, text=f'Erors', borderwidth=1, relief='solid')
        self.error_label.place(x=10/14*width, y=y, width=1/14*width, height=height)

        self.figure_label = ttk.Label(self.inner_frame, text=f'Figure', borderwidth=1, relief='solid')
        self.figure_label.place(x=11/14*width, y=y, width=1/14*width, height=height)

        self.enabled_label = ttk.Label(self.inner_frame, text=f'Enable', borderwidth=1, relief='solid')
        self.enabled_label.place(x=12/14*width, y=y, width=1/14*width, height=height)

        self.delete_label = ttk.Label(self.inner_frame, text=f'Delete', borderwidth=1, relief='solid')
        self.delete_label.place(x=12/14*width, y=y, width=1/14*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        # Buttons
        self.plotresultbut = tk.Button(self, text='Plot Results', command=self.plot_results)
        self.plotresultbut.grid(row=0, column=0)

        self.loaddefaultbut = tk.Button(self, text='Load Default', command=self.load_default)
        self.loaddefaultbut.grid(row=0, column=0)

        self.plusbut = tk.Button(self, text='+', command=self.add_row)
        self.plusbut.grid(row=0, column=0)

        self.resultsetting_var = tk.StringVar()
        self.resultsetting_var.set('Default')
        self.resultsetting = tk.OptionMenu(self, self.resultsetting_var, self.resultsetting_var.get(), *[])
        self.resultsetting.grid(row = 0, column = 0)

        self.loadsettingbut = tk.Button(self, text='Load Settings', command=self.load_settings)
        self.loaddefaultbut.grid(row=0, column =0)

        self.savesettingsbut = tk.Button(self, text='Save Settings', command=self.save_settings)
        self.savesettingsbut.grid(row=0, column=0)
        
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
            relwidth=scrollbarwidth, relheight=8.75/10)
        
        self.canvas.place(in_=self, relx=0, rely=0,
            relwidth=1- 2 * padx - scrollbarwidth, relheight=8.75/10)
        
        # Resize buttons
        self.plotresultbut.place(in_=self, relx=0, rely=8.75/10 + pady,
            relwidth=2.25/15-padx, relheight=1.25/10 - pady)

        self.loaddefaultbut.place(in_=self, relx=2.25/15, rely=8.75/10 + pady,
            relwidth=2.25/15, relheight=1.25/10 - pady)

        self.plusbut.place(in_=self, relx=4.5/15, rely=8.75/10 + pady,
            relwidth=0.5/15, relheight=1.25/10 - pady)

        self.resultsetting.place(in_=self, relx=1/3+padx, rely=8.75/10 + pady,
            relwidth=1/3-padx, relheight=1.25/10 - pady)

        self.loadsettingbut.place(in_=self, relx=2/3+padx, rely=8.75/10 + pady,
            relwidth=1/6-padx, relheight=1.25/10 - pady)

        self.savesettingsbut.place(in_=self, relx=5/6+padx, rely=8.75/10 + pady,
            relwidth=1/6-padx, relheight=1.25/10 - pady)
        
        # Resize table header
        
        self.canvas.update()

        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = 0

        width = self.canvas.winfo_reqwidth()
        
        self.type_label.place(in_=self.inner_frame, x=0, y=y, width=2/14*width, height=height)

        self.detector_label.place(in_=self.inner_frame, x=2/14*width, y=y, width=5/14*width, height=height)

        self.index_label.place(in_=self.inner_frame, x=7/14*width, y=y, width=2/14*width, height=height)

        self.error_label.place(in_=self.inner_frame, x=9/14*width, y=y, width=1/14*width, height=height)

        self.figure_label.place(in_=self.inner_frame, x=10/14*width, y=y, width=1/14*width, height=height)

        self.enabled_label.place(in_=self.inner_frame, x=11/14*width, y=y, width=1/14*width, height=height)

        self.delete_label.place(in_=self.inner_frame, x=12/14*width, y=y, width=1/14*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        self.update_rows()
    
    def update_canvas(self, event):
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.winfo_width())

    def update_scroll_region(self, event):
        self.update_canvas(event)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.winfo_width())

    def add_row(self):
        self.update_lists()

        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = (len(self.entries)+1) * height

        width = self.canvas.winfo_reqwidth()
        
        type_variable = tk.StringVar()
        type_variable.set('')

        type_optmen = ttk.OptionMenu(self.inner_frame, type_variable, type_variable.get(), *self.type_options, command=lambda e: self.type_opt_func(type_optmen))
        type_optmen.place(x=0, y=y, width=2/14*width, height=height)
        
        det_variable = tk.StringVar()
        det_variable.set('')

        det_optmen = ttk.OptionMenu(self.inner_frame, det_variable, det_variable.get(), *[])
        det_optmen.place(x=2/14*width, y=y, width=5/14*width, height=height)
        det_optmen['state'] = 'disabled'
        
        ind_variable = tk.StringVar()
        ind_variable.set('')

        ind_optmen = ttk.OptionMenu(self.inner_frame, ind_variable, ind_variable.get(), *[])
        ind_optmen.place(x=7/14*width, y=y, width=2/14*width, height=height)
        ind_optmen['state'] = 'disabled'
        
        err_var = tk.IntVar()
        err_var.set(1)
        err_checkbox = tk.Checkbutton(self.inner_frame, variable=err_var)
        err_checkbox.place(x=9/14*width, y=y, width=1/14*width, height=height)

        entry = ttk.Entry(self.inner_frame, validate='key')
        entry.insert(0, f'{len(self.entries)+1}')
        entry['validatecommand'] = (entry.register(self.valid_figure_input),'%P')
        entry.place(x=10/14*width, y=y, width=1/14*width, height=height)

        enable_var = tk.IntVar()
        enable_var.set(1)
        enable_checkbox = tk.Checkbutton(self.inner_frame, variable=enable_var)
        enable_checkbox.place(x=11/14*width, y=y, width=1/14*width, height=height)

        checkbox = ttk.Checkbutton(self.inner_frame, command=lambda :self.delbut(type_optmen))
        checkbox.place(x=12/14*width, y=y, width=1/14*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        
        self.entries.append((type_optmen, det_optmen, ind_optmen, err_checkbox, entry, enable_checkbox, checkbox, type_variable, det_variable, ind_variable, err_var, enable_var))

    def delbut(self,event):
        # Delete row
        row = self.find_row(event)
        self.del_row(row)
        
        # Move rows up
        self.update_rows()

    def del_row(self, row):
        # Delete row visually
        for j in range(7):
            self.entries[row][j].destroy()

        # Make new entry list
        new_list = []
        for r in range(len(self.entries)):
            if r != row:
                new_list.append(self.entries[r])
        self.entries = new_list

    def del_all_rows(self):
        # Delete row visually
        for entry in self.entries:
            for j in range(7):
                entry[j].destroy()
        self.entries = []

    def update_rows(self):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        width = self.canvas.winfo_reqwidth()

        count = 0

        for e in self.entries:
            y = (count+1) * height
            
            e[0].place(x=0, y=y, width=2/14*width, height=height)
            e[1].place(x=2/14*width, y=y, width=5/14*width, height=height)
            e[2].place(x=7/14*width, y=y, width=2/14*width, height=height)
            e[3].place(x=9/14*width, y=y, width=1/14*width, height=height)
            e[4].place(x=10/14*width, y=y, width=1/14*width, height=height)
            e[5].place(x=11/14*width, y=y, width=1/14*width, height=height)
            e[6].place(x=12/14*width, y=y, width=1/14*width, height=height)

            count += 1

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

    def update_lists(self):
        # Reset
        self.type_options = []
        self.calculated_options = []
        self.detector_options = []
        self.index_options = []
        
        # Calculation options
        self.type_options.append('--Calculations--')
        self.type_options.append('Result')
        self.type_options.append('Count')
        self.type_options.append('Signal')

        # Parameters
        self.type_options.append('--Parameters--')
        if 'flags' in self.root.parameters.keys():
            for key in self.root.parameters['flags']:
                self.type_options.append(key)
        
        # Calculated results
        for key in self.root.calculations.keys():
            self.calculated_options.append(key)

        # Detectors and windows
        for win in self.root.Command.settingsframe.windows.entries:
            self.detector_options.append(win[5].get() + ':' + win[0].get())
        for win in self.root.Command.settingsframe.windows.entries_back:
            self.detector_options.append(win[0]['text'] + ':' + 'background')

        if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
            self.index_options.append('All')
            self.index_options.append('Laser')
            self.index_options.append('No laser')  
        elif self.root.histogram['scan_key'] == 'Delay (fs)_ctr':
            self.index_options.append('All')
            self.index_options.append('PumpProbe')
            self.index_options.append('Probe')
            self.index_options.append('Pump')
            self.index_options.append('None')
        else:
            self.index_options.append('All')
            self.index_options.append('i1')
            self.index_options.append('i2')
            self.index_options.append('i3')
            self.index_options.append('i4')
    
    def update_lists_in_row(self):
        self.update_lists()
        row = 0
        rows_to_del = []
        for entry in self.entries:
            # Check if the entries are still valid
            if entry[7].get() not in self.type_options or \
                not (entry[8].get() in self.calculated_options or entry[8].get() in self.detector_options or entry[8].get() == 'Not required') or \
                not (entry[9].get() in self.index_options or entry[9].get() == 'Not required'):
                
                rows_to_del.append(row)
            # Else update
            else:
                self.update_type_menu(entry[0], entry[7], self.type_options)

                if entry[8].get() in self.calculated_options:
                    self.update_menu(entry[1], entry[8], self.calculated_options)
                elif entry[8].get() in self.detector_options:
                    self.update_menu(entry[1], entry[8], self.detector_options)
                if entry[9].get() != 'Not required':
                    self.update_menu(entry[2], entry[9], self.index_options)

        # Delete rows from the rear
        for row in np.sort(rows_to_del)[::-1]:
            self.del_row(row)

    def type_opt_func(self, event):
        # Find out the row in question
        row = self.find_row(event)

        # Check content
        try:
            # Parameter
            if self.entries[row][7].get() in self.root.parameters['flags']:
                # Update lists
                # Detector
                self.update_menu(self.entries[row][1], self.entries[row][8], [])
                self.entries[row][8].set('Not required')
                # Index
                self.update_menu(self.entries[row][2], self.entries[row][9], self.index_options)
                self.entries[row][9].set(self.index_options[0])

                # Enable / Disable stuff
                self.entries[row][1]['state'] = 'disabled'
                self.entries[row][2]['state'] = 'enabled'
            # Result
            elif self.entries[row][7].get() in ['Result','Signal'] :
                # Update lists
                # Detector
                self.update_menu(self.entries[row][1], self.entries[row][8], self.calculated_options)
                self.entries[row][8].set(self.calculated_options[0])
                # Index
                self.update_menu(self.entries[row][2], self.entries[row][9], [])
                self.entries[row][9].set('Not required')

                # Enable / Disable stuff
                self.entries[row][1]['state'] = 'enabled'
                self.entries[row][2]['state'] = 'disabled'
            # Counts
            elif self.entries[row][7].get() == 'Count':
                # Update lists
                # Detector
                self.update_menu(self.entries[row][1], self.entries[row][8], self.detector_options)
                self.entries[row][8].set(self.detector_options[0])
                # Index
                self.update_menu(self.entries[row][2], self.entries[row][9], self.index_options)
                self.entries[row][9].set(self.index_options[0])

                # Enable / Disable stuff
                self.entries[row][1]['state'] = 'enabled'
                self.entries[row][2]['state'] = 'enabled'
            else:
                # Update lists
                self.entries[row][7].set('')
                # Detector
                self.update_menu(self.entries[row][1], self.entries[row][8], [])
                self.entries[row][8].set('')
                # Index
                self.update_menu(self.entries[row][2], self.entries[row][9], [])
                self.entries[row][9].set('')

                # Enable / Disable stuff
                self.entries[row][1]['state'] = 'disabled'
                self.entries[row][2]['state'] = 'disabled' 
        except:
            # Update lists
                self.entries[row][7].set('')
                # Detector
                self.update_menu(self.entries[row][1], self.entries[row][8], [])
                self.entries[row][8].set('')
                # Index
                self.update_menu(self.entries[row][2], self.entries[row][9], [])
                self.entries[row][9].set('')

                # Enable / Disable stuff
                self.entries[row][1]['state'] = 'disabled'
                self.entries[row][2]['state'] = 'disabled' 

    def update_menu(self, menu, var, options):
        menu['menu'].delete(0, "end")
        for string in options:
            menu['menu'].add_command(label=string, command=tk._setit(var, string))

    def update_type_menu(self, menu, var, options):
        menu['menu'].delete(0, "end")
        for string in options:
            menu['menu'].add_command(label=string, command=lambda x=string: self.new_type_opt_func(menu, var, x))
    
    def new_type_opt_func(self, menu, var, string):
        # Select
        var.set(string)
        self.type_opt_func(menu)

    def find_row(self, event):
        row = 0
        for entry in self.entries:
            if entry[0] == event:
                return row
            else:
                row += 1
        else:
            return row

    def valid_figure_input(self, val):
        if val == ''or \
            isint(val):
            return True
        elif len(val.split(':')) == 2:
            if isint(val.split(':')[0]) and (isint(val.split(':')[1]) or val.split(':')[1] == ''):
                return True
            else:
                return False
        else:
            return False

    def plot_results(self):
        tab_name = 'Results'
        
        if len(self.entries) == 0 or 'scan_key' not in self.root.histogram.keys():
            return

        # See if the window already exists
        for item in self.root.tab_bar.winfo_children():
            if tab_name == self.root.tab_bar.tab(item)['text']:
                self.root.tab_bar.select(item)
                
                # Plot stuff in the window
                self._plot_results(item)

                return
        
        # Create a new window
        self.root.create_new_tab(tab_name)

        # Plot stuff in the window
        for item in self.root.tab_bar.winfo_children():
            if tab_name == self.root.tab_bar.tab(item)['text']:
                self.root.tab_bar.select(item)
                
                self._plot_results(item)

                return

    def _plot_results(self,item):
        self.root.plotdict = dict()
        
        # Loop over entries to figure out ratio of plots.
        max = 0
        row = 0
        multiple = []
        single = []
        for entry in self.entries:
            # Sanity check
            if entry[7].get() != '':
                # No figure
                if entry[4].get() == '' or entry[11].get() != 1:
                    pass
                # Span a multiple
                elif ':' in entry[4].get():
                    # Check if figure text is applicable
                    if entry[4].get().split(':')[1] == '':
                        pass
                    else:
                        if row not in multiple:
                            multiple.append([row,int(entry[4].get().split(':')[0]),int(entry[4].get().split(':')[1])])
                        # Set new maximum
                        if int(entry[4].get().split(':')[1]) > max:
                            max = int(entry[4].get().split(':')[1])
                # Integer
                else:
                    single.append([row, int(entry[4].get())])
                    # Set new maximum
                    if int(entry[4].get()) > max:
                        max = int(entry[4].get())
            row += 1
        
        # Check that all multiples are ok
        for m in range(len(multiple)):
            for c in [y for i,y in enumerate(range(len(multiple))) if i!=m]:
                # Combine 
                if multiple[m][2] == multiple[c][1]:
                    multiple[m][2] == multiple[c][2]
                    multiple[c][1] == multiple[m][1]
                if multiple[m][1] == multiple[c][2]:
                    multiple[m][1] == multiple[c][1]
                    multiple[c][2] == multiple[m][2] 
                
                # Expand
                if multiple[m][1] >= multiple[c][1] and\
                    multiple[m][2] <= multiple[c][2]:
                    multiple[m][2] == multiple[c][2]
                    multiple[m][1] == multiple[c][1]
        
        # Check if singles should be moved to multiples
        remove = []
        for s in range(len(single)):
            for m in range(len(multiple)):
                if single[s][1] >= multiple[m][1] and single[s][1] <= multiple[m][2]:
                    multiple.append([single[s][0],multiple[m][1],multiple[m][2]])
                    remove.append(s)
        # Remove deprected
        for r in np.sort(remove)[::-1]:
            single.pop(r)
        
        # Ready to plot
        # Clear axes
        for i, ax in enumerate(item.figure.fig.axes):
            item.figure.fig.delaxes(ax)

        x, start_index = np.unique(np.sort(np.array(self.root.parameters[self.root.histogram['scan_key']])), return_index=True)
        index = np.argsort(self.root.parameters[self.root.histogram['scan_key']])
        edges = np.array(self.root.histogram['edges'])*1e-3

        self.root.plotdict['x'] = x

        # plot on the unique multiple axis
        if len(multiple) > 0:
            for mul in np.unique(np.array(multiple)[:,1:], axis=0):
                # Create axis
                ax = item.figure.fig.add_subplot(max, 1, (mul[0], mul[1]))
                ax.set_position([0.05,1-0.9*mul[1]/max,0.94,0.885*(mul[1]-mul[0]+1)/max])

                # Loop over all the rows to plot on this axis
                for m in multiple:
                    if m[1] == mul[0] and m[2] == mul[1]:
                        self.plot_on_axis(m, ax, x, edges, index, start_index)

        # plot on the unique single axis
        if len(single) > 0:
            for sin in np.unique(np.array(single)[:,1], axis=0):
                # Create axis
                ax = item.figure.fig.add_subplot(max, 1, sin)
                ax.set_position([0.05,1-0.9*sin/max,0.94,0.885/max])
                
                # Loop over all the rows to plot on this axis
                for s in single:
                    if s[1] == sin:
                        self.plot_on_axis(s, ax, x, edges, index, start_index)

        # Pretty plot
        item.figure.fig.axes[-1].set_xlabel(self.root.histogram['scan_key'])
        for i, ax in enumerate(item.figure.fig.axes):
            ax.legend(loc=1)
            
            if i != len(item.figure.fig.axes)-1:
                ax.sharex(item.figure.fig.axes[-1])
                ax.set_xticklabels([])
            
            ax.grid(visible=True, which='major', axis='both', color='gray', alpha=0.5, linestyle='-')
            ax.grid(visible=True, which='minor', axis='both', color='gray', alpha=0.3, linestyle='--')

        # Update settings
        item.plot_settings.xmin_entry.delete(0,'end')
        item.plot_settings.xmin_entry.insert(0,str(x[0]))
        item.plot_settings.xmax_entry.delete(0,'end')
        item.plot_settings.xmax_entry.insert(0,str(x[-1]))

        item.plot_settings.zero_line.select()

        item.figure.canvas.draw()

        # Write plotdict
        f = open(self.root.folder_path+'/'+self.root.run_choosen+'/PythonAnalysis/plotdict.txt', 'w')
        f.write(json.dumps(self.root.plotdict, cls=NumpyEncoder))
        f.close()

        # Write txt file
        f = open(self.root.folder_path+'/'+self.root.run_choosen+'/PythonAnalysis/plot.txt', 'w')
        
        f.write('x'.rstrip('\n'))
        for key in self.root.plotdict.keys():
            if key != 'x':
                f.write((','+key+','+key+': error').rstrip('\n'))
        f.write('\n')
        for line in range(len(self.root.plotdict['x'])):
            f.write(f'{self.root.plotdict["x"][line]}'.rstrip('\n'))
            for key in self.root.plotdict.keys():
                if key != 'x':
                    f.write(f',{self.root.plotdict[key][0][line]},{self.root.plotdict[key][1][line]}'.rstrip('\n'))
            f.write('\n')

        f.close()

    def plot_on_axis(self, m, ax, x, edges, index, start_index):

        # Results
        if self.entries[m[0]][7].get() in ['Result','Signal']:
            
            y, y_err = self.root.calculations[self.entries[m[0]][8].get()]
            
            if self.entries[m[0]][10].get():
                ax.errorbar(x, y, np.sqrt(y_err), label=self.entries[m[0]][8].get(), fmt='.-', capsize=1.5)
            else:
                ax.plot(x, y, '.-', label=self.entries[m[0]][8].get())
                
            self.root.plotdict[self.root.run_choosen+': '+self.entries[m[0]][7].get()+': '+self.entries[m[0]][8].get()] = [y, y_err]

        # Counts
        elif self.entries[m[0]][7].get() == 'Count':
            # Get windows 
            mask = np.ones(len(edges), dtype=bool)
            if self.entries[m[0]][8].get().split(':')[1] == 'background':
                for win in self.container.settingsframe.windows.entries_back:
                    if self.entries[m[0]][8].get().split(':')[0] == win[0]['text']:
                        mask = (edges[:-1] > float(win[1].get())) * (edges[:-1] < float(win[2].get()))
            else:
                for win in self.container.settingsframe.windows.entries:
                    if self.entries[m[0]][8].get().split(':')[1] == win[0].get():
                        mask = (edges[:-1] > float(win[2].get())) * (edges[:-1] < float(win[3].get()))
            
            if isinstance(x, (list, tuple, np.ndarray)):
                point_edges = x[:-1] + (x[1:] - x[:-1])/2
                point_edges = np.concatenate((np.concatenate(([point_edges[0]+(x[0]-x[1])],point_edges)), [point_edges[-1]+(x[-1]-x[-2])]))
            else:
                point_edges = x
            points = []
            
            if self.root.histogram['scan_key'] == 'Wavelength_ctr' or self.root.histogram['scan_key'] == 'Requested Transmission_ctr':
                for i in x:
                    if self.entries[m[0]][9].get() == 'All':
                        points.append(np.sum(np.array(self.root.histogram[self.entries[m[0]][8].get().split(':')[0]+f'_hist_{1}_'+str(i)])[mask])+
                                      np.sum(np.array(self.root.histogram[self.entries[m[0]][8].get().split(':')[0]+f'_hist_{0}_'+str(i)])[mask]))
                    else:
                        points.append(np.sum(np.array(self.root.histogram[self.entries[m[0]][8].get().split(':')[0]+f'_hist_{int(self.entries[m[0]][9].get() == "Laser")}_'+str(i)])[mask]))
            else:
                for i in x:
                    if self.entries[m[0]][9].get() == 'All':
                        points.append(np.sum(np.array(self.root.histogram[self.entries[m[0]][8].get().split(':')[0]+f'_hist_1_1_'+str(i)])[mask])+
                                      np.sum(np.array(self.root.histogram[self.entries[m[0]][8].get().split(':')[0]+f'_hist_0_0_'+str(i)])[mask])+
                                      np.sum(np.array(self.root.histogram[self.entries[m[0]][8].get().split(':')[0]+f'_hist_1_0_'+str(i)])[mask])+
                                      np.sum(np.array(self.root.histogram[self.entries[m[0]][8].get().split(':')[0]+f'_hist_0_1_'+str(i)])[mask]))
                    else:
                        points.append(np.sum(np.array(self.root.histogram[self.entries[m[0]][8].get().split(':')[0]+f'_hist_{int("Probe" in self.entries[m[0]][9].get())}_{int("Pump" in self.entries[m[0]][9].get())}_'+str(i)])[mask]))
            
            if isinstance(x, (list, tuple, np.ndarray)):
                ax.stairs(points, point_edges, label=self.entries[m[0]][8].get())
            else:
                ax.plot(point_edges, points, label=self.entries[m[0]][8].get())
            
            self.root.plotdict[self.root.run_choosen+': '+self.entries[m[0]][7].get()+': '+self.entries[m[0]][8].get()+ ': '+ self.entries[m[0]][9].get()] = [points, points]

        # Parameter
        else:
            param = np.array(self.root.parameters[self.entries[m[0]][7].get()])[index]
            
            if self.entries[m[0]][9].get() == 'All':
                for ind in self.index_options[1:]:
                    if len(self.index_options) == 5:
                        if ind == 'PumpProbe' or ind == 'i1':
                            laser_mask = np.array(self.root.parameters['ADC.Probe_on'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_on'], dtype=bool)
                        elif ind == 'None' or ind == 'i4':
                            laser_mask = np.array(self.root.parameters['ADC.Probe_off'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_off'], dtype=bool)
                        elif ind == 'Probe' or ind == 'i2':
                            laser_mask = np.array(self.root.parameters['ADC.Probe_on'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_off'], dtype=bool)
                        elif ind == 'Pump' or ind == 'i3':
                            laser_mask = np.array(self.root.parameters['ADC.Probe_off'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_on'], dtype=bool)
                        laser_mask = laser_mask[index]
                    else:
                        if ind == 'Laser':
                            laser_mask = np.array(self.root.parameters['ADC.Laser_on'], dtype=bool)
                        elif ind == 'No laser':
                            laser_mask = np.array(self.root.parameters['ADC.Laser_off'], dtype=bool)
                        

                    y = []
                    y_err = []
                    for i in range(len(start_index)):
                        if i == len(start_index)-1:
                            y.append(np.mean(param[start_index[i]:][laser_mask[start_index[i]:]]))
                            y_err.append(np.var(param[start_index[i]:][laser_mask[start_index[i]:]])/len(param[start_index[i]:][laser_mask[start_index[i]:]]))
                        else:
                            y.append(np.mean(param[start_index[i]:start_index[i+1]][laser_mask[start_index[i]:start_index[i+1]]]))
                            y_err.append(np.var(param[start_index[i]:start_index[i+1]][laser_mask[start_index[i]:start_index[i+1]]])/len(param[start_index[i]:start_index[i+1]][laser_mask[start_index[i]:start_index[i+1]]]))
                    
                    if self.entries[m[0]][10].get():
                        ax.errorbar(x, y, np.sqrt(y_err), label=self.entries[m[0]][7].get()+':'+ind, fmt='.', capsize=1.5)
                    else:
                        ax.plot(x, y, '.', label=self.entries[m[0]][7].get()+':'+ind)
                    
                    self.root.plotdict[self.root.run_choosen+': '+self.entries[m[0]][7].get()+ ': '+ ind] = [y, y_err]
            else:
                if len(self.index_options) == 5:
                    if self.entries[m[0]][9].get() == 'PumpProbe':
                        laser_mask = np.array(self.root.parameters['ADC.Probe_on'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_on'], dtype=bool)
                    elif self.entries[m[0]][9].get() == 'None':
                        laser_mask = np.array(self.root.parameters['ADC.Probe_off'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_off'], dtype=bool)
                    elif self.entries[m[0]][9].get() == 'Probe':
                        laser_mask = np.array(self.root.parameters['ADC.Probe_on'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_off'], dtype=bool)
                    elif self.entries[m[0]][9].get() == 'Pump':
                        laser_mask = np.array(self.root.parameters['ADC.Probe_off'], dtype=bool)*np.array(self.root.parameters['ADC.Pump_on'], dtype=bool)
                    laser_mask = laser_mask[index]
                else:
                    if self.entries[m[0]][9].get() == 'Laser':
                        laser_mask = np.array(self.root.parameters['ADC.Laser_on'], dtype=bool)
                    elif self.entries[m[0]][9].get() == 'No laser':
                        laser_mask = np.array(self.root.parameters['ADC.Laser_off'], dtype=bool)
                    
                y = []
                y_err = []
                for i in range(len(start_index)):
                    if i == len(start_index)-1:
                        y.append(np.mean(param[start_index[i]:][laser_mask[start_index[i]:]]))
                        y_err.append(np.var(param[start_index[i]:][laser_mask[start_index[i]:]])/(len(param[start_index[i]:][laser_mask[start_index[i]:]])))
                    else:
                        y.append(np.mean(param[start_index[i]:start_index[i+1]][laser_mask[start_index[i]:start_index[i+1]]]))
                        y_err.append(np.var(param[start_index[i]:start_index[i+1]][laser_mask[start_index[i]:start_index[i+1]]])/(len(param[start_index[i]:start_index[i+1]][laser_mask[start_index[i]:start_index[i+1]]])))
                    
                if self.entries[m[0]][10].get():
                    ax.errorbar(x, y, np.sqrt(y_err), label=self.entries[m[0]][7].get()+':'+self.entries[m[0]][9].get(), fmt='.', capsize=1.5)
                else:
                    ax.plot(x, y, '.', label=self.entries[m[0]][7].get()+':'+self.entries[m[0]][9].get())
                
                self.root.plotdict[self.root.run_choosen+': '+self.entries[m[0]][7].get()+ ': '+ self.entries[m[0]][9].get()] = [y, y_err]
        
        ax.axhline(0, color='k')
        ax.minorticks_on()
        ax.set_xlim(x[0],x[-1])

    def load_default(self):
        self.load_settings(default = True)
    
    def load_settings(self, default = False):
        # Reset
        self.del_all_rows()
        if self.resultsetting_var.get() == 'Default':
            default = True

        # Default settings from data
        if default:
            
            # Make result settings
            for key in self.root.calculations.keys():
                self.add_row()

                # Put in the settings
                self.entries[-1][7].set('Result')
                self.entries[-1][8].set(key)
                self.entries[-1][1]['state'] = 'enabled'
                self.entries[-1][9].set('Not required')
                self.entries[-1][10].set(1)
                self.entries[-1][4].delete(0,'end')
                self.entries[-1][4].insert(0,'1:3')
                self.entries[-1][11].set(1)

                self.update_lists_in_row()
            
            # Make background settings
            for win in self.container.settingsframe.windows.entries_back:
                self.add_row()

                # Put in the settings
                self.entries[-1][7].set('Count')
                self.entries[-1][8].set(win[0]['text'] + ':' + 'background')
                self.entries[-1][1]['state'] = 'enabled'
                self.entries[-1][9].set('All')
                self.entries[-1][2]['state'] = 'enabled'
                self.entries[-1][10].set(1)
                self.entries[-1][4].delete(0,'end')
                self.entries[-1][4].insert(0,'4')
                self.entries[-1][11].set(1)

                self.update_lists_in_row()
            
            # If Power measured make power measured
            if 'ADC.Laser_pw' in self.root.parameters.keys():
                self.add_row()

                # Put in the settings
                self.entries[-1][7].set('ADC.Laser_pw')
                self.entries[-1][8].set('Not required')
                self.entries[-1][9].set('All')
                self.entries[-1][2]['state'] = 'enabled'
                self.entries[-1][10].set(1)
                self.entries[-1][4].delete(0,'end')
                self.entries[-1][4].insert(0,'5')
                self.entries[-1][11].set(1)

                self.update_lists_in_row()

        # Load from file
        else:    
            type, det, index, error, figure, enable = np.loadtxt(os.getcwd()+'/settings_files/'+self.resultsetting_var.get()+'.txt', unpack=True, delimiter=',')

            # Check if compatible with current data
            self.update_lists()
            for t, d, i in zip(type, det, index):
                if t not in self.type_options or \
                    not (d in self.calculated_options or d in self.detector_options or d == 'Not required') or\
                    not (i in self.index_options or i == 'Not required'):
                    print(time.strftime('%H:%M:%S', time.gmtime())+' Couldn\'t load settings')
                    return

            # Loop thourgh settings
            for i in range(len(type)):
                self.add_row()
                
                # Put in the settings
                self.entries[-1][7].set(type[i])
                self.entries[-1][8].set(det[i])
                self.entries[-1][9].set(index[i])
                self.entries[-1][10].set(int(error[i]))
                self.entries[-1][4].delete(0,'end')
                self.entries[-1][4].insert(0,figure[i])
                self.entries[-1][11].set(int(enable[i]))

                self.update_lists_in_row(i)

    def load_settings_menu(self):
        options = []
        options.append('Default')
        for filename in os.listdir(os.getcwd()+'/settings_files'):
            options.append(filename[:-4])
        self.update_menu(self.resultsetting, self.resultsetting_var, options)
        self.resultsetting_var.set('Default')

    def save_settings(self):
        # Check if there are settings to save
        savable = 0
        for entry in self.entries:
            if entry[7].get() != '' and entry[8].get() != '' and entry[9].get() != '':
                savable += 1
        
        if savable > 0:
            self.name_of_file = ''
            self.cont = True

            toplevel = self.save_proceed(self)
            toplevel.wait_window(toplevel)
            
            if not self.cont:
                return
            
            f = open(os.getcwd()+'/settings_files/'+self.name_of_file+'.txt', "w")
            for entry in self.entries:
                if entry[7].get() != '' and entry[8].get() != '' and entry[9].get() != '':
                    f.write(f'{entry[7].get()},{entry[8].get()},{entry[9].get()},{entry[10].get()},{entry[11].get()}')
            f.close()

            self.load_settings_menu()

        else:
            print(time.strftime('%H:%M:%S', time.gmtime())+' No settings to save')

    class save_proceed(tk.Toplevel):
        def __init__(_self, self, *args, **kwargs):
            super().__init__(self, *args, **kwargs)
            _self.title("Save settings")

            # Create a label in the Toplevel window
            label = tk.Label(_self, text=f'Name of settings')
            label.pack(padx=10, pady=10)

            # Create "Continue" and "Cancel" buttons in the Toplevel window
            _self.entry = tk.Entry(_self)
            _self.entry.pack(padx=15, pady=5, fill='x')

            # Create "Continue" and "Cancel" buttons in the Toplevel window
            yes_button = tk.Button(_self, text="Save", command=lambda : _self.continue_action(self))
            cancel_button = tk.Button(_self, text="Cancel", command=lambda : _self.cancel_action(self))

            yes_button.pack(side = tk.LEFT, padx=5, pady=5)
            cancel_button.pack(side = tk.RIGHT, padx=5, pady=5)

        def continue_action(_self, self):
            self.name_of_file = _self.entry.get()
            _self.destroy()

        def cancel_action(_self, self):
            self.cont = False
            _self.destroy()
        