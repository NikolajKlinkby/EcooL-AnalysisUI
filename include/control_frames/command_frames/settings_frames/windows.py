import os
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import numpy as np
from threading import Thread
import json
import time
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

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

def string_divider(str):
    ret = []
    for s in str[::1]:
        ret.append(s)
    return np.array(ret)

class windows(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        self.root = root
        
        options = {'padx': 5, 'pady': 5}

        '''          Background window           '''
        # Create a canvas for scrolling
        self.canvas_back = tk.Canvas(self)
        self.canvas_back.grid(row=0, column=0, sticky='nswe')

        # Create a vertical scrollbar
        self.scrollbar_back = ttk.Scrollbar(self, orient="vertical", command=self.canvas_back.yview)
        self.scrollbar_back.grid(row=0, column=1, sticky='nse')
        self.canvas_back.configure(yscrollcommand=self.scrollbar_back.set)

        # Create a frame inside the canvas to hold the widgets
        self.inner_frame_back = ttk.Frame(self.canvas_back)
        self.canvas_back.create_window((0, 0), window=self.inner_frame_back, anchor="nw", tags='inner_frame')
        self.inner_frame_back.grid_propagate(False)

        self.entries_back = []

        # Add table header
        height = 1.5/15 * self.canvas_back.winfo_reqheight()
        y = (len(self.entries_back)+1) * height

        width = self.canvas_back.winfo_reqwidth()/1.5
        
        self.back_win_label = ttk.Label(self.inner_frame_back, text=f'Background win', borderwidth=1, relief='solid')
        self.back_win_label.place(x=0, y=y, width=4/10*width, height=height)

        self.back_from_label = ttk.Label(self.inner_frame_back, text=f'From', borderwidth=1, relief='solid')
        self.back_from_label.place(x=4/10*width, y=y, width=3/10*width, height=height)

        self.back_to_label = ttk.Label(self.inner_frame_back, text=f'To', borderwidth=1, relief='solid')
        self.back_to_label.place(x=7/10*width, y=y, width=3/10*width, height=height)

        self.canvas_back.itemconfigure("inner_frame", height=(len(self.entries_back)+2) * height)
        self.canvas_back.itemconfigure("inner_frame", width=self.canvas_back.winfo_reqwidth())

        '''          Windows           '''
        # Create a canvas for scrolling
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=1, column=0, sticky='nswe')

        # Create a vertical scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=1, column=1, sticky='nse')
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
        
        self.name_label = ttk.Label(self.inner_frame, text=f'Name', borderwidth=1, relief='solid')
        self.name_label.place(x=0, y=y, width=2/10*width, height=height)

        self.detector_label = ttk.Label(self.inner_frame, text=f'Detector', borderwidth=1, relief='solid')
        self.detector_label.place(x=2/10*width, y=y, width=4/10*width, height=height)

        self.from_label = ttk.Label(self.inner_frame, text=f'From', borderwidth=1, relief='solid')
        self.from_label.place(x=6/10*width, y=y, width=1.5/10*width, height=height)

        self.to_label = ttk.Label(self.inner_frame, text=f'To', borderwidth=1, relief='solid')
        self.to_label.place(x=7.5/10*width, y=y, width=1.5/10*width, height=height)

        self.delete_label = ttk.Label(self.inner_frame, text=f'Del', borderwidth=1, relief='solid')
        self.delete_label.place(x=9/10*width, y=y, width=1/10*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        '''        Buttons         '''

        # Save and restore
        self.savebut = tk.Button(self, text='Save', command=self.save)
        self.savebut.grid(row=2, column=0)

        self.restorebut = tk.Button(self, text='Restore', command=self.restore)
        self.restorebut.grid(row=2, column=0)

        # F and +

        self.freezebut = tk.Button(self, text='F', command=self.freeze)
        self.freezebut.grid(row=2, column=1)
        self.frozen = False

        self.plusbut = tk.Button(self, text='+', command=lambda : self.add_row(self.root.histogram['time_keys'][0],self.root.histogram['time_keys']))
        self.plusbut.grid(row=2, column=1)

        # Disable buttons
        self.savebut['state'] = 'disabled'
        self.restorebut['state'] = 'disabled'
        self.freezebut['state'] = 'disabled'
        self.plusbut['state'] = 'disabled'

        # Function to update scroll region whenever widgets are added or removed
        self.inner_frame_back.bind("<Configure>", self.update_canvas)
        self.canvas_back.bind("<Configure>", self.update_canvas)
        self.inner_frame.bind("<Configure>", self.update_canvas)
        self.canvas.bind("<Configure>", self.update_canvas)

        self.bind('<Configure>', self.resize)

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 2 / 50

        back_height = 8.5*2 / 50
        front_height = 8.5*3 / 50

        # place the window, giving it an explicit size
        self.scrollbar_back.place(in_=self, relx=1 - padx - scrollbarwidth, rely=0,
            relwidth=scrollbarwidth, relheight=back_height - pady)
        
        self.canvas_back.place(in_=self, relx=0, rely=0,
            relwidth=1- 2 * padx - scrollbarwidth, relheight=back_height - pady)
        
        self.scrollbar.place(in_=self, relx=1 - padx - scrollbarwidth, rely=back_height, 
            relwidth=scrollbarwidth, relheight=front_height)
        
        self.canvas.place(in_=self, relx=0, rely=back_height,
            relwidth=1- 2 * padx - scrollbarwidth, relheight=front_height)
        
        self.savebut.place(in_=self, relx=0, rely=8.5/10 + pady, 
            relwidth=3/10, relheight=1.5/10 - pady)
        
        self.restorebut.place(in_=self, relx=3/10+padx, rely=8.5/10 + pady, 
            relwidth=3/10, relheight=1.5/10 - pady)
        
        self.freezebut.place(in_=self, relx=8/10-padx, rely=8.5/10 + pady, 
            relwidth=1/10, relheight=1.5/10 - pady)
        
        self.plusbut.place(in_=self, relx=9/10, rely=8.5/10 + pady,
            relwidth=1/10, relheight=1.5/10 - pady)
        
        # Resize table headers
        
        self.canvas_back.update()

        height = 1.5/15 * self.canvas_back.winfo_reqheight()
        y = 0

        width = self.canvas_back.winfo_reqwidth()
        
        self.back_win_label.place(in_=self.inner_frame_back, x=0, y=y, width=5/10*width, height=height)

        self.back_from_label.place(in_=self.inner_frame_back, x=5/10*width, y=y, width=2/10*width, height=height)

        self.back_to_label.place(in_=self.inner_frame_back, x=7/10*width, y=y, width=2/10*width, height=height)

        self.canvas_back.itemconfigure("inner_frame", height=(len(self.entries_back)+2) * height)
        self.canvas_back.itemconfigure("inner_frame", width=self.canvas_back.winfo_reqwidth())
        
        self.canvas.update()

        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = 0

        width = self.canvas.winfo_reqwidth()
        
        self.name_label.place(in_=self.inner_frame, x=0, y=y, width=2/10*width, height=height)

        self.detector_label.place(in_=self.inner_frame, x=2/10*width, y=y, width=3/10*width, height=height)

        self.from_label.place(in_=self.inner_frame, x=5/10*width, y=y, width=1.5/10*width, height=height)

        self.to_label.place(in_=self.inner_frame, x=6.5/10*width, y=y, width=1.5/10*width, height=height)

        self.delete_label.place(in_=self.inner_frame, x=8/10*width, y=y, width=1/10*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())

        self.update_rows()
    
    def update_canvas(self, event):
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        self.canvas_back.itemconfigure("inner_frame", width=self.canvas_back.winfo_reqwidth())

        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=self.winfo_width())
        self.canvas_back.configure(scrollregion=self.canvas_back.bbox("all"), width=self.winfo_width())

    def update_rows(self):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        width = self.canvas.winfo_reqwidth()

        count = 0

        for e in self.entries:
            y = (count+1) * height
            
            e[0].place(x=0, y=y, width=2/10*width, height=height)
            e[1].place(x=2/10*width, y=y, width=3/10*width, height=height)
            e[2].place(x=5/10*width, y=y, width=1.5/10*width, height=height)
            e[3].place(x=6.5/10*width, y=y, width=1.5/10*width, height=height)
            e[4].place(x=8/10*width, y=y, width=1/10*width, height=height)

            count += 1

        height = 1.5/15 * self.canvas_back.winfo_reqheight()
        width = self.canvas_back.winfo_reqwidth()

        count = 0

        for e in self.entries_back:
            y = (count+1) * height
            
            e[0].place(x=0, y=y, width=5/10*width, height=height)
            e[1].place(x=5/10*width, y=y, width=2/10*width, height=height)
            e[2].place(x=7/10*width, y=y, width=2/10*width, height=height)

            count += 1

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        self.canvas_back.itemconfigure("inner_frame", height=(len(self.entries_back)+2) * height)
        self.canvas_back.itemconfigure("inner_frame", width=self.canvas_back.winfo_reqwidth())

    def add_row(self, key, options):
        height = 1.5/15 * self.canvas.winfo_reqheight()
        y = (len(self.entries)+1) * height

        width = self.canvas.winfo_reqwidth()
        
        label = ttk.Entry(self.inner_frame, background='white')
        label.insert(0,f'win{len(self.entries)+1}')
        label.place(x=0, y=y, width=2/10*width, height=height)
        
        variable = tk.StringVar()
        variable.set(key)

        optmen = ttk.OptionMenu(self.inner_frame, variable, variable.get(), *options)
        optmen.place(x=2/10*width, y=y, width=3/10*width, height=height)
        
        entry1 = ttk.Entry(self.inner_frame, validate='key')
        entry1.insert(0, '100')
        entry1.place(x=5/10*width, y=y, width=1.5/10*width, height=height)
        entry1['validatecommand'] = (entry1.register(self.entry_validate),'%P')
        
        entry2 = ttk.Entry(self.inner_frame, validate='key')
        entry2.insert(0, '300')
        entry2.place(x=6.5/10*width, y=y, width=1.5/10*width, height=height)
        entry2['validatecommand'] = (entry2.register(self.entry_validate),'%P')
        
        checkbox = ttk.Checkbutton(self.inner_frame, command=lambda : self.del_but(label))
        checkbox.place(x=8/10*width, y=y, width=1/10*width, height=height)

        self.canvas.itemconfigure("inner_frame", height=(len(self.entries)+2) * height)
        self.canvas.itemconfigure("inner_frame", width=self.canvas.winfo_reqwidth())
        
        self.entries.append((label, optmen, entry1, entry2, checkbox, variable))

    def add_back_row(self, param):
        height = 1.5/15 * self.canvas_back.winfo_reqheight()
        y = (len(self.entries_back)+1) * height

        width = self.canvas_back.winfo_reqwidth()
        
        label = ttk.Label(self.inner_frame_back, text=param, background='white', borderwidth=1, relief='solid')
        label.place(x=0, y=y, width=5/10*width, height=height)
        
        entry1 = ttk.Entry(self.inner_frame_back, validate='key')
        entry1.insert(0,'100')
        entry1.place(x=5/10*width, y=y, width=2/10*width, height=height)
        entry1['validatecommand'] = (entry1.register(self.back_entry_validate),'%P')
        
        entry2 = ttk.Entry(self.inner_frame_back, validate='key')
        entry2.insert(0,'300')
        entry2.place(x=7/10*width, y=y, width=2/10*width, height=height)
        entry2['validatecommand'] = (entry2.register(self.back_entry_validate),'%P')

        self.canvas_back.itemconfigure("inner_frame", height=(len(self.entries_back)+2) * height)
        self.canvas_back.itemconfigure("inner_frame", width=self.canvas_back.winfo_reqwidth())
        
        self.entries_back.append((label, entry1, entry2))

    def back_entry_validate(self, val):
        try:
            if isfloat(val) or val == '':
                return True
            elif all(string_divider(val) == ' '):
                return True
            else:
                return False
        except:
            return False

    def entry_validate(self, val):
        try:
            if isfloat(val) or val == '':
                self.unfreeze(val)
                return True
            elif all(string_divider(val) == ' '):
                self.unfreeze(val)
                return True
            else:
                return False
        except:
            return False

    def del_all_rows(self):
        for i in self.entries:
            for j in range(5):
                i[j].destroy()
        self.entries = []

        for i in self.entries_back:
            for j in i:
                j.destroy()
        self.entries_back = []

    def del_but(self,event):
        # Delete row
        row = self.find_row(event)
        self.del_row(row)
        
        # Move rows up
        self.update_rows()

    def find_row(self, event):
        row = 0
        for entry in self.entries:
            if entry[0] == event:
                return row
            else:
                row += 1
        else:
            return row

    def del_row(self, row):
        # Delete row visually
        for j in range(5):
            self.entries[row][j].destroy()

        # Make new entry list
        new_list = []
        for r in range(len(self.entries)):
            if r != row:
                new_list.append(self.entries[r])
        self.entries = new_list

    def save(self):
        
        self.frozen = False
        self.freezebut['state'] = 'normal'

        print(time.strftime('%H:%M:%S', time.gmtime())+' Saving windows for ' + self.root.run_choosen)
        selection_to_save = self.root.folder_path+'/'+self.root.run_choosen+'/PythonAnalysis/windows.txt'
        
        self.root.windows = {}

        # Get from background
        for entry in self.entries_back:
            self.root.windows[entry[0]['text']] = [entry[1].get(), entry[2].get()]

        # Get from windows
        for entry in self.entries:
            self.root.windows[entry[0].get()] = [entry[5].get(), entry[2].get(), entry[3].get()]

        # Write
        f = open(selection_to_save, 'w')
        f.write(json.dumps(self.root.windows, cls=NumpyEncoder))
        f.close()

        self.restorebut['state'] = 'normal'

    def restore(self):
        # Reset
        self.del_all_rows()

        # Load
        print(time.strftime('%H:%M:%S', time.gmtime())+' Loading windows from ' + self.root.run_choosen)
        selection_to_load = self.root.folder_path+'/'+self.root.run_choosen+'/PythonAnalysis/windows.txt'

        if not self.frozen and os.path.exists(selection_to_load):
            f = open(selection_to_load, 'r')
            self.root.windows = json.loads(f.read())
            f.close()

        for key in self.root.windows.keys():
            # Background
            if len(self.root.windows[key]) == 2:
                self.add_back_row(key)
                
                self.entries_back[-1][1].delete(0,'end')
                self.entries_back[-1][1].insert(0,self.root.windows[key][0])

                self.entries_back[-1][2].delete(0,'end')
                self.entries_back[-1][2].insert(0,self.root.windows[key][1])

            if len(self.root.windows[key]) == 3:
                self.add_row(self.root.windows[key][0], self.root.histogram['time_keys'])
                
                self.entries[-1][0].delete(0,'end')
                self.entries[-1][0].insert(0,key)

                self.entries[-1][2].delete(0,'end')
                self.entries[-1][2].insert(0,self.root.windows[key][1])

                self.entries[-1][3].delete(0,'end')
                self.entries[-1][3].insert(0,self.root.windows[key][2])

        self.unfreeze(1)

    def freeze(self):
        self.root.windows = {}

        # Get from background
        for entry in self.entries_back:
            self.root.windows[entry[0]['text']] = [entry[1].get(), entry[2].get()]

        # Get from windows
        for entry in self.entries:
            self.root.windows[entry[0].get()] = [entry[5].get(), entry[2].get(), entry[3].get()]


        self.frozen = True
        self.restorebut['state'] = 'normal'
        self.freezebut['state'] = 'disabled'

    def load_update(self):
        # Reset
        self.del_all_rows()
        
        selection_to_load = self.root.folder_path+'/'+self.root.run_choosen+'/PythonAnalysis/windows.txt'
        
        self.freezebut['state'] = 'normal'
        # Looad from freeze
        if self.frozen:
            self.freezebut['state'] = 'disabled'
            self.restore()
            self.restorebut['state'] = 'normal'
        else:
            self.restorebut['state'] = 'disabled'
            
            # Load from file
            if os.path.exists(selection_to_load):
                self.restore()
                self.restorebut['state'] = 'normal'
            # Create
            else:
                for key in self.root.histogram['time_keys']:
                    # Add to background
                    self.add_back_row(key)

                    # Add to window
                    self.add_row(key, self.root.histogram['time_keys'])

        # Enable buttons
        self.savebut['state'] = 'normal'
        self.plusbut['state'] = 'normal'
            
    def unfreeze(self, event):
        self.frozen = False
        self.freezebut['state'] = 'normal'

        self.restorebut['state'] = 'disabled'
        selection_to_load = self.root.folder_path+'/'+self.root.run_choosen+'/PythonAnalysis/windows.txt'
        if os.path.exists(selection_to_load):
            self.restorebut['state'] = 'normal'

