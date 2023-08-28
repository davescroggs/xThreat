
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import math
import numpy as np
import time
from plot_field import generate_afl_oval, plot_events
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 50)

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

# Create ID for chains and possession for easy lookup
chains_raw['chainId'] = chains_raw.season.astype(str) + "_" + chains_raw.roundNumber.astype(str) + "_" + chains_raw.homeTeam.apply(lambda x: x.replace(" ", "_")) + "_C" + chains_raw.chainNumber.astype(str)

# Remove Kick Into F50 type results
chains_processed = chains_raw[~chains_raw.description.isin(['Kick Into F50','Kick Inside 50 Result', 'Inside 50', 'Shot At Goal', 'Centre Bounce', 'Mark Fumbled', 'Mark Dropped', 'Tackle','Credit','No Pressure Error'])].copy()
chains_processed['date'] = pd.to_datetime(chains_processed['date'])
chains_processed = chains_processed.sort_values(by=['season', 'roundNumber', 'date', 'homeTeam', 'displayOrder'])
# Create number for each possession
chains_processed['possessionNum'] = chains_processed.groupby(["roundNumber", "homeTeam", "period", "chainNumber"],  group_keys=False)['playerId'].apply(lambda s: s.ne(s.shift()).cumsum())
chains_processed['possessionId'] = chains_processed['chainId'] + "_P" + chains_processed.possessionNum.astype(str)

chains_processed['x_norm'] = chains_processed['x'] / (chains_processed['venueLength'] / 2)
## The average ratio of width/length in the league is about 0.78 or so, round up to 0.8
chains_processed['y_norm'] = chains_processed['y'] / (chains_processed['venueWidth'] / 2) * 0.8

# Fill missing values for context rows
chains_processed['playerId'] = chains_processed.groupby(['chainId'])['playerId'].transform(lambda s: s.ffill())
chains_processed['playingFor'] = chains_processed.groupby(['chainId'])['playingFor'].transform(lambda s: s.ffill())

# Indicate which chains have ended with a shot at goal
# chains_processed['shotAtGoalChain'] = chains_processed.groupby('chainId', group_keys=False)['shotAtGoal'].transform(lambda s: any(s))

# Identify duplicate rows that show the player gaining possession and remove 
dupes = chains_processed.duplicated(subset=['season', 'roundNumber', 'homeTeam', 'period', 'periodSeconds', 'playerId', 'description'], keep='last')
chains_processed = chains_processed[~dupes]

# Create of column of instances of possession changes
chains_processed['possChng'] = chains_processed.groupby(game_identifiers + ['period'],  group_keys=False)['playingFor'].apply(lambda s: s.ne(s.shift(-1)) & ~s.shift(-1).isnull())
chains_processed['endOfQtr'] = chains_processed.periodSeconds > chains_processed.periodSeconds.shift(-1)
# Final possession in a chain
chains_processed['finalPos'] = chains_processed.possessionNum == chains_processed.groupby('chainId').possessionNum.transform(max)
# Create 
player_info = chains_processed[['playerId', 'firstName', 'surname', 'playingFor']].drop_duplicates().dropna()
player_info['full_name'] = chains_processed['firstName'] + " " + chains_processed['surname']
player_info.drop(['firstName', 'surname'], axis=1, inplace=True)
player_info.set_index('playerId', inplace=True)

game_info = chains_processed[['season', 'roundNumber', 'homeTeam', 'awayTeam']].drop_duplicates()
game_info = game_info.assign(game_title = 'Round ' + game_info.roundNumber.map(str) + ' ' + game_info.season.map(str) + ' ' + game_info.homeTeam + ' vs. ' + game_info.awayTeam)

print('Step 1 complete: time = ', time.time() - st, ' seconds')
#### SUMMARISE POSSESSIONS ####
print("Summarising possessions")
## Create possession summary

def paste(outcm_strings):
    return ', '.join(outcm_strings)

def calc_dist(x0, y0, x1, y1):
    x0 = np.array(x0, dtype=float)
    y0 = np.array(y0, dtype=float)
    x1 = np.array(x1, dtype=float)
    y1 = np.array(y1, dtype=float)
    return np.sqrt((x1-x0)**2 + (y1 - y0)**2)

def check_final_disposal(x):
    disposal_types = ['Kick', 'Handball', 'Ground Kick', 'OOF Kick In', 'Kickin short',
                     'Kickin long', 'Kick In Ineffective', 'Kick Long To Adv.', 'Kick In Clanger']
    return len(x) - np.argmax(np.flip(x.isin(disposal_types).values)) - 1

possession_summary = (chains_processed
                        .groupby(['season', 'roundNumber', 'homeTeam', 'period', 'chainId',  'possessionNum', 'possessionId', 'playerId','playingFor', 'venueName', 'venueLength', 'venueWidth'])
                        .agg(
                            n=('x', 'size'),
                            outcomes=('description', lambda outcm_strings: ', '.join(outcm_strings)),
                            xInitialPoss = ('x', 'first'),
                            yInitialPoss = ('y', 'first'),
                            xFinalPoss = ('x', 'last'),
                            yFinalPoss = ('y', 'last'),
                            posStart = ('periodSeconds', 'first'),
                            posEnd = ('periodSeconds', 'last'),
                            shotAtGoal = ('shotAtGoal', 'any'),
                            bounces = ('description', lambda x: sum(x == "Bounce")),
                            goals = ('description', lambda x: sum(x == "Goal")),
                            behind = ('description', lambda x: sum(x == "Behind")),
                            behindDesc = ('behindInfo', lambda x: next((item for item in x if item is not np.NaN), None)),
                            possChng = ('possChng', 'any'),
                            finalPos = ('finalPos', 'any'),
                            disposal=('disposal', lambda x: sum(x == "effective")),
                            disposalList = ('description', lambda x: list(x)),
                            xList = ('x', lambda x: list(x)),
                            yList = ('y', lambda x: list(x)),
                            finalDisposal = ('description', check_final_disposal),
                            chainInitialState = ('initialState', 'first'),
                            chainFinalState = ('finalState', 'first'),
                            initialState = ('description', 'first'),
                            finalState = ('description', 'last'),
                            endOfQtr = ('endOfQtr', 'any'))).reset_index()

print('Step 2 complete: time = ', time.time() - st, ' seconds')
# Get the start position of the next possession as the 
possession_summary['xNextPoss'] = possession_summary.groupby(['season', 'roundNumber', 'homeTeam', 'period'], as_index=False)['xInitialPoss'].shift(-1)
possession_summary['yNextPoss'] = possession_summary.groupby(['season', 'roundNumber', 'homeTeam', 'period'], as_index=False)['yInitialPoss'].shift(-1)

# Remove spoils from final poss
# Update final disposal characteristics when not the final event
for index, row in possession_summary.iterrows():
    if row.finalDisposal + 1 < row.n:
        possession_summary.loc[index, 'finalState'] = row.disposalList[row.finalDisposal]
        possession_summary.loc[index, 'xFinalPoss'] = row.xList[row.finalDisposal]
        possession_summary.loc[index, 'yFinalPoss'] = row.yList[row.finalDisposal]
        possession_summary.loc[index, 'xNextPoss'] = row.xList[-1]
        possession_summary.loc[index, 'yNextPoss'] = row.yList[-1]

possession_summary = possession_summary[~(possession_summary.finalPos & (possession_summary.finalState == "Spoil"))]

possession_summary = possession_summary.assign(xInitialPoss = np.where(possession_summary.initialState == "Kickin play on",-(possession_summary.venueLength/2-8.5), possession_summary.xInitialPoss),
                                               yInitialPoss = np.where(possession_summary.initialState == "Kickin play on",0 , possession_summary.yInitialPoss))

# Adjust initial position for kickins

initCondList = [possession_summary.initialState.str.contains('Kickin')]
initxchoiceList = [-(possession_summary.venueLength/2 - 9)]
initychoiceList = [0]
initChoiceCond = ["KI"]

# Adjust final position when kicking a goal/behind
finCondList = [possession_summary.endOfQtr,
            possession_summary.finalPos & (possession_summary.chainFinalState.isin(['ballUpCall','outOfBounds'])),
            possession_summary.finalPos & (possession_summary.chainFinalState.isin(["turnover", 'rushed']) & ~possession_summary.outcomes.str.contains('Out On Full After Kick')),
            possession_summary.goals > 0,
            possession_summary.behindDesc=='missLeft',
            possession_summary.behindDesc=='leftPost',
            possession_summary.behindDesc=='missRight',
            possession_summary.behindDesc=='touched',
            possession_summary.behindDesc=='rightPost']
## Y next pos
finychoiceList = [np.NaN,
              possession_summary.yFinalPoss,
              -possession_summary.yNextPoss,
              0,
              6.4,
              3.2,
              -6.4,
              0,
              -3.2]
## X next pos
finxchoiceList = [np.NaN,
              possession_summary.xFinalPoss,
              -possession_summary.xNextPoss] + \
              [possession_summary.venueLength/2] * 6
## Record condition for debugging
nextCondChoice = ['EOQ',
                 'DISCONT',
                 'TO',
                 'G',
                 'ML',
                 'LP',
                 'MR',
                 'Touched',
                 'RP']

possession_summary = possession_summary.assign(xInitialPoss = np.select(initCondList, initxchoiceList, default=possession_summary.xInitialPoss),
                                               yInitialPoss = np.select(initCondList, initychoiceList, default=possession_summary.yInitialPoss),
                                               initialPossCond = np.select(initCondList, initChoiceCond, default='Def'),
                                               xNextPoss = np.select(finCondList, finxchoiceList, default=possession_summary.xNextPoss),
                                               yNextPoss = np.select(finCondList, finychoiceList, default=possession_summary.yNextPoss),
                                               nextPosCond = np.select(finCondList, nextCondChoice, default='Def'))

possession_summary = possession_summary.assign(distanceFromPoss = calc_dist(possession_summary.xInitialPoss, possession_summary.yInitialPoss, possession_summary.xFinalPoss, possession_summary.yFinalPoss),
                        distanceDisposal = calc_dist(possession_summary.xFinalPoss, possession_summary.yFinalPoss, possession_summary.xInitialPoss.shift(-1), possession_summary.yInitialPoss.shift(-1), ),
                        initialDistFromGoal = calc_dist(possession_summary.xInitialPoss, possession_summary.yInitialPoss, possession_summary.venueLength/2, 0),
                        finalDistFromGoal = calc_dist(possession_summary.xFinalPoss, possession_summary.yFinalPoss, possession_summary.venueLength/2, 0),
                        disposalRecipient = np.where(\
                            # Disposal recipient when there is a disposal and the team doesn't loose possession
                            (~possession_summary.possChng & (possession_summary.disposal > 0)) | \
                            # Its not the end of quarter
                            ~possession_summary.endOfQtr | \
                            # It's not a discontinuity event
                            possession_summary.finalPos & (possession_summary.chainFinalState.isin(['ballUpCall','outOfBounds'])), \
                            possession_summary.playerId.shift(-1),np.NaN))

possession_summary['deltaDistFromGoal'] = possession_summary.finalDistFromGoal - possession_summary.initialDistFromGoal
possession_summary.drop(['venueLength','venueWidth'], axis=1, inplace=True)

possession_summary.to_pickle("data/possessions_processed.pkl")
chains_raw.to_pickle("data/chains_raw.pkl")
chains_processed.to_pickle("data/chains_processed.pkl")

# get the end time
et = time.time()

# get the execution time
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')
# %%
