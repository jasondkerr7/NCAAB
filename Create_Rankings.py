##################################################
###### Setup #####################################
##################################################

## -- Import Required Packages -- ##

import requests
from bs4 import BeautifulSoup
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
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
from datetime import datetime, date, timedelta
from datetime import time as datetime_time
from io import StringIO
import urllib
import gzip
import json
import lxml

# -- Functions -- #
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
barttorvik_headers = pd.read_csv('Static Files/Barttorvik Headers.csv')

# Team Help
temp = pd.read_csv('Static Files/Team Help.csv')
teamhelp = dict(zip(temp['College Poll Archive'],temp['Pandas']))

teamhelp_barttorvik = dict(zip(temp['Pandas'],temp['Bart Torvik']))
teamhelp_barttorvik.pop(np.nan, 'nope')

teamhelp_gl_dict = dict(zip(temp['BT Player Log'],temp['Pandas']))
teamhelp_gl_dict.pop(np.nan, 'nope')

teamhelp_scores_and_odds_dict = dict(zip(temp['Scores and Odds'],temp['Pandas']))
teamhelp_scores_and_odds_dict.pop(np.nan, 'nope')

temp_two = temp.loc[~temp['Odds Shark'].isna(),['Odds Shark','Pandas']].drop_duplicates().copy()
temp_two = temp.loc[~temp['Odds Shark Opponents'].isna(),['Odds Shark Opponents','Pandas']].drop_duplicates().copy()
teamhelp_os = dict(zip(temp_two['Odds Shark'],temp_two['Pandas']))
oppteamhelp_os = dict(zip(temp_two['Odds Shark Opponents'],temp_two['Pandas']))

# -- Rankings -- #
# Initialize
rankings = {}
stnum = 934

# Find Last Rankings
rank_season = datetime.now().year if datetime.now().month < 6 else datetime.now().year + 1
url = 'https://www.collegepollarchive.com/basketball/men/ap/seasons.cfm?seasonid='+str(rank_season)
page = requests.get(url)
soup = BeautifulSoup(page.text, 'lxml')
## get last value of Poll ID and add 1
endnum = int(soup.find('select',{'name':'appollid'}).find_all('option')[-1]['value']) + 1

for x in range(stnum, endnum):
    url = "https://www.collegepollarchive.com/mbasketball/ap/seasons.cfm?appollid="+str(x)+"#.Y329GOzMJ-X"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'lxml')

    # Test for Preseason/Final
    secondword = soup.find('h2').text.split(' ')[1]
    if secondword == 'Final':
        continue

    # Pull Table
    table = pd.read_html(StringIO(page.text))[7]
    table.drop('Rank.1',axis=1,inplace=True)
    table.rename(columns={'Team (FPV)':'Team'},inplace=True)
    tab = table[~table.Rank.isnull()].iloc[0:25].copy()
    tab['Rank'] = tab['Rank'].astype(int)
    tab['Team'] = [x.split('(')[0].strip() for x in tab.Team]

    # Pull Date
    if secondword == 'Preseason':
        yr = int(soup.find('h2').text.split(' ')[0].strip())
        date = datetime(year=yr-1, day=1, month=10)
    else:
        temp = soup.find('h2').text.split(' AP')[0]
        temp2 = temp.split(' ')[0]
        mnth = datetime.strptime(temp2, '%B').month
        dy = int(temp.split(' ')[1].split(',')[0])
        yr = int(temp.split(',')[1].strip())
        date = datetime(year=yr, day=dy, month=mnth)

    # Set Dictionary Table
    rankings[date] = tab

# Expand into Dataframe of all information (Rank, Team, Conference, Date)
counter = 0
for ky in rankings.keys():
    temp = rankings[ky]
    temp['Date'] = ky
    if counter == 0:
        allranks = temp
    else:
        allranks = pd.concat([allranks,temp],axis=0).reset_index(drop=True)
    counter += 1
allranks['Team'].replace(teamhelp, inplace=True)

##################################################
###### End Setup #################################
##################################################

# Test File Creation #
creation_name = 'Rankings - '+datetime.today().strftime('%m.%d.%y')
allranks.to_csv('saved_file.csv')

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv',
                'parents':['1DdTC37ao2EK23f-dnQ5Tj9EvgoS9BaIW']}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().create(body=file_metadata, media_body=media,
                              fields=returned_fields).execute()