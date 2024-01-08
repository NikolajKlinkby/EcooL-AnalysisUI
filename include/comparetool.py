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


class comparetool(tk.Toplevel):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.title("Compare Tool")
        self.geometry(f'{root.tab_bar.winfo_width()}x{root.tab_bar.winfo_height()}')

        self.root = root
        self.data = dict()
        self.memory = dict()
        self.x = []

        # Plot
        self.plotframe = tk.LabelFrame(self)
        self.plotframe.grid()

        # Figure
        self.fig = plt.figure()
    
        # creating the Tkinter canvas
        self.canvas_fig = FigureCanvasTkAgg(self.fig, master = self.plotframe)  
        self.canvas_fig.draw()
        self.canvas_fig.get_tk_widget().pack(expand=True, fill='both')
    
        # creating the Matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas_fig, self.plotframe)
        self.toolbar.update()
    
        # placing the toolbar on the Tkinter window
        self.canvas_fig.get_tk_widget().pack(expand=True, fill='both')

        # Controls
        self.control = tk.LabelFrame(self, text='Controls')
        self.control.grid()

        self.dataselection = tk.LabelFrame(self.control, text='Data selection')
        self.dataselection.grid()

        self.plotsettings = tk.LabelFrame(self.control, text='Plot settings')
        self.plotsettings.grid()

        self.storeddata = tk.LabelFrame(self.control, text='Stored data')
        self.storeddata.grid()

        # Data selection
        self.data_var = tk.StringVar()
        self.data_var.set('')

        self.data_optmen = ttk.OptionMenu(self.dataselection, self.data_var, self.data_var.get(), *[])
        self.data_optmen.grid()

        self.updatebut = tk.Button(self.dataselection, text='Update', command=self.update)
        self.updatebut.grid()

        self.loadbut = tk.Button(self.dataselection, text='Load', command=self.load)
        self.loadbut.grid()

        self.addselectedbut = tk.Button(self.dataselection, text = 'Add', command=self.add_to_stored)
        self.addselectedbut.grid()

        # Stored data
        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self.storeddata)
        self.canvas.grid(row=1, column=0, sticky='nswe')

        # Create a vertical scrollbar
        self.scrollbar = ttk.Scrollbar(self.storeddata, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=1, column=1, sticky='nse')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas to hold the widgets
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw", tags='inner_frame')
        self.inner_frame.grid_propagate(False)

        self.entries = []

        # Add table header
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = 0

        width = self.canvas.winfo_reqwidth()
        
        self.data_label = ttk.Label(self.inner_frame, text=f'Data', borderwidth=1, relief='solid')
        self.data_label.place(x=0, y=y, width=4/10*width, height=height)

        self.norm_label = ttk.Label(self.inner_frame, text=f'Normalize', borderwidth=1, relief='solid')
        self.norm_label.place(x=4/10*width, y=y, width=1.5/10*width, height=height)

        self.scale_label = ttk.Label(self.inner_frame, text=f'Scale', borderwidth=1, relief='solid')
        self.scale_label.place(x=5.5/10*width, y=y, width=2/10*width, height=height)

        self.enable_label = ttk.Label(self.inner_frame, text=f'Enable', borderwidth=1, relief='solid')
        self.enable_label.place(x=7.5/10*width, y=y, width=1/10*width, height=height)

        self.delete_label = ttk.Label(self.inner_frame, text=f'Delete', borderwidth=1, relief='solid')
        self.delete_label.place(x=8.5/10*width, y=y, width=1/10*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        self.clearbutton = tk.Button(self.storeddata, text='Clear data', command=self.clear)
        self.clearbutton.grid()

        # Function to update scroll region whenever widgets are added or removed
        self.inner_frame.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.update_canvas)

        self.bind('<Configure>', self.resize)
        self.protocol("WM_DELETE_WINDOW", lambda : self.destroy())

        self.update_plot()

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2/50

        # Major frames      
        self.plotframe.place(in_=self, relx=padx, rely=pady,
            relwidth=1 - 2 * padx, relheight=2/3 - 2 * pady)
        
        self.control.place(in_=self, relx=padx, rely=2/3 + pady,
            relwidth=1 - 2 * padx, relheight=1/3 - 2 * pady)
        
        # Minor frames
        self.dataselection.place(in_=self.control, relx=padx, rely=pady,
            relwidth=1/4 - 2 * padx, relheight=1/3 - 2 * pady)
        
        self.plotsettings.place(in_=self.control, relx=padx, rely=1/3+pady,
            relwidth=1/4 - 2 * padx, relheight=2/3 - 2 * pady)
        
        self.storeddata.place(in_=self.control, relx=1/4+padx, rely=pady,
            relwidth=3/4 - 2 * padx, relheight=1 - 2 * pady)
        
        # Data selection
        self.data_optmen.place(in_=self.dataselection, relx=padx, rely=pady,
            relwidth=1 - 2 * padx, relheight=1/2 - 2 * pady)
        
        self.updatebut.place(in_=self.dataselection, relx=padx, rely=1/2+pady,
            relwidth=1/3 - 2 * padx, relheight=1/2 - 2 * pady)
        
        self.loadbut.place(in_=self.dataselection, relx=1/3+padx, rely=1/2+pady,
            relwidth=1/3 - 2 * padx, relheight=1/2 - 2 * pady)
        
        self.addselectedbut.place(in_=self.dataselection, relx=2/3+padx, rely=1/2+pady,
            relwidth=1/3 - 2 * padx, relheight=1/2 - 2 * pady)
        
        # Stored data
        self.scrollbar.place(in_=self.storeddata, relx=1 - padx - scrollbarwidth, rely=pady,
            relwidth=scrollbarwidth, relheight=9/10 - pady)
        
        self.canvas.place(in_=self.storeddata, relx=padx, rely=0,
            relwidth=1 - 2*padx - scrollbarwidth, relheight=9/10 - pady)
        
        self.canvas.update()
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = 0

        width = self.canvas.winfo_reqwidth()
        
        self.data_label.place(in_=self.inner_frame, x=0, y=y, width=4/10*width, height=height)

        self.norm_label.place(in_=self.inner_frame, x=4/10*width, y=y, width=1.5/10*width, height=height)

        self.scale_label.place(in_=self.inner_frame, x=5.5/10*width, y=y, width=2/10*width, height=height)

        self.enable_label.place(in_=self.inner_frame, x=7.5/10*width, y=y, width=1/10*width, height=height)

        self.delete_label.place(in_=self.inner_frame, x=8.5/10*width, y=y, width=1/10*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        self.clearbutton.place(in_=self.storeddata, relx=padx, rely=9/10+pady,
                               relwidth=1/10, relheight=1/10 - 2*pady)
        
        self.update_rows()

    def update_canvas(self, event):
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.storeddata.winfo_width())

    def update_scroll_region(self, event):
        self.update_canvas(event)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.storeddata.winfo_width())

    def add_row(self, text):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = (len(self.entries)+1) * height

        width = self.canvas.winfo_reqwidth()
        
        label = tk.Label(self.inner_frame, text=text)
        label.place(x=0, y=y, width=4/10*width, height=height)
        
        variable1 = tk.IntVar()
        variable1.set(0)
        checkbox1 = tk.Checkbutton(self.inner_frame, variable=variable1, command=self.update_plot)
        checkbox1.place(x=4/10*width, y=y, width=1.5/10*width, height=height)
        
        entry1 = ttk.Entry(self.inner_frame)
        entry1.insert(0, '1')
        entry1.place(x=5.5/10*width, y=y, width=2/10*width, height=height)
        
        variable2 = tk.IntVar()
        variable2.set(1)
        checkbox2 = tk.Checkbutton(self.inner_frame, variable=variable2, command=self.update_plot)
        checkbox2.place(x=7.5/10*width, y=y, width=1/10*width, height=height)
        
        checkbox = ttk.Checkbutton(self.inner_frame, command=lambda : self.del_but(label))
        checkbox.place(x=8.5/10*width, y=y, width=1/10*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        
        self.entries.append((label, checkbox1, entry1, checkbox2, checkbox, variable1, variable2))

    def update_rows(self):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        width = self.canvas.winfo_reqwidth()

        count = 0

        for e in self.entries:
            y = (count+1) * height
            
            e[0].place(x=0, y=y, width=4/10*width, height=height)
            e[1].place(x=4/10*width, y=y, width=1.5/10*width, height=height)
            e[2].place(x=5.5/10*width, y=y, width=2/10*width, height=height)
            e[3].place(x=7.5/10*width, y=y, width=1/10*width, height=height)
            e[4].place(x=8.5/10*width, y=y, width=1/10*width, height=height)

            count += 1

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

    def update_plot(self):
        for i, ax in enumerate(self.fig.axes):
            self.fig.delaxes(ax)
        ax = self.fig.add_subplot(111)
        
        for entry in self.entries:
            if entry[6].get():
                x, y, y_err = self.data[entry[0]['text']]
                
                # Normalize
                if entry[5].get():
                    y_err = np.array(y_err)/np.max(y)**2
                    y = np.array(y)/np.max(y)

                # Scale
                y = np.array(y)*float(entry[2].get())
                y_err = np.array(y_err)*float(entry[2].get())**2

                ax.errorbar(x, y, np.sqrt(y_err), label=entry[0]['text'], capsize=3)
            
        if isinstance(ax.get_legend_handles_labels()[1], list):
            if len(ax.get_legend_handles_labels()[1]) > 0:
                ax.legend(loc=1)
        ax.minorticks_on()
        ax.grid(visible=True, which='major', axis='both', color='gray', alpha=0.5, linestyle='-')
        ax.grid(visible=True, which='minor', axis='both', color='gray', alpha=0.3, linestyle='--')
        ax.set_position([0.05,0.1,0.94,0.89])

        self.canvas_fig.draw()

    def del_but(self,event):
        # Delete row
        row = self.find_row(event)
        self.del_row(row)
        
        # Move rows up
        self.update_rows()
        self.update_plot()

    def del_row(self, row):
        # Delete from data
        self.data.pop(self.entries[row][0]['text'])
        # Delete row visually
        for j in range(5):
            self.entries[row][j].destroy()

        # Make new entry list
        new_list = []
        for r in range(len(self.entries)):
            if r != row:
                new_list.append(self.entries[r])
        self.entries = new_list

    def find_row(self, event):
        row = 0
        for entry in self.entries:
            if entry[0] == event:
                return row
            else:
                row += 1
        else:
            return row

    def clear(self):
        for entry in self.entries:
            for i in range(5):
                entry[i].destroy()
        self.entries = []
        self.data = dict()
        self.update_plot()

    def add_to_stored(self):
        added = False
        count = 0

        while not added:
            if count == 0:
                added = self.add_to_stored_nested(self.data_var.get(), self.data_var.get())
            else:
                added = self.add_to_stored_nested(self.data_var.get()+f'-copy-{count}', self.data_var.get())
            count += 1
            
        self.update_plot()
    
    def add_to_stored_nested(self, var, orig):
        if var != '':
            if var not in self.data.keys():
                self.add_row(var)
                self.data[var] = np.concatenate(([self.x],self.memory[orig]))
                return True
            else:
                return False
        else:
            return False

    def load(self):
        # Reset
        self.memory = dict()
        
        filepath = tk.filedialog.askdirectory(initialdir = self.root.folder_path)
        if 'Run-' in filepath.split('/')[-1]:
            if os.path.exists(filepath+'/PythonAnalysis/plotdict.txt'):
                f = open(filepath+'/PythonAnalysis/plotdict.txt', 'r')
                calculations = json.loads(f.read())
                f.close()

                self.memory = calculations
                self.x = self.memory.pop('x')
        
        self.update_dropdown()

    def update_dropdown(self):
        self.data_optmen['menu'].delete(0, "end")
        for string in self.memory.keys():
            self.data_optmen['menu'].add_command(label=string, command=tk._setit(self.data_var, string))
            self.data_var.set(string)

    def update(self):
        # Reset
        self.memory = dict()

        if len(self.root.Command.results.entries) > 0:
            self.root.Command.results.plot_results()
            self.memory = self.root.plotdict

            self.x = self.memory.pop('x')

        # Update dropdown
        self.update_dropdown()

