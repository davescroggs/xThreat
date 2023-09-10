# %%
import pandas as pd
import numpy as np

bin_period = 25

venueWidth = (141/2)
venueLength = (160/2)
defaultVenue = 'MCG'

chains_processed =  pd.read_pickle("../data/chains_processed.pkl")

def bin_values(col, dir='x'):
    if dir == 'x':
        s = -venueLength; e = venueLength
    else:
        s = -venueWidth; e = venueWidth
    col = np.select([col > e, col < s], [e-0.1, s+0.1],default=col)
    return pd.cut(col, pd.interval_range(start=s, end=e, periods=bin_period, closed='right'), include_lowest=True, precision=2)

x_bins = pd.interval_range(start=-venueLength, end=venueLength, periods=bin_period, closed='right')
y_bins = pd.interval_range(start=-venueWidth, end=venueWidth, periods=bin_period, closed='right')

chains_processed = chains_processed.assign(xInitialPoss_bin=bin_values(chains_processed.x, 'x'),
                                                yInitialPoss_bin=bin_values(chains_processed.y, 'y'),
                                                xFinalPoss_bin=bin_values(chains_processed.x_next, 'x'),
                                                yFinalPoss_bin=bin_values(chains_processed.y_next, 'y'))

disposal_actions = ['Kick', 'Handball', 'Ground Kick', 'Kickin short', 'Kickin long', 'Kickin play on']

# %%
position_summary = chains_processed[chains_processed.description.isin(disposal_actions)]

position_summary = (position_summary.groupby(['xInitialPoss_bin','yInitialPoss_bin'])
            .agg(total_events = ('x', 'size'),
                 total_shots = ('shotAtGoal', 'sum'),
                 total_points = ('points', 'sum')))
position_summary['total_moves'] = position_summary.total_events - position_summary.total_shots
position_summary['move_prob'] = position_summary.total_moves/position_summary.total_events
position_summary['shot_prob'] = position_summary.total_shots/position_summary.total_events
position_summary['xPoints'] = position_summary.total_points/position_summary.total_shots
## Remove influence of low count transitions
position_summary['xPoints'] = np.where(position_summary.total_events < 10, 0, position_summary.xPoints)
position_summary = position_summary.fillna(0)
position_summary['shotXp'] = position_summary.shot_prob * position_summary.xPoints

#%% Iterative step
transitions = chains_processed[chains_processed.description.isin(disposal_actions)].groupby(['xInitialPoss_bin','yInitialPoss_bin','xFinalPoss_bin', 'yFinalPoss_bin']).size().rename('total_events')
xT = chains_processed.groupby(['xFinalPoss_bin', 'yFinalPoss_bin']).x.count().apply(lambda x: 0)

## Iterate 8 times, simulating 8 moves ahead
for i in range(8):
    xT_start = xT
    tX = transitions.div(position_summary.total_events, fill_value=0).replace(np.NaN, 0)
    tX = tX.mul(xT).groupby(['xInitialPoss_bin','yInitialPoss_bin']).sum()
    xT = position_summary.shotXp + position_summary.move_prob * tX
    print("Diff: ", sum(abs(xT - xT_start)))

xT_df = (chains_processed[chains_processed.description.isin(disposal_actions)]
        .merge(xT.rename('xT_start').reset_index(), how='left', on=['xInitialPoss_bin', 'yInitialPoss_bin'])
        .merge(xT.reset_index().rename(columns={0: 'xT_end','xInitialPoss_bin': 'xFinalPoss_bin', 'yInitialPoss_bin': 'yFinalPoss_bin'}), how='left', on=['xFinalPoss_bin', 'yFinalPoss_bin'])
        # .drop(['xInitialPoss_bin', 'yInitialPoss_bin', 'xFinalPoss_bin', 'yFinalPoss_bin'], axis=1)
        )
xT_df['deltaXT'] = xT_df.xT_end - xT_df.xT_start

xT_df.to_pickle("../data/xT.pkl")