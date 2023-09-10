#%%

import pandas as pd
import numpy as np
from scipy.stats import binned_statistic_2d
import time

# Use MCG dimensions as default
venueWidth = (141/2)
venueLength = (160/2)
venueDims = (-venueLength, venueLength, -venueWidth, venueWidth)
defaultVenue = 'MCG'

# Process raw chains data
st = time.time()
chains_raw =  pd.read_csv("data/chains_data.csv")

## Rename columns
chains_raw.rename(columns={'homeTeam.teamName': "homeTeam",
  'awayTeam.teamName': "awayTeam",
  'homeTeamScore.totalScore': 'homeTeamScore',
  'awayTeamScore.totalScore': 'awayTeamScore',
  'chain_number': "chainNumber",
  'venue.name': "venueName",
  'team': "playingFor"}, inplace=True)

# Create columns fr grouping for easy summarising

game_identifiers = ['season', 'roundNumber', 'homeTeam']
chain_identifiers = game_identifiers + ['chainNumber']
possession_identifiers = chain_identifiers + ['possessionNum']

print("Starting processing...")
# Create ID for chains and possession for easy lookup
chains_raw['chainId'] = chains_raw.season.astype(str) + "_" + chains_raw.roundNumber.astype(str) + "_" + chains_raw.homeTeam.apply(lambda x: x.replace(" ", "_")) + "_C" + chains_raw.chainNumber.astype(str)

# Remove Kick Into F50 type results
chains_processed = chains_raw[~chains_raw.description.isin(['Kick Into F50','Kick Inside 50 Result', 'Inside 50', 'Shot At Goal', 'Centre Bounce', 'Mark Fumbled', 'Mark Dropped', 'Tackle','Debit','Credit','No Pressure Error'])].copy()
chains_processed['date'] = pd.to_datetime(chains_processed['date'])
chains_processed = chains_processed.sort_values(by=['season', 'roundNumber', 'date', 'homeTeam', 'displayOrder'])
# Create number for each possession
chains_processed['possessionNum'] = chains_processed.groupby(["roundNumber", "homeTeam", "period", "chainNumber"],  group_keys=False)['playerId'].apply(lambda s: s.ne(s.shift()).cumsum())
chains_processed['possessionId'] = chains_processed['chainId'] + "_P" + chains_processed.possessionNum.astype(str)

# Function to bound dimensions within the maximum/minimum dimensions
def bound(low, high, value):
  return max(low, min(high, value))

# Normalise the x/y coords and adjust to MCG dimensions
chains_processed['x_norm'] = chains_processed['x'] / (chains_processed['venueLength'] / 2) 
chains_processed['x_norm'] = chains_processed.x_norm.apply(lambda x: bound(-1,1,x)) * venueLength
chains_processed['y_norm'] = chains_processed['y'] / (chains_processed['venueWidth'] / 2) 
chains_processed['y_norm'] = chains_processed.y_norm.apply(lambda x: bound(-1,1,x)) * venueWidth

# Identify duplicate rows that show the player gaining possession and remove 
dupes = chains_processed.duplicated(subset=['season', 'roundNumber', 'homeTeam', 'period', 'periodSeconds', 'playerId', 'description'], keep='last')
chains_processed = chains_processed[~dupes]

# Create of column of instances of possession changes
chains_processed['possChng'] = chains_processed.groupby(game_identifiers + ['period'],  group_keys=False)['playingFor'].apply(lambda s: s.ne(s.shift(-1)) & ~s.shift(-1).isnull())
chains_processed['endOfQtr'] = chains_processed.periodSeconds > chains_processed.periodSeconds.shift(-1)
# Final possession in a chain
chains_processed['finalPos'] = chains_processed.possessionNum == chains_processed.groupby('chainId').possessionNum.transform(max)

# Record scores against kicks
chains_processed['points'] = np.select([chains_processed.description == "Goal", chains_processed.description == "Behind"], [6, 1], default=np.NaN)
chains_processed['points'] = chains_processed['points'].shift(-1)

# Reset goal positions
finCondList = [chains_processed.description == "Goal",
            chains_processed.behindInfo =='missLeft',
            chains_processed.behindInfo =='leftPost',
            chains_processed.behindInfo =='missRight',
            chains_processed.behindInfo =='touched',
            chains_processed.behindInfo =='rightPost']
## Y next pos
finychoiceList = [0,
              6.4,
              3.2,
              -6.4,
              0,
              -3.2]
## X next pos
finxchoiceList = [venueLength] * 6

## Record condition for debugging
nextCondChoice = ['G',
                 'ML',
                 'LP',
                 'MR',
                 'Touched',
                 'RP']

chains_processed = chains_processed.assign(x = np.select(finCondList, finxchoiceList, default=chains_processed.x),
                                           y = np.select(finCondList, finychoiceList, default=chains_processed.y),
                                           Cond = np.select(finCondList, nextCondChoice, default='Def'))

chains_processed['shotAtGoal'] = chains_processed.shotAtGoal.replace(np.NaN,False)

chains_processed['x'] = np.where(chains_processed.description == "Goal", venueWidth, chains_processed.x)
chains_processed['y'] = np.where(chains_processed.description == "Goal", 0, chains_processed.y)
# 2. shift next pos
chains_processed['x_next'] = chains_processed.groupby(['season', 'roundNumber', 'homeTeam', 'period'], as_index=False)['x'].shift(-1)
chains_processed['y_next'] = chains_processed.groupby(['season', 'roundNumber', 'homeTeam', 'period'], as_index=False)['y'].shift(-1)

# Reverse position for turnovers for distance calcs
finCondList = ((chains_processed.description == 'Spoil') & (~chains_processed.playingFor.shift(-1).isnull()) & \
    (~chains_processed.playingFor.shift(1).eq(chains_processed.playingFor.shift(-1)))) | \
    (chains_processed.possChng & chains_processed.finalPos & \
              (chains_processed.finalState.isin(["turnover", 'rushed'])) & \
              (chains_processed.description != 'Out On Full After Kick') & \
              (chains_processed.description.shift(-1) != 'Spoil'))

chains_processed = chains_processed.assign(x_next_actual = np.where(finCondList, -chains_processed.x_next, chains_processed.x_next),
                                           y_next_actual = np.where(finCondList, -chains_processed.y_next, chains_processed.y_next))

# 3. Set kickin as middle of the goal square - Update: removed 
# chains_processed['x'] = np.where(chains_processed.description.str.contains('Kickin') & chains_processed.description.shift(1).isin(['Goal', 'Behind']), -venueLength + 5, chains_processed.x)
# chains_processed['y'] = np.where(chains_processed.description.str.contains('Kickin') & chains_processed.description.shift(1).isin(['Goal', 'Behind']), 0, chains_processed.y)

# 4. Remove game events
game_events = ['Out On Full After Kick', 'Out On Full', 'Out of Bounds', 'Ball Up Call', 'Goal', 'Behind','Kick Inside 50 Result', 'OOF Kick In']

chains_processed = chains_processed[~chains_processed.description.isin(game_events)]


# 5. Calculate distance for QA
def calc_dist(x0, y0, x1, y1):
    x0 = np.array(x0, dtype=float)
    y0 = np.array(y0, dtype=float)
    x1 = np.array(x1, dtype=float)
    y1 = np.array(y1, dtype=float)
    return np.sqrt((x1-x0)**2 + (y1 - y0)**2)

chains_processed = chains_processed.assign(possDist = calc_dist(chains_processed.x, chains_processed.y, chains_processed.x_next_actual, chains_processed.y_next_actual))

chains_processed.to_pickle("data/chains_processed.pkl")
print("Processing time: ", round(time.time() - st, 2), " seconds")