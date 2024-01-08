import os, sys
import subprocess
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import numpy as np
from threading import Thread
import time
import queue
import traceback
from inspect import signature
from inspect import getfullargspec
from include.FittingRoutine import FittingRoutine

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

class status_frame(tk.LabelFrame):
    def __init__(self, container, root, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        options = {'padx': 5, 'pady': 5}
        
        self.text_widget = tk.Text(self, wrap=tk.WORD, height=20, width=80)
        self.text_widget.grid(**options, row=0, column=0, sticky=tk.W)

        self.scrollbar = tk.Scrollbar(self, command=self.text_widget.yview)
        self.scrollbar.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E)
        self.text_widget.config(yscrollcommand=self.scrollbar.set)
        
        sys.stdout = StdoutRedirector(self.text_widget)

        # show the frame on the container
        self.grid(**options)

        self.bind('<Configure>', self.resize)

    def resize(self, event):
        width = self.winfo_width()
        height = self.winfo_height()

        padx = 5 / width
        pady = 5 / height

        scrollbarwidth = 1 / 50

        # place the window, giving it an explicit size
        self.text_widget.place(in_=self, relx=padx, rely=pady, 
            relwidth=1 - 5 * padx - scrollbarwidth, relheight=1 - 2 * pady)
        
        # place the window, giving it an explicit size
        self.scrollbar.place(in_=self, relx=1 - 6 * padx, rely=pady, 
            relwidth= scrollbarwidth, relheight=1 - 2 * pady)

                 

class StdoutRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

        self.empty()

    def write(self, message):
        self.text_widget.insert("1.0", message)

    def empty(self):
        max_lines = 100

        count = self.text_widget.get("1.0",tk.END).count('\n')
        if count > max_lines:
            self.text_widget.delete(f'end-{count-max_lines}l', tk.END)

        self.text_widget.after(2000,self.empty)