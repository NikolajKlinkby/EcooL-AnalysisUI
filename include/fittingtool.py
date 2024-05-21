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


class fittingtool(tk.Toplevel):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.title("Fitting Tool")
        self.geometry(f'{root.winfo_width()}x{root.winfo_height()}')

        self.root = root
        self.data = dict()
        self.memory = dict()
        self.x = []
        self.y = []
        self.y_err = []
        self.param_names = []
        self.fit_function_nr_params = []
        self.fit_function = {}
        self.fit = {}
        self.flip_ax = False
        self.filepath = ''

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

        # Plot settings
        self.plot_settings = tk.LabelFrame(self, text='Plot settings')
        self.plot_settings.grid()

        self.flip_axis_button = tk.Button(self.plot_settings, text = 'Flip X-axis', command=self.flip_axis)
        self.flip_axis_button.grid()

        # Fit tools
        self.control = tk.LabelFrame(self, text='Fitting tools')
        self.control.grid()

        self.explainer = tk.LabelFrame(self.control, text='')
        self.explainer.grid()

        self.explainer_text = tk.scrolledtext.ScrolledText(self.explainer)
        self.explainer_text.pack(expand=True, fill='both')
        self.explainer_text.insert(tk.END, f'Function must have name f, and form \n\ndef f(x,*params):\n\nJacobian and Hessian returning (len(params),n) and (len(params), len(params, n)) can be given with jac and hess functions.\n\n Lower and upper bounds are only used for global minimization with method \'diff_evol\'\n\n For method \'diff_evol\' errors are only reliable if jac and hess are given\n')
        self.explainer_text.configure(state='disabled')

        self.fit_text = scrolledtext.ScrolledText(self.control, wrap=tk.WORD)
        self.fit_text.grid()

        self.method = tk.StringVar()
        self.method.set('BFGS')
        self.method_dropdown = ttk.OptionMenu(self.control, self.method, self.method.get(), *['BFGS', 'diff_evol'], command=lambda e: self.method_change())
        self.method_dropdown.grid()

        # Data selection
        self.data_var = tk.StringVar()
        self.data_var.set('')

        self.data_optmen = ttk.OptionMenu(self.control, self.data_var, self.data_var.get(), *[])
        self.data_optmen.grid()

        self.updatebut = tk.Button(self.control, text='From current', command=self.update)
        self.updatebut.grid()

        self.loadbut = tk.Button(self.control, text='Load', command=self.load)
        self.loadbut.grid()

        # Buttons
        self.save_but = tk.Button(self.control, text='Save', command=self.save)
        self.save_but.grid()

        self.load_but = tk.Button(self.control, text='Load', command=self.load_preset)
        self.load_but.grid()

        self.fit_but = tk.Button(self.control, text='Fit', command=self.fit_button_func)
        self.fit_but.grid()

        # Preset selection
        self.preset_var = tk.StringVar()
        self.preset_var.set('')

        self.preset_optmen = ttk.OptionMenu(self.control, self.preset_var, self.preset_var.get(), *[])
        self.preset_optmen.grid()

        # Results grid
        self.results = tk.LabelFrame(self.control, text='Results')
        self.results.grid()

        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self.results)
        self.canvas.grid(row=1, column=0, sticky='nswe')

        # Create a vertical scrollbar
        self.scrollbar = ttk.Scrollbar(self.results, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=1, column=1, sticky='nse')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create a frame inside the canvas to hold the widgets
        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw", tags='inner_frame')
        self.inner_frame.grid_propagate(False)

        self.entries = []

        self.header = []

        # Function to update scroll region whenever widgets are added or removed
        self.inner_frame.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.update_canvas)

        self.bind('<Configure>', self.resize)
        self.protocol("WM_DELETE_WINDOW", lambda : self.destroy())

        self.update_plot()
        self.update_preset_dropdown()
        self.add_header()

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2/50

        # Major frames      
        self.plotframe.place(in_=self, relx=1/5+padx, rely=pady,
            relwidth=4/5 - 2 * padx, relheight=9/10 - 2 * pady)
        
        self.plot_settings.place(in_=self, relx=1/5+padx, rely=9/10+pady,
            relwidth=4/5 - 2* padx, relheight= 1/10 - 2* pady)
        
        self.control.place(in_=self, relx=padx, rely=pady,
            relwidth=1/5 - 2 * padx, relheight=1 - 2 * pady)
        
        # Minor frames
        self.explainer.place(in_=self.control, relx=padx, rely=pady,
            relwidth=1 - 2 * padx, relheight=1/3 - 4.5/45 - 2 * pady)
        
        self.fit_text.place(in_=self.control, relx=padx, rely=1/3+pady,
            relwidth=1 - 2 * padx, relheight=1/3 - 2 * pady)
        
        self.results.place(in_=self.control, relx=padx, rely=2/3+3/45+pady,
            relwidth=1 - 2 * padx, relheight=1/3-3/45 - 2 * pady)
        
        # Methods
        self.method_dropdown.place(in_=self.control, relx=padx, rely=1/3 - 4.5/45+pady,
            relwidth=1 - 2 * padx, relheight=1.5/45 - 2 * pady)
        
        # Data selection
        self.data_optmen.place(in_=self.control, relx=padx, rely=1/3-3/45+pady,
            relwidth=1 - padx, relheight=1.5/45 - pady)

        self.updatebut.place(in_=self.control, relx=padx, rely=1/3-1.5/45,
            relwidth=1/2 - padx, relheight=1.5/45 - pady)

        self.loadbut.place(in_=self.control, relx=1/2, rely=1/3-1.5/45,
            relwidth=1/2 - padx, relheight=1.5/45 - pady)
        
        # Buttons
        self.save_but.place(in_=self.control, relx=padx, rely=2/3+pady,
            relwidth=1/2 - padx, relheight=1.5/45 - pady)

        self.load_but.place(in_=self.control, relx=1/2, rely=2/3+pady,
            relwidth=1/2 - padx, relheight=1.5/45 - pady)

        self.fit_but.place(in_=self.control, relx=2/3, rely=2/3+1.5/45,
            relwidth=1/3 - padx, relheight=1.5/45 - pady)

        self.preset_optmen.place(in_=self.control, relx=padx, rely=2/3+1.5/45,
            relwidth=2/3 - padx, relheight=1.5/45 - pady)
        
        # Results
        self.scrollbar.place(in_=self.results, relx=1 - padx - scrollbarwidth, rely=pady,
            relwidth=scrollbarwidth, relheight=1 - pady)
        
        self.canvas.place(in_=self.results, relx=padx, rely=0,
            relwidth=1 - 2*padx - scrollbarwidth, relheight=1 - pady)
        
        self.update_header()
        
        self.update_rows()

    def update_canvas(self, event):
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.results.winfo_width())

    def update_scroll_region(self, event):
        self.update_canvas(event)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.results.winfo_width())

    def add_row(self, text):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = (len(self.entries)+1) * height

        width = self.canvas.winfo_reqwidth()
        
        label = tk.Label(self.inner_frame, text=text)
        label.place(x=0, y=y, width=2.25/10*width, height=height)
        
        entry1 = ttk.Entry(self.inner_frame)
        entry1.insert(0, '1')
        entry1.place(x=2.25/10*width, y=y, width=2.25/10*width, height=height)

        label1 = tk.Label(self.inner_frame, text='')
        label1.place(x=4.5, y=y, width=2.25/10*width, height=height)

        label2 = tk.Label(self.inner_frame, text='')
        label2.place(x=6.75, y=y, width=2.25/10*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        
        self.entries.append((label, entry1, label1, label2))

    def add_diff_evol_row(self, text):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = (len(self.entries)+1) * height

        width = self.canvas.winfo_reqwidth()
        
        label = tk.Label(self.inner_frame, text=text)
        label.place(x=0, y=y, width=1.8/10*width, height=height)
        
        entry1 = ttk.Entry(self.inner_frame)
        entry1.insert(0, '0')
        entry1.place(x=1.8/10*width, y=y, width=1.8/10*width, height=height)

        entry2 = ttk.Entry(self.inner_frame)
        entry2.insert(0, '1')
        entry2.place(x=3.6/10*width, y=y, width=1.8/10*width, height=height)

        label1 = tk.Label(self.inner_frame, text='')
        label1.place(x=5.4, y=y, width=1.8/10*width, height=height)

        label2 = tk.Label(self.inner_frame, text='')
        label2.place(x=7.2, y=y, width=1.8/10*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        
        self.entries.append((label, entry1, entry2, label1, label2))

    def update_rows(self):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        width = self.canvas.winfo_reqwidth()

        count = 0

        if self.method.get() != 'diff_evol':
            for e in self.entries:
                y = (count+1) * height
                
                e[0].place(x=0, y=y, width=2.25/10*width, height=height)
                e[1].place(x=2.25/10*width, y=y, width=2.25/10*width, height=height)
                e[2].place(x=4.5/10*width, y=y, width=2.25/10*width, height=height)
                e[3].place(x=6.75/10*width, y=y, width=2.25/10*width, height=height)

                count += 1

        else:
            for e in self.entries:
                y = (count+1) * height
                
                e[0].place(x=0, y=y, width=1.8/10*width, height=height)
                e[1].place(x=1.8/10*width, y=y, width=1.8/10*width, height=height)
                e[2].place(x=3.6/10*width, y=y, width=1.8/10*width, height=height)
                e[3].place(x=5.4/10*width, y=y, width=1.8/10*width, height=height)
                e[4].place(x=7.2/10*width, y=y, width=1.8/10*width, height=height)

                count += 1

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

    def update_header(self):
        self.canvas.update()

        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = 0

        width = self.canvas.winfo_reqwidth()

        if len(self.header) == 4:
            # Resize table header
            
            self.header[0].place(in_=self.inner_frame, x=0, y=y, width=2.25/10*width, height=height)

            self.header[1].place(in_=self.inner_frame, x=2.25/10*width, y=y, width=2.25/10*width, height=height)

            self.header[2].place(in_=self.inner_frame, x=4.5/10*width, y=y, width=2.25/10*width, height=height)

            self.header[3].place(in_=self.inner_frame, x=6.75/10*width, y=y, width=2.25/10*width, height=height)

            self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
            self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        elif len(self.header) == 5:
            # Resize table header
            
            self.header[0].place(in_=self.inner_frame, x=0, y=y, width=1.8/10*width, height=height)

            self.header[1].place(in_=self.inner_frame, x=1.8/10*width, y=y, width=1.8/10*width, height=height)

            self.header[2].place(in_=self.inner_frame, x=3.6/10*width, y=y, width=1.8/10*width, height=height)

            self.header[3].place(in_=self.inner_frame, x=5.4/10*width, y=y, width=1.8/10*width, height=height)

            self.header[4].place(in_=self.inner_frame, x=7.2/10*width, y=y, width=1.8/10*width, height=height)

            self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
            self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

    def add_header(self):
        
        # Add table header
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = 0

        width = self.canvas.winfo_reqwidth()
        
        if self.method.get() == 'diff_evol':
            
            param_label = ttk.Label(self.inner_frame, text=f'Param', borderwidth=1, relief='solid')
            param_label.place(x=0, y=y, width=1.8/10*width, height=height)

            lower_label = ttk.Label(self.inner_frame, text=f'Lower', borderwidth=1, relief='solid')
            lower_label.place(x=1.8, y=y, width=1.8/10*width, height=height)

            upper_label = ttk.Label(self.inner_frame, text=f'Upper', borderwidth=1, relief='solid')
            upper_label.place(x=3.6, y=y, width=1.8/10*width, height=height)

            value_label = ttk.Label(self.inner_frame, text=f'Value', borderwidth=1, relief='solid')
            value_label.place(x=5.4/10*width, y=y, width=1.8/10*width, height=height)

            error_label = ttk.Label(self.inner_frame, text=f'Error', borderwidth=1, relief='solid')
            error_label.place(x=7.2/10*width, y=y, width=1.8/10*width, height=height)

            self.header = [param_label, lower_label, upper_label, value_label, error_label]

        else:
            
            param_label = ttk.Label(self.inner_frame, text=f'Param', borderwidth=1, relief='solid')
            param_label.place(x=0, y=y, width=2.25/10*width, height=height)

            init_label = ttk.Label(self.inner_frame, text=f'Init', borderwidth=1, relief='solid')
            init_label.place(x=2.25, y=y, width=2.25/10*width, height=height)

            value_label = ttk.Label(self.inner_frame, text=f'Value', borderwidth=1, relief='solid')
            value_label.place(x=4.5/10*width, y=y, width=2.25/10*width, height=height)

            error_label = ttk.Label(self.inner_frame, text=f'Error', borderwidth=1, relief='solid')
            error_label.place(x=6.75/10*width, y=y, width=2.25/10*width, height=height)

            self.header = [param_label, init_label, value_label, error_label]

    def del_header(self):
        for i in self.header:
            i.destroy()
        self.header = []

    def data_choosen(self, var, string):
        var.set(string)

        self.fit = {}
        self.y, self.y_err = self.memory[var.get()]
        self.y_err = np.array(self.y_err) / max(self.y)**2
        self.y = np.array(self.y) / max(self.y)

        self.update_plot()

    def update_plot(self):
        for i, ax in enumerate(self.fig.axes):
            self.fig.delaxes(ax)
        ax1 = self.fig.add_subplot(3, 1, (1,2))
        ax2 = self.fig.add_subplot(3, 1, (3,3))

        ax1.axhline(0, color='k')
        ax2.axhline(0, color='k')
        ax2.axhline(1, color='gray', alpha=0.5)
        ax2.axhline(-1, color='gray', alpha=0.5)
        
        # Plot data
        ax1.errorbar(self.x, self.y, np.sqrt(self.y_err), label=self.data_var.get(), capsize=3)
        
        # Plot fit
        if isinstance(self.fit, FittingRoutine):
            
            # Fit
            ax1.plot(self.x,self.fit_function['f'](np.array(self.x),*self.fit.params), label='Fit')

            # Initial guess
            if self.method.get() != 'diff_evol':
                # Read of initial values
                param_init = []
                for entry in self.entries:
                    param_init.append(float(entry[1].get()))

                ax1.plot(self.x,self.fit_function['f'](np.array(self.x),*param_init), label='Init')

            # Residuals
            mask = (np.array(self.y_err) > 0)
            ax2.plot(np.array(self.x)[mask],self.fit.NormRes, 'o')

            # Statistics
            handles, labels = ax1.get_legend_handles_labels()
            patch = mpatches.Patch(linewidth=0,fill=False,label=f'P-val: {self.fit.Pval:.2e}')
            handles.append(patch)
            patch = mpatches.Patch(linewidth=0,fill=False,label=f'Chi2: {self.fit.Chi2:.2e}')
            handles.append(patch) 
            ax1.legend(handles=handles,loc = 1)

        ax1.sharex(ax2)
        ax1.minorticks_on()
        ax1.grid(visible=True, which='major', axis='both', color='gray', alpha=0.5, linestyle='-')
        ax1.grid(visible=True, which='minor', axis='both', color='gray', alpha=0.3, linestyle='--')
        ax1.set_position([0.05,1-0.9*2/3,0.94,0.885*2/3])

        ax2.minorticks_on()
        ax2.grid(visible=True, which='major', axis='both', color='gray', alpha=0.5, linestyle='-')
        ax2.grid(visible=True, which='minor', axis='both', color='gray', alpha=0.3, linestyle='--')
        ax2.set_position([0.05,1-0.9,0.94,0.885*1/3])

        self.canvas_fig.draw()

    def del_all_rows(self):
        # Delete row visually
        for entry in self.entries:
            for widget in entry:
                widget.destroy()
        self.entries = []

    def find_row(self, event):
        row = 0
        for entry in self.entries:
            if entry[0] == event:
                return row
            else:
                row += 1
        else:
            return row

    def load(self):
        # Reset
        self.memory = dict()
        
        file_path = tk.filedialog.askdirectory(initialdir = self.root.folder_path)
        self.filepath = file_path
        if 'Run-' in self.filepath.split('/')[-1]:
            if os.path.exists(self.filepath+'/PythonAnalysis/plotdict.txt'):
                f = open(os_format_string(self.filepath+'/PythonAnalysis/plotdict.txt'), 'r')
                calculations = json.loads(f.read())
                f.close()

                self.memory = calculations
                self.x = self.memory.pop('x')
        
        self.update_dropdown()

    def update_dropdown(self):
        self.data_optmen['menu'].delete(0, "end")
        for string in self.memory.keys():
            self.data_optmen['menu'].add_command(label=string, command=lambda x=string: self.data_choosen(self.data_var, x))
            self.data_var.set('')
        if len(self.memory.keys()) < 1:
            self.data_var.set('')

    def update(self):
        # Reset
        self.memory = dict()

        if len(self.root.Command.results.entries) > 0:
            self.root.Command.results.plot_results()
            self.memory = self.root.plotdict

            self.x = self.memory.pop('x')

        self.filepath=self.root.folder_path + '/'+self.root.run_choosen

        # Update dropdown
        self.update_dropdown()

    def save(self):
        # Check if there are settings to save
        if len(self.fit_text.get("1.0", tk.END)) > 0:
            
            self.name_of_file = ''
            self.cont = True

            toplevel = self.save_proceed(self)
            toplevel.wait_window(toplevel)
            
            if not self.cont:
                return
            
            f = open(os_format_string(os.getcwd()+'/fitting_presets/'+self.name_of_file+'.txt'), "w")
            f.write(self.fit_text.get())
            f.close()

            self.update_preset_dropdown()

        else:
            print('No settings to save')

    def fit_button_func(self):
        try:
            # Covariance matrix
            mask = (np.array(self.y_err) > 0)

            cov_y = np.diag(np.array(self.y_err)[mask])

            if self.method.get() == 'diff_evol':
                # Read of upper and lower limits
                param_lower = []
                param_upper = []
                for entry in self.entries:
                    param_lower.append(entry[1].get())
                    param_upper.append(entry[2].get())

                # Call fit
                p0 = np.array([[float(i), float(j)] for i, j in zip(param_lower, param_upper)])
                self.fit = FittingRoutine(self.fit_function['f'], np.array(self.x)[mask],
                                                np.array(self.y)[mask], covy=cov_y, P0=p0,
                                                method=self.method.get(),
                                                jac=self.fit_function['jac'],
                                                hess=self.fit_function['hess'])
            else:
                # Read of initial values
                param_init = []
                for entry in self.entries:
                    param_init.append(entry[1].get())

                # Call fit
                p0 = np.array([float(i) for i in param_init])
                self.fit = FittingRoutine(self.fit_function['f'], np.array(self.x)[mask],
                                                np.array(self.y)[mask], covy=cov_y, P0=p0,
                                                method=self.method.get(),
                                                jac=self.fit_function['jac'],
                                                hess=self.fit_function['hess'])

            # Parameters table
            self.update_params_table()
            self.update_plot()
            self.save_fit()

        except Exception as e:
            print(traceback.format_exc())

    def save_fit(self):
        
        # Write txt file
        f = open(os_format_string(self.filepath+'/PythonAnalysis/fit_params.txt'), 'w')
        
        string = ''
        for entry in self.header:
            string += entry['text']+','
        f.write(string[:-1]+'\n')

        for entry in self.entries:
            string = ''
            for widget in entry:
                try:
                    string += widget['text']+','
                except:
                    string += widget.get()+','
            f.write(string[:-1]+'\n')

        f.close()

        f = open(os_format_string(self.filepath+'/PythonAnalysis/fit_val.txt'), 'w')
        
        f.write('x,y,y_var,normres')
        for i in range(len(self.fit.x)):
            f.write(f'{self.fit.x[i]},{self.fit.y[i]},{self.fit.cov_y[i,i]},{self.fit.NormRes[i]}\n')

        f.close()

        f = open(os_format_string(self.filepath+'/PythonAnalysis/fit_info.txt'), 'w')
        
        f.write(f'Chi2: {self.fit.Chi2}, Pval: {self.fit.Pval}, df: {self.fit.df},\n')
        f.write(f'Function:\n')
        f.write(self.fit_text.get("1.0", tk.END))

        f.close()

    def load_preset(self):
        self.fit_text.delete("1.0", 'end')
        self.fit = {}

        if os.path.exists(os.getcwd()+'/fitting_presets/'+self.preset_var.get()):
            f = open(os_format_string(os.getcwd()+'/fitting_presets/'+self.preset_var.get()), 'r')
            self.fit_text.insert('end', f'{f.read()}')
            f.close()

            self.update_fit_params()

    def update_fit_params(self):
        exec(self.fit_text.get("1.0", tk.END), self.fit_function)

        if 'f' in self.fit_function.keys():
            self.param_names = getfullargspec(self.fit_function['f'])[0][1:]
            self.fit_function_nr_params = len(self.param_names)

        self.del_header()
        self.del_all_rows()

        self.add_header()

        if self.method.get() == 'diff_evol':
            for i in self.param_names:
                self.add_diff_evol_row(i)

        else:
            for i in self.param_names:
                self.add_row(i)

    def update_params_table(self):
        if isinstance(self.fit, FittingRoutine):
            if len(self.entries) == len(self.fit.params):
                for e in range(len(self.entries)):
                    self.entries[e][-2].config(text='%1.3e' % self.fit.params[e])
                    self.entries[e][-1].config(text='%1.3e' % self.fit.Error[e])

    def update_preset_dropdown(self):
        self.preset_optmen['menu'].delete(0, 'end')
        if os.path.exists(os.getcwd()+'/fitting_presets'):
            for file in os.listdir(os.getcwd()+'/fitting_presets'):
                self.preset_optmen['menu'].add_command(label=file[:-4], command=tk._setit(self.preset_var, file))
                self.preset_var.set(file)

    def method_change(self):
        self.unbind('<Configure>')

        self.del_all_rows()
        self.del_header
        self.fit = {}

        self.add_header()

        self.update_fit_params()

        self.bind('<Configure>', self.resize)

    def flip_axis(self):
        self.x = -1*np.array(self.x)
        self.update_plot()

class save_proceed(tk.Toplevel):
    def __init__(_self, self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        _self.title("Save preset")

        # Create a label in the Toplevel window
        label = tk.Label(_self, text=f'Name of preset')
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
        