##################################################
###### Setup #####################################
##################################################

## -- Import Required Packages -- ##

import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import pandas as pd
import re
import numpy as np
import time
import pickle
import glob
import os
import matplotlib.pyplot as plt
import statsmodels.formula.api as sm
import statsmodels.api as SM
import math
from statsmodels.stats.outliers_influence import variance_inflation_factor
from datetime import datetime, date, timedelta
from datetime import time as datetime_time
from io import StringIO
import urllib
import gzip
import json
import lxml

# Helpful Functions
all_stats_col = ['MP', 'ORTG', 'Usage', 'eFG', 'TS_per', 'ORB_per', 'DRB_per', 'AST_per', 'TO_per', 
                 'DunksM','DunksAtt', 'AtRimM', 'AtRimAtt', 'MidM', 'MidAtt', '2PM', '2PA', '3PM',
                   '3PA', 'FTM', 'FTA', 'OBPM', 'DBPM', 'BPM_net', 'PTS', 'ORB', 'DRB',
                   'AST', 'TOV', 'STL', 'BLK', 'STL_per', 'BLK_per', 'PF', 'POSS', 'BPM']

total_stats_col = ['MP','DunksM','DunksAtt', 'AtRimM', 'AtRimAtt', 'MidM', 'MidAtt', 
                  '2PM', '2PA', '3PM','3PA', 'FGM', 'FGA', 'FTM', 'FTA', 'PTS',
                  'ORB', 'DRB','TRB','AST', 'TOV', 'STL', 'BLK', 'PF', 'POSS', 'OffGameScore']

all_agg_stats = total_stats_col + ['AMP', 'StarScore', 'Avg Height','Avg Experience']

rate_stats_col = ['ORTG','Usage', 'eFG', 'TS_per', 'ORB_per', 'DRB_per', 'AST_per',
                     'TO_per', 'OBPM', 'DBPM', 'BPM_net', 'STL_per', 'BLK_per', 'BPM']

player_info_col = ['Player','Height', 'Class', 'PID']

game_info_col = ['Team', 'Opp', 'Date', 'ResultDummy', 'Season']

# -- GOOGLE CONNECTION -- #
# Prepare auth json for google connection
cred_json = os.environ['SERVICE_ACCOUNT_CREDENTIALS_JSON']
s_char = cred_json.index('~~~')
e_char = cred_json.index('%%%')
service_account_cred = eval(cred_json[s_char+3:e_char])

# Connect to the google service account
scope = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_info(
                              info=service_account_cred, 
                              scopes=scope)
ggl_drive = build('drive', 'v3', credentials=credentials)

# -- Read Files -- #
# Bart Torvik Headers
barttorvik_headers = pd.read_csv('https://docs.google.com/spreadsheets/d/1_alO289CpDPCFemFrC5D-sxL8WJqWj57Krny06a4K6M/export?format=csv&gid=0')

# Team Help
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1D9eKEUM_B3gXs3ukfj0_704YzG3Iw4u2_ATdj21JvGE/export?format=csv&gid=0')

# Create from files
teamhelp = dict(zip(temp['College Poll Archive'],temp['Pandas']))

teamhelp_barttorvik = dict(zip(temp['Pandas'],temp['Bart Torvik']))
teamhelp_barttorvik.pop(np.nan, 'nope')

teamhelp_gl_dict = dict(zip(temp['BT Player Log'],temp['Pandas']))
teamhelp_gl_dict.pop(np.nan, 'nope')

teamhelp_scores_and_odds_dict = dict(zip(temp['Scores and Odds'],temp['Pandas']))
teamhelp_scores_and_odds_dict.pop(np.nan, 'nope')

teamhelp_os = dict(zip(temp['Odds Shark'],temp['Pandas']))
teamhelp_os.pop(np.nan, 'nope')

# - Player Logs - #
# Data Pull

ncaa_player_wip = pd.DataFrame()

for yr in range(2021, 2025):

    testfile = urllib.request.URLopener()
    testfile.retrieve("https://barttorvik.com/"+str(yr)+"_all_advgames.json.gz", "file.gz")
    with gzip.GzipFile("file.gz", 'r') as fin:
        json_bytes = fin.read()
    json_str = json_bytes.decode('utf-8')
    test_data = json.loads(json_str)

    data = pd.DataFrame(test_data)
    data.columns = list(barttorvik_headers['Column Names'])
    data.drop('XXX',axis=1,inplace=True)
    
    ncaa_player_wip = pd.concat([ncaa_player_wip,data], ignore_index=True)

# Process Columns
ncaa_player_wip['Team'].replace(teamhelp_gl_dict, inplace=True)
ncaa_player_wip['Opp'].replace(teamhelp_gl_dict, inplace=True)
ncaa_player_wip['Season'] = ncaa_player_wip['Season']
ncaa_player_wip['Date'] = pd.to_datetime(ncaa_player_wip['DateNum'])
ncaa_player_wip.drop('DateNum', axis=1, inplace=True)

# Calculated Columns
ncaa_player_wip['FGM'] = ncaa_player_wip['2PM'] + ncaa_player_wip['3PM']
ncaa_player_wip['FGA'] = ncaa_player_wip['2PA'] + ncaa_player_wip['3PA']
ncaa_player_wip['TRB'] = ncaa_player_wip['ORB'] + ncaa_player_wip['DRB']
ncaa_player_wip['OffGameScore'] = ncaa_player_wip['PTS'] + 0.4*ncaa_player_wip['FGM'] - 0.7*ncaa_player_wip['FGA']\
                                - 0.4*(ncaa_player_wip['FTA'] - ncaa_player_wip['FTM'])\
                                + 0.7*ncaa_player_wip['ORB'] + 0.3*ncaa_player_wip['DRB']\
                                + 0.7*ncaa_player_wip['AST'] - ncaa_player_wip['TOV']

# Player Aggregated Stats #

# Create one DF for players and one for Games
temp_player_list = ncaa_player_wip[player_info_col+['Team','Season']].copy().drop_duplicates()
temp_game_list = ncaa_player_wip[game_info_col].copy().drop_duplicates()
# Merge them so that each player has a row for games regardless of if they played
temp = pd.merge(temp_game_list, temp_player_list, on=['Season','Team'], how='left')
# Merge with full dataset to get stats
new = pd.merge(temp, ncaa_player_wip, on=list(temp.columns), how='left')

# Fix Columns
## Create Temp variable to determine GP
new['tempGP'] = (~new['PTS'].isna())*1
## Sort for Date so that cumulative stats are correct
new.sort_values('Date', inplace=True)
## Fill nan values with 0
new.fillna(0, inplace=True)

# Establish new DF to add cumlative stats
player_agg_stats = new[['Player','Team','Season','Date']].copy()
# Loop through Stats to Aggregate
player_agg_stats['GP'] = (new.groupby(['Season','Player'])['tempGP'].cumsum()).astype(int) - 1
for col in total_stats_col:
    player_agg_stats[col] = ((new.groupby(['Season','Player'])[col].cumsum() - new[col])/(player_agg_stats['GP'])).round(2)
    player_agg_stats[col].fillna(0,inplace=True)
# Total OffGameScore
player_agg_stats['TotalOffGameScore'] = (new.groupby(['Season','Player'])[col].cumsum()).round(2)
player_agg_stats['TotalOffGameScore'].fillna(0,inplace=True)
# Reset Index
player_agg_stats.reset_index(drop=True, inplace=True)
# StarRank Stat generation
player_agg_stats['StarRank'] = player_agg_stats.groupby(['Team','Date'])['TotalOffGameScore'].\
                                            rank(method = 'first',ascending=False)

# Team Season Stats #

# Generate Team Game Logs
team_game_logs = ncaa_player_wip.groupby(['Team','Date','Season'])[total_stats_col].sum().reset_index()
# Aggregate for Season Stats
temp = team_game_logs.sort_values('Date').copy()
# Loop through Stats to Aggregate
temp['GP'] = (temp.groupby(['Season','Team'])['Team'].cumcount()).astype(int)
# Establish new DF to add cumlative stats
team_agg_stats = temp[['Team','Season','Date']].copy()
for col in total_stats_col:
    team_agg_stats[col] = ((temp.groupby(['Season','Team'])[col].cumsum() - temp[col])/temp['GP']).round(2)
    team_agg_stats[col].fillna(0,inplace=True)


# Opp Season Stats #

# Generate Team Game Logs
team_def_game_logs = ncaa_player_wip.groupby(['Opp','Date','Season'])[total_stats_col].sum().reset_index()

# Aggregate for Season Stats
temp = team_def_game_logs.sort_values('Date').copy()
# Loop through Stats to Aggregate
temp['GP'] = (temp.groupby(['Season','Opp'])['Opp'].cumcount()).astype(int)
# Establish new DF to add cumlative stats
team_def_agg_stats = temp[['Opp','Season','Date']].copy()
for col in total_stats_col:
    team_def_agg_stats[col] = ((temp.groupby(['Season','Opp'])[col].cumsum() - temp[col])/temp['GP']).round(2)
    team_def_agg_stats[col].fillna(0,inplace=True)
# Rename to Def
team_def_agg_stats.columns = ['Def'+col if col in total_stats_col else col for col in team_def_agg_stats.columns]
team_def_agg_stats.rename(columns={'Opp':'Team'},inplace=True)

# Merge Off and Def Stats #
team_agg_stats_v1 = pd.merge(team_game_logs, team_def_agg_stats, on=['Team','Season','Date'], how='left')

# AMP #

# Copy Player Agg Stats
amp_temp = player_agg_stats.copy()
# Create Total Minutes Played this season stat
amp_temp['Total Minutes'] = amp_temp['GP'] * amp_temp['MP']
# Total Minutes Played by Team for Relevant Players by Day
amp_temp_agg_ex = amp_temp[amp_temp['MP'] > 10].groupby(['Date','Team','Season'])['Total Minutes'].sum()\
                                                .reset_index().rename(columns={'Total Minutes':'ExTM'})

# Copy Player Game Logs with Total Minutes and Avg Minutes
amp_temp_players = pd.merge(ncaa_player_wip, amp_temp[['Date','Player','Team','Total Minutes','MP']].rename(columns={'MP':'AvgMP'}), 
                            on=['Date','Player','Team'], how='left')
# Number of Available Minutes by Team for Relevant Players by Day
amp_temp_agg_actual = amp_temp_players[amp_temp_players['AvgMP'] > 10].groupby(['Date','Team','Season'])['Total Minutes'].sum()\
                                                                        .reset_index().rename(columns={'Total Minutes':'ActTM'})
# Generate AMP stat
temp_amp = pd.merge(amp_temp_agg_ex, amp_temp_agg_actual, on=['Date','Team','Season'], how='left')
temp_amp['AMP'] = temp_amp['ActTM']/temp_amp['ExTM']
# Remove Intermediary Stats
temp_amp.drop(['ExTM','ActTM'],axis=1, inplace=True)

# Merge with Total Stats #
team_agg_stats_v2 = pd.merge(team_agg_stats_v1, temp_amp, on=['Date', 'Team', 'Season'], how='left')

# Best Player #

temp = player_agg_stats[(player_agg_stats['StarRank'] == 1)].drop_duplicates(['Date','Team'])[['Date','Team','OffGameScore']].rename(columns={'OffGameScore':'StarScore'})
team_agg_stats_v3 = pd.merge(team_agg_stats_v2, temp, on=['Date', 'Team'], how='left')

# Weighted Height and Experience

# Database for Descriptors
desc_stats = ncaa_player_wip[['Season','Player','Team','Class','Height']].drop_duplicates()
# Copy Player Agg Stats
amp_temp = pd.merge(player_agg_stats, desc_stats, on = ['Season','Player','Team'], how='left')
# Create Numerical Class
amp_temp['ClassNum'] = (amp_temp['Class'] == 'Fr')*1 +\
                        (amp_temp['Class'] == 'So')*2 +\
                        (amp_temp['Class'] == 'Jr')*3 +\
                        (amp_temp['Class'] == 'Sr')*4
# Create Total Minutes Played this season stat
amp_temp['Total Minutes'] = amp_temp['GP'] * amp_temp['MP']
amp_temp['Total Height'] = amp_temp['Total Minutes'] * amp_temp['Height']
amp_temp['Total Experience'] = amp_temp['Total Minutes'] * amp_temp['ClassNum']
# Sum by Team
agged = amp_temp.groupby(['Team','Season','Date'])[['Total Minutes','Total Height','Total Experience']].sum().reset_index()
# Divide by Minutes for Weighted Averages
agged['Avg Height'] = (agged['Total Height']/agged['Total Minutes']).round(2)
agged['Avg Experience'] = (agged['Total Experience']/agged['Total Minutes']).round(2)

# Merge #
team_agg_stats = pd.merge(team_agg_stats_v3, agged[['Date', 'Team','Avg Height','Avg Experience']], on=['Date', 'Team'], how='left')

##################################################
###### End Setup #################################
##################################################

# Test File Creation #
creation_name = 'Player Stats through 2024'
allranks.to_csv('saved_file.csv',index=False)

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().update(fileId='17p3ZBuoFeYSj4E64pRuLUJBL7LpSvfin',
                                body=file_metadata, 
                                media_body=media,
                              fields=returned_fields).execute()
