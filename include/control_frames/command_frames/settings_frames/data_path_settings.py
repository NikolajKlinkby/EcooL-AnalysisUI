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
import time
import traceback
from inspect import signature
from inspect import getfullargspec
from include.FittingRoutine import FittingRoutine

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

from include.load import *
from include.control_frames.plot_frame import *
from include.control_frames.plot_frames.figure import *

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

class data_path_settings(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.root = root
        self.container = container
        self.run_selected = ''
        
        options = {'padx': 5, 'pady': 5}

        # Path location
        self.pathlocation = ttk.Label(self, text = self.root.folder_path, background='white')
        self.pathlocation.grid(pady=5, sticky=tk.W+tk.E, row = 0, column = 0, columnspan = 10)
        
        photo_loc = root.current_dir + r"/pics/UpdateArrow.png"
        photo_loc.encode('unicode_escape')
        
        # Reload button
        # Creating a photoimage object to use image
        self.photo = tk.PhotoImage(file = photo_loc)
        self.reloadbutton = tk.Button(self, text='Re',image = self.photo, command = self.updatefolder)
        self.reloadbutton.grid(pady=5, sticky=tk.E, row = 0, column = 10, columnspan=2)
        
        # Run viewer and chooser
        self.runlist = tk.Listbox(self, selectmode=tk.SINGLE, exportselection=0)
        self.runlist.grid(padx=(5,0), row=1, rowspan=4, column=6, columnspan=6, sticky=tk.W)

        self.scrollbar = tk.Scrollbar(self, command=self.runlist.yview)
        self.scrollbar.grid(row=1, rowspan=4, column=12, sticky=tk.E+tk.N+tk.S)
        self.runlist.config(yscrollcommand=self.scrollbar.set)
        
        # Bind clicks
        self.runlist.bind('<<ListboxSelect>>', self.on_select)
        self.runlist.bind('<Double-Button-1>', self.on_double_click)
        
        # Info
        self.infobox = tk.LabelFrame(self, text='Info')
        self.infobox.grid(row=4, column=0, columnspan=6, sticky=tk.E+tk.W)
        self.histlabel = tk.Label(self.infobox, text = 'Hist: NA')
        self.calclabel = tk.Label(self.infobox, text = 'Calc: NA')
        self.histlabel.grid(row=0, column=0, sticky=tk.W+tk.E)
        self.calclabel.grid(row=0, column=1, sticky=tk.W+tk.E)
        
        # Browse button
        self.browsebut = tk.Button(self, text='Browse', command = self.browse)
        self.browsebut.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E)
        
        # Load button
        self.loadbut = tk.Button(self, text='Load', command = self.load)
        self.loadbut.grid(row=1, column=2, columnspan=2, sticky=tk.W+tk.E)

        # Update current button
        self.updatebut = tk.Button(self, text='Update current', command = self.update)
        self.updatebut.grid(row=2, column=0, columnspan=2, sticky=tk.W)

        # Force button
        self.forcebut = tk.Button(self, text='Force', command = self.force)
        self.forcebut.grid(row=2, column=2, columnspan=2, sticky=tk.E)

        # Grid weight

        self.grid_columnconfigure(0, weight = 1)
        self.grid_columnconfigure(1, weight = 1)
        self.grid_rowconfigure(0, weight = 2)
        self.grid_rowconfigure(1, weight = 3)


        self.bind('<Configure>', self.resize)

        if os.path.exists(self.root.folder_path):
            self.updatefolder()
            self.root.run_choosen = ''

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2 / 50

        # place the window, giving it an explicit size
        self.pathlocation.place(in_=self, relx=0, rely=pady, 
            relwidth=1 - (1/5 - 2 * pady), relheight=1/5- 2 * pady)
        
        self.reloadbutton.place(in_=self, relx=5/6, rely=pady,
            relwidth=1/5 - 2 * pady, relheight=1/5 - 2 * pady)
        
        self.runlist.place(in_=self, relx=1/2 + padx, rely=1/5,
            relwidth=1/2 - 2 * padx - scrollbarwidth, relheight=4/5)
        
        self.scrollbar.place(in_=self, relx=1 - padx - scrollbarwidth, rely=1/5,
            relwidth=scrollbarwidth, relheight=4/5)
        
        self.infobox.place(in_=self, relx=0, rely=3/5, 
            relwidth=1/2, relheight=2/5)
        
        self.browsebut.place(in_=self, relx=0, rely=1/5,
            relwidth=1/4, relheight=1/5)
        
        self.forcebut.place(in_=self, relx=2/6, rely=2/5,
            relwidth=1/6, relheight=1/5)
        
        self.loadbut.place(in_=self, relx=1/4, rely=1/5,
            relwidth=1/4, relheight=1/5)
        
        self.updatebut.place(in_=self, relx=0, rely=2/5,
            relwidth=2/6, relheight=1/5)

    def browse(self):
        if os.path.exists(self.root.folder_path):
            folder_path = tk.filedialog.askdirectory(initialdir = self.root.folder_path)
        else:
            folder_path = tk.filedialog.askdirectory(initialdir = os.getcwd())
        if folder_path:
            self.root.folder_path = folder_path
            self.pathlocation.config(text = folder_path)
            self.root.settings['folder_path'] = self.root.folder_path
        
            # Write to file
            f = open(os.getcwd()+'/settings_files/settings.txt', 'w')
            f.write(json.dumps(self.root.settings, cls=NumpyEncoder))
            f.close()
        self.updatefolder()
        self.root.run_choosen = ''

    def load(self, overwrite = False, delplots = True):

        t = self.ThreadClient(self.root.queue, self.load_thread, overwrite, delplots)
        t.start()
        self.schedule_check(t, delplots)

    def load_thread(self, overwrite = False, delplots = True):
        #Disable button
        self.root.disable_buttons()

        selection_to_load = self.root.folder_path+'/'+self.run_selected

        if os.path.exists(selection_to_load) and self.run_selected[:4] == 'Run-':

            # Big load
            updated, files_to_load, dat_files = load_data(selection_to_load, overwrite=overwrite)

            # Update histogram if needed
            if os.path.exists(selection_to_load+'/PythonAnalysis/hist.txt') and updated:
                
                if files_to_load == True:
                    # Load Parameters
                    self.root.parameters = load_parameters([selection_to_load+'/JSON/'+self.run_selected], write=selection_to_load+'/PythonAnalysis/params.txt', 
                                                        overwrite=overwrite, threshold=1000)
                    
                    # Hist limits
                    hist_limits = [self.root.parameters['TDC.min'][0],self.root.parameters['TDC.max'][0]]
                    if self.root.parameters['TDC.max'][0] - self.root.parameters['TDC.min'][0] > 3125000:
                        hist_limits[0] = self.root.parameters['TDC.max'][0] - 3125000

                    # Load Histogram
                    self.root.histogram = load_histogram([selection_to_load+'/JSON/'+self.run_selected],write=selection_to_load+'/PythonAnalysis/hist.txt', 
                                                        nr_bins=self.root.bin_size, overwrite=overwrite, 
                                                        hist_limits=hist_limits)
                    
                    if os.path.exists(selection_to_load+'/PythonAnalysis/hist_deplete.txt'):
                        # Load Depletion Histogram
                        self.root.histogram_deplete = load_histogram([selection_to_load+'/JSON/'+self.run_selected],write=selection_to_load+'/PythonAnalysis/hist_deplete.txt', 
                                                        nr_bins=self.root.bin_size, overwrite=overwrite, 
                                                        hist_limits=hist_limits)

                else:
                    # Load Parameters
                    self.root.parameters = load_parameters([selection_to_load+'/JSON/'+self.run_selected], write=selection_to_load+'/PythonAnalysis/params.txt', 
                                                        overwrite=updated, threshold=1000)
                    
                    # Hist limits
                    hist_limits = [self.root.parameters['TDC.min'][0],self.root.parameters['TDC.max'][0]]
                    if self.root.parameters['TDC.max'][0] - self.root.parameters['TDC.min'][0] > 3125000:
                        hist_limits[0] = self.root.parameters['TDC.max'][0] - 3125000
                    
                    # Load Histogram
                    self.root.histogram = update_histogram(dat_files, files_to_load, write=selection_to_load+'/PythonAnalysis/hist.txt', 
                                                        hist_limits=hist_limits)
                    
                    if os.path.exists(selection_to_load+'/PythonAnalysis/hist_deplete.txt'):
                        # Load Depletion Histogram
                        self.root.histogram_deplete = update_histogram(dat_files, files_to_load, write=selection_to_load+'/PythonAnalysis/hist_deplete.txt', 
                                                            hist_limits=hist_limits)
            
            # Otherwise just load the histogram
            else:
                # Load Parameters
                self.root.parameters = load_parameters([selection_to_load+'/JSON/'+self.run_selected], write=selection_to_load+'/PythonAnalysis/params.txt', 
                                                       overwrite=overwrite, threshold=1000)
                
                # Hist limits
                hist_limits = [self.root.parameters['TDC.min'][0],self.root.parameters['TDC.max'][0]]
                if self.root.parameters['TDC.max'][0] - self.root.parameters['TDC.min'][0] > 3125000:
                    hist_limits[0] = self.root.parameters['TDC.max'][0] - 3125000
                
                # Load Histogram
                self.root.histogram = load_histogram([selection_to_load+'/JSON/'+self.run_selected],write=selection_to_load+'/PythonAnalysis/hist.txt', 
                                                    nr_bins=self.root.bin_size, overwrite=overwrite, 
                                                        hist_limits=hist_limits)
                
                if os.path.exists(selection_to_load+'/PythonAnalysis/hist_deplete.txt'):
                    # Load Depletion Histogram
                    self.root.histogram_deplete = load_histogram([selection_to_load+'/JSON/'+self.run_selected],write=selection_to_load+'/PythonAnalysis/hist_deplete.txt', 
                                                    nr_bins=self.root.bin_size, overwrite=overwrite, 
                                                    hist_limits=hist_limits)
                
            self.root.run_choosen = self.run_selected

            # Update everything
            print(time.strftime('%H:%M:%S', time.gmtime())+' Updating parameters')
            self.container.parameters.load_update()
            print(time.strftime('%H:%M:%S', time.gmtime())+' Updating windows')
            self.container.windows.load_update()
            print(time.strftime('%H:%M:%S', time.gmtime())+' Updating calculations')
            self.container.calculations.load_update()
            print(time.strftime('%H:%M:%S', time.gmtime())+' Updating results')
            self.root.Command.results.update_lists_in_row()

            self.container.container.plotoptframe.parameters.load_update()
            self.container.container.plotoptframe.histogram.load_update()
            self.histlabel.config(text = 'Hist: V')

            

        # Re-enable buttons
        self.root.enable_buttons()
                    
    def schedule_check(self,t, delplots):
        if t.is_alive():
            self.after(50, lambda: self.schedule_check(t,delplots))
        else:
            # Ask to keep windows
            if len(self.root.tab_bar.winfo_children()) > 1 and delplots:
                self.cont = True
                self.windowed = False
                toplevel = self.load_proceed(self)
                toplevel.wait_window(toplevel)
                
                # Continue
                if not self.cont:
                    # Remove tabs
                    for item in self.root.tab_bar.winfo_children():
                        item.destroy()
                    
                    self.root.tab_bar.add(plot_frame(self.root.tab_bar, self.root), text="Empty Plot")
                    self.root.empty_tab = True
                    return
                elif self.windowed:
                    self.popout_windows()
                else:
                    self.rename_windows()

            elif self.root.tab_bar.tab(self.root.tab_bar.winfo_children()[0])['text'] != 'Empty Plot' and delplots:
                self.cont = True
                self.windowed = False
                toplevel = self.load_proceed(self)
                toplevel.wait_window(toplevel)
                
                # Continue
                if not self.cont:
                    # Remove tabs
                    for item in self.root.tab_bar.winfo_children():
                        item.destroy()
                    
                    self.root.tab_bar.add(plot_frame(self.root.tab_bar, self.root), text="Empty Plot")
                    self.root.empty_tab = True
                    return
                elif self.windowed:
                    self.popout_windows()
                else:
                    self.rename_windows()
    
    def update(self):
        selection_to_load = self.root.folder_path+'/'+self.run_selected
        if os.path.exists(selection_to_load) and self.run_selected[:4] == 'Run-':
            froze = False
            if len(self.container.windows.entries) > 0 and \
                len(self.container.windows.entries_back) > 0:
                self.container.windows.freeze()
                froze = True
                            
            self.load(delplots=False)

            if froze:
                self.container.windows.restore()

            # Update histogram plots
            self.container.parameters.update_histogram_plots()

            # Update result plots
            self.container.parameters.update_result_plots()
    
    def force(self):
        selection_to_load = self.root.folder_path+'/'+self.run_selected
        if os.path.exists(selection_to_load) and self.run_selected[:4] == 'Run-':
            self.cont = True
            toplevel = self.force_proceed(self)
            toplevel.wait_window(toplevel)

            if not self.cont:
                return
            
            self.load(overwrite=True)
                 
    def updatefolder(self):
        try:
            self.runlist.delete(0, tk.END) 
            lines = []
            for folder in sorted(os.listdir(self.root.folder_path)):
                if 'Run-' in folder:
                    if os.path.isdir(self.root.folder_path+'/'+folder):
                        lines.append(folder) 

            for line in lines:
                self.runlist.insert(tk.END, line)
        except:
            print(time.strftime('%H:%M:%S', time.gmtime())+' Directory doesn\'t exist')
    
    def on_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            data = event.widget.get(index)
            self.run_selected = data
        else:
            self.run_selected = ''
    
    def on_double_click(self, event):
    
        self.on_select(event)
        self.load(overwrite=False)

    def popout_windows(self):
        self.rename_windows()
        self.popout_windows_class(self, self.root)

        # Remove tabs
        for item in self.root.tab_bar.winfo_children():
            item.destroy()
        
        self.root.tab_bar.add(plot_frame(self.root.tab_bar, self.root), text="Empty Plot")
        self.root.empty_tab = True

    def rename_windows(self):
        # Make list of names in tab
        names = []
        for item in self.root.tab_bar.winfo_children():
            names.append(self.root.tab_bar.tab(item)['text'])

        number = 0
        for item in self.root.tab_bar.winfo_children():
            # Rename tab  
            new_name = self.root.tab_bar.tab(item)['text'].replace(' ', '_')
            new_name = new_name.replace('.', '_')

            # Remove beginning if already numbered
            if isint(new_name[:new_name.find('_')]):
                number = int(new_name[:new_name.find('_')])
                new_name = new_name[new_name.find('_')+1:]
            
            # Make sure we don't have two tabs of the same name
            while f'{number}_'+new_name in names:
                number += 1

            self.root.tab_bar.tab(self.root.tab_bar.index(item), text=f'{number}_'+new_name)
            number = 0
                    
    class load_proceed(tk.Toplevel):
        def __init__(_self, self, *args, **kwargs):
            super().__init__(self, *args, **kwargs)
            _self.title("Keep windows")

            # Create a label in the Toplevel window
            label = tk.Label(_self, text=f'Do you wish to keep current plots')
            label.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

            # Create "Continue" and "Cancel" buttons in the Toplevel window
            yes_button = tk.Button(_self, text="Yes", command=_self.continue_action)
            yes_pop_button = tk.Button(_self, text="Yes (in other window)", command=lambda : _self.continue1_action(self))
            cancel_button = tk.Button(_self, text="No", command=lambda : _self.cancel_action(self))

            yes_button.grid(row=1, column=0, padx=5, pady=5)
            yes_pop_button.grid(row=1, column=1,padx=5, pady=5)
            cancel_button.grid(row=1, column=2, padx=5, pady=5)

        def continue_action(self):
            self.destroy()

        def continue1_action(_self, self):
            self.windowed = True
            _self.destroy()

        def cancel_action(_self, self):
            self.cont = False
            _self.destroy()

    class force_proceed(tk.Toplevel):
        def __init__(_self, self, *args, **kwargs):
            super().__init__(self, *args, **kwargs)
            _self.title("Force load")

            # Create a label in the Toplevel window
            label = tk.Label(_self, text=f'Do you wish to recreate all files?')
            label.pack(padx=10, pady=10)

            # Create "Continue" and "Cancel" buttons in the Toplevel window
            yes_button = tk.Button(_self, text="Yes", command=_self.continue_action)
            cancel_button = tk.Button(_self, text="No", command=lambda : _self.cancel_action(self))

            yes_button.pack(side=tk.LEFT, padx=5, pady=5)
            cancel_button.pack(side=tk.RIGHT, padx=5, pady=5)

        def continue_action(self):
            self.destroy()

        def cancel_action(_self, self):
            self.cont = False
            _self.destroy()
        
    class popout_windows_class(tk.Toplevel):
        def __init__(_self, self, root, *args, **kwargs):
            super().__init__(self, *args, **kwargs)
            _self.title("Previous plots")
            _self.geometry(f'{root.tab_bar.winfo_width()}x{root.tab_bar.winfo_height()}')

            _self.root = root

            # Create frame for tabs
            _self.tab_bar = ttk.Notebook(_self)

            _self.tab_bar.grid(padx = 5, pady = 5, row=0, column=0, sticky=tk.N+tk.W+tk.E+tk.S)

            _self.tab_bar.bind('<Button-3>', _self.close_tab)

            # Load the tabs
            for item in root.tab_bar.winfo_children():
                # Clone
                clone = _self.clone_widget(item, _self.tab_bar)
                _self.tab_bar.add(clone, text=root.tab_bar.tab(item)['text'])

            _self.bind('<Configure>', _self.resize)

        def resize(_self, event):
            width = _self.winfo_width()
            height = _self.winfo_height()

            padx = 5 / width
            pady = 5 / height

            # place the window, giving it an explicit size
            _self.tab_bar.place(in_=_self, relx=padx, rely=pady, 
                    relwidth=1 - 2 * pady, relheight=1 - 2 * pady)
        
        def close_tab(_self, event):
            clicked_tab = _self.tab_bar.tk.call(_self.tab_bar._w, "identify", "tab", event.x, event.y)
            active_tab = _self.tab_bar.index(_self.tab_bar.select())

            if clicked_tab == active_tab:
                for item in _self.tab_bar.winfo_children():
                    if _self.tab_bar.index(item) == clicked_tab:
                        if len(_self.tab_bar.winfo_children()) > 1:
                            item.destroy()
                            return
                        else:
                            _self.destroy()
                            return
                        
        # Ripped from the internet
        def clone_widget(_self, widget, master=None, nav = False):
            """
            Create a cloned version o a widget

            Parameters
            ----------
            widget : tkinter widget
                tkinter widget that shall be cloned.
            master : tkinter widget, optional
                Master widget onto which cloned widget shall be placed. If None, same master of input widget will be used. The
                default is None.

            Returns
            -------
            cloned : tkinter widget
                Clone of input widget onto master widget.

            """
            # Get main info
            parent = master if master else widget.master
            cls = widget.__class__
            # Clone the widget configuration
            cfg = {key: widget.cget(key) for key in widget.configure()}
            try:
                cloned = cls(parent, **cfg)
            except:
                cloned = cls(parent, _self.root, **cfg)
            
            if isinstance(widget , figure):
                # Figure
                cloned.fig = widget.fig
            
                # creating the Tkinter canvas
                cloned.canvas = FigureCanvasTkAgg(cloned.fig, master = cloned)  
                cloned.canvas.draw()
                cloned.canvas.get_tk_widget().pack()
            
                # creating the Matplotlib toolbar
                cloned.toolbar = NavigationToolbar2Tk(cloned.canvas, cloned)
                cloned.toolbar.update()
            
                # placing the toolbar on the Tkinter window
                cloned.canvas.get_tk_widget().pack()

            else:
                # Clone the widget's children
                for child in widget.winfo_children():
                    child_cloned = _self.clone_widget(child, master=cloned)
                    if child.grid_info():
                        grid_info = {k: v for k, v in child.grid_info().items() if k not in {'in'}}
                        child_cloned.grid(**grid_info)
                    elif child.place_info():
                        place_info = {k: v for k, v in child.place_info().items() if k not in {'in'}}
                        child_cloned.place(**place_info)
                    else:
                        pack_info = {k: v for k, v in child.pack_info().items() if k not in {'in'}}
                        child_cloned.pack(**pack_info)
                
            return cloned

    class ThreadClient(Thread):
        def __init__(self, queue, fcn, overwrite, delplot):
            Thread.__init__(self, args = (overwrite, delplot))
            self.queue = queue
            self.fcn = fcn
            self.overwrite = overwrite
            self.delplot = delplot
        def run(self):
            time.sleep(1)
            self.queue.put(self.fcn(self.overwrite, self.delplot))