import numpy as np
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
from math import pi

def generate_afl_oval(v, plot_grid = True):

    venueDims = {'MCG': {'venueLength': 160, 'venueWidth': 141},
                'Marvel Stadium': {'venueLength': 160, 'venueWidth': 129},
                'Adelaide Oval': {'venueLength': 167, 'venueWidth': 123},
                'Heritage Bank Stadium': {'venueLength': 161, 'venueWidth': 134},
                'GIANTS Stadium': {'venueLength': 164, 'venueWidth': 128},
                'Gabba': {'venueLength': 156, 'venueWidth': 138},
                'Optus Stadium': {'venueLength': 165, 'venueWidth': 130},
                'SCG': {'venueLength': 155, 'venueWidth': 136},
                'University of Tasmania Stadium': {'venueLength': 170, 'venueWidth': 140},
                'Norwood Oval': {'venueLength': 165, 'venueWidth': 109},
                'Adelaide Hills': {'venueLength': 152, 'venueWidth': 111},
                'Manuka Oval': {'venueLength': 162, 'venueWidth': 138},
                'GMHBA Stadium': {'venueLength': 170, 'venueWidth': 115},
                'Blundstone Arena': {'venueLength': 160, 'venueWidth': 124},
                'Mars Stadium': {'venueLength': 160, 'venueWidth': 129},
                'TIO Stadium': {'venueLength': 175, 'venueWidth': 135},
                'TIO Traeger Park': {'venueLength': 168, 'venueWidth': 132}}

    
    x_lim = venueDims[v]['venueLength'] / 2
    y_lim = venueDims[v]['venueWidth'] / 2
    
    # Optionally plot grid
    if plot_grid:
        plt.grid(color='lightgray',linestyle='--')

    # Plot oval shape
    t = np.linspace(0, 2*pi, 100)
    plt.plot(x_lim*np.cos(t) ,y_lim*np.sin(t), 'k-')
    
    # Generate 50m lines
    x = np.arange(0, 50.1, 0.1)
    y = np.sqrt(50**2 - x**2)
    x = np.concatenate([x,x[::-1]]) - x_lim
    y = np.concatenate([y,-y[::-1]])

    # Clip 50m lines at boundary
    cos_angle = np.cos(np.radians(180.))
    sin_angle = np.sin(np.radians(180.))
    xct = x * cos_angle - y * sin_angle
    yct = x * sin_angle + y * cos_angle
    rad_cc = np.array((xct**2/(x_lim)**2) + (yct**2/(y_lim)**2))
    clip_circle = rad_cc < 1
    y = y[clip_circle]
    x = x[clip_circle]

    # Plot 50m lines
    plt.plot(x, y,'k-', -x, y, 'k-')

    # Plot goal square
    x_sq = np.array([x_lim, x_lim-9 , x_lim-9, x_lim])
    y_sq = np.array([6.4, 6.4, -6.4, -6.4])
    plt.plot(x_sq, y_sq,'k-', -x_sq, y_sq, 'k-')

    # Plot centre square
    plt.plot([-25, -25, 25, 25, -25], [-25, 25, 25, -25, -25], 'k-')

    # Plot centre point
    plt.scatter(0,0,s=15)

    plt.show()