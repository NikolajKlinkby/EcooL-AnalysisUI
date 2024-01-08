from FittingRoutine import *
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(-6000,1000, 1000)

plt.plot(x, exp_gauss_dist(x, 1e+6, 0, 150, -0.001, 0))
plt.show()
