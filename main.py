"""                                              Imort                                                             """
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
import traceback
from inspect import signature
from inspect import getfullargspec
from src.FittingRoutine import FittingRoutine

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

from include.control import *

"""                                              Main                                                                """
if __name__ == '__main__':
    '''              GUI                  '''
    
    control_app = ControlWindow()
    control_app.mainloop()
