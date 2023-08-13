import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
from math import pi

def generate_afl_oval(v):

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

    plt.grid(color='lightgray',linestyle='--')
    t = np.linspace(0, 2*pi, 500)

    x_sq = np.array([x_lim, x_lim-9 , x_lim-9, x_lim])
    y_sq = np.array([3.2, 3.2, -3.2, -3.2])
    plt.plot(x_sq, y_sq, 'k-', -x_sq, y_sq, 'k-')

    # Plot goal line
    goal_linex = np.array([x_lim, x_lim])
    goal_liney = np.array([-9.6, 9.6])

    # Plot posts
    goal_post_x = x_sq[[0,3]]
    goal_post_y = y_sq[[0,3]]

    in_bounds = False

    # Find ellipse dimensions to have a straight goal line
    while not in_bounds:
        x_lim += 0.01; y_lim += 0.01*0.8; 
        rad_cc = np.array(((-goal_linex)**2/(x_lim)**2) + ((-goal_liney)**2/(y_lim)**2))
        in_bounds = all(rad_cc < 1)

    x = x_lim*np.cos(t)
    y = y_lim*np.sin(t)
    plt.plot(x[(x<goal_linex[0]) & (x>-goal_linex[0])], y[(x<goal_linex[0]) & (x>-goal_linex[0])], 'k-')

    # Generate 50m lines
    x = np.arange(0, 50.1, 0.1)
    y = np.sqrt(50**2 - x**2)
    x = np.concatenate([x,x[::-1]]) - x_lim
    y = np.concatenate([y,-y[::-1]])

    rad_cc = np.array(((-x)**2/(x_lim)**2) + ((-y)**2/(y_lim)**2))
    clip_circle = rad_cc < 1

    y = y[clip_circle]; x = x[clip_circle]
    plt.plot(x, y, 'k-', -x, y, 'k-')

    plt.plot(goal_linex, goal_liney, 'k-', -goal_linex, goal_liney, 'k-')
    plt.plot(goal_post_x, goal_post_y, 'ro', -goal_post_x, goal_post_y, 'ro', markersize=3)
    plt.plot(goal_post_x, goal_post_y + [6.4, -6.4], 'bo', -goal_post_x, goal_post_y + [6.4, -6.4], 'bo',markersize=3)
    # Centre square
    plt.plot([-25, -25, 25, 25, -25], [-25, 25, 25, -25, -25], 'k-')

    plt.scatter(0,0,s=15)

    plt.show()


def plot_events(possession_summary, chains_processed, id=None, id_type="chainId", print_id=False):

    def label_point(x, y, val, ax):
        a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
        for i, point in a.iterrows():
            ax.text(point['x'], point['y'], str(point['val']), color='white', verticalalignment='center', horizontalalignment='center')
            
    # For no id supplied, show a random example
    if (id is None):
        id = possession_summary[id_type].sample(1).values
    elif (~isinstance(id,np.ndarray)):
        id = np.array(id)

    if print_id:
        print(id)
        
    plot_df = possession_summary[possession_summary[id_type].isin(id)].sort_values('possessionNum').copy()

    game_info = chains_processed[chains_processed[id_type].isin(id)][['season', 'roundNumber', 'homeTeam', 'awayTeam']].drop_duplicates()
    game_title = 'Round ' + game_info.roundNumber.map(str) + ' ' + game_info.season.map(str) + ' ' + game_info.homeTeam + ' vs. ' + game_info.awayTeam

    time_info = chains_processed[chains_processed[id_type].isin(id)][['season', 'roundNumber', 'homeTeam', 'awayTeam', 'period', 'periodSeconds']].drop_duplicates()
    time_info = 'Qtr ' + time_info.period.values[0].astype(str) + ": " + time_info.periodSeconds.values[0].astype(str) + '-' + time_info.periodSeconds.values[-1].astype(str) + ' seconds'

    id_info = id_type + ' ' + ", ".join(id.tolist())

    # plot_df = pd.wide_to_long(plot_df, stubnames=['x', 'y'], i=['possessionNum'], j='state', suffix=r'\w+').reset_index()
    plot_df_wide = pd.wide_to_long(plot_df, stubnames=['x', 'y'], i=['possessionNum'], j='state', suffix=r'\w+').reset_index()
    plt.figure(figsize=(13,9))
    for _, rows in plot_df.iterrows():
        x = (rows.xFinalPoss, rows.xNextPos)
        y = (rows.yFinalPoss, rows.yNextPos)
        plt.plot(x, y, 'r-')
        x = (rows.xInitialPoss, rows.xFinalPoss)
        y = (rows.yInitialPoss, rows.yFinalPoss)
        plt.plot(x, y, 'b--')
    label_point(plot_df.xInitialPoss, plot_df.yInitialPoss, plot_df.possessionNum.astype(str), plt.gca())
    plt.plot(plot_df['xInitialPoss'], plot_df['yInitialPoss'], 'ko', markersize=14)
    plt.title(game_title.values[0] + '\n' + time_info)
    plt.figtext(0.5, 0.01, id_info, wrap=True, horizontalalignment='center', fontsize=12)
    generate_afl_oval(plot_df.venueName.values[0])
    plt.show()