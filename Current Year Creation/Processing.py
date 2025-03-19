##################################################
###### Setup #####################################
##################################################

## -- Import Required Packages -- ##

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import smtplib
from bs4.element import Comment
import re
import requests
from pydomo import Domo
import openpyxl
import datetime
from datetime import datetime, date, timedelta
from datetime import time as datetime_time
import pandas as pd
import pickle
import time
import numpy as np
from io import StringIO
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.api as SM
from statsmodels.stats.outliers_influence import variance_inflation_factor
from calendar import monthrange
from bs4 import BeautifulSoup
import math
import censusgeocode as cg
import html5lib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import glob
import urllib
import gzip
import json
import lxml
import sys

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
# Creation Files
odds = pd.read_csv('https://docs.google.com/uc?id=1d6slsiCtovW0zJgG5eqrgAFzJEW17r7K').rename(columns={'Opponent':'Opp'})
rankings = pd.read_csv('https://docs.google.com/uc?id=1gRwZVVxARkDCWkR9hXMopW3vOF46aunn')
conference_reference = pd.read_csv('https://docs.google.com/uc?id=1ewDetzYCoyS5hnVBMjXaiTSM_fLop3wy')[['Team','Conf','Season']]
team_agg_stats = pd.read_csv('https://docs.google.com/uc?id=1yYXa7aWdXYYE2D6vdbElkThdOlIgM5zz')
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1GAILK1kQ4BPGvIs3E0a-M83yeCYofiQfSbFpp4NNnHI/export?format=csv&gid=0')
NattyDates = temp.loc[~temp['Season'].isna(),['Season','StartNatty']]
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1WgzvFxF8Ze3aQ5smjSMvAedVlbhkqh97sP7lvXCmSv8/export?format=csv&gid=0')
marchmadness = temp[['Season','Team','Seed','Berth']].rename(columns={'Seed':'TourneySeed',
                                                                   'Berth':'TourneyBerth'}).copy()
oppmarchmadness = temp[['Season','Team','Seed','Berth']].rename(columns={'Team':'Opp',
                                                                    'Seed':'OppTourneySeed',
                                                                   'Berth':'OppTourneyBerth'}).copy()
# Team Help
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1D9eKEUM_B3gXs3ukfj0_704YzG3Iw4u2_ATdj21JvGE/export?format=csv&gid=0')
teamhelp = dict(zip(temp['Odds Shark Opponents'],temp['Pandas']))

############
# Read in Upcoming Games
############
# Setup Connection
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
user_agent = 'Chrome/60.0.3112.50'
options.add_argument(f'user-agent={user_agent}')
driver = webdriver.Chrome(service=service, options=options)

for xy in range(0,5):
    try:
        # Access Website
        soup = BeautifulSoup(requests.get('https://www.oddsshark.com/ncaab/odds').content)

        # Initialize
        teams = []
        opps = []
        spreads = []
        mls = []
        totals = []
        tomorrow = (datetime.today() + timedelta(days=1)).strftime('%m/%d/%y')

        for gm in soup.select('div[class*="odds--group__event-container basketball"]'):
            # First Row
            teams.append(gm.select('div[class="participant-name"]')[0]['title'])
            opps.append(gm.select('div[class="participant-name"]')[1]['title'])
            fr = gm.select('div[class="odds--group__event-book book-10039"]')[0].select('div[class="first-row"]')[0]
            spreads.append(fr.select('div[class="odds-spread"]')[0].select('div')[0].text)
            mls.append(fr.select('div[class="odds-moneyline hide"]')[0].select('div')[1].text)
            totals.append(fr.select('div[class="odds-total hide"]')[0].select('div')[0].text[2:])
            
            # Second Row
            teams.append(gm.select('div[class="participant-name"]')[1]['title'])
            opps.append(gm.select('div[class="participant-name"]')[0]['title'])
            fr = gm.select('div[class="odds--group__event-book book-10039"]')[0].select('div[class="second-row"]')[0]
            spreads.append(fr.select('div[class="odds-spread"]')[0].select('div')[0].text)
            mls.append(fr.select('div[class="odds-moneyline hide"]')[0].select('div')[1].text)
            totals.append(fr.select('div[class="odds-total hide"]')[0].select('div')[0].text[2:])
            break
    except:
        time.sleep(2)
        print('Attempt #',xy)
        continue
    
odds_shark_games = pd.DataFrame({'Date':tomorrow,
                                 'Team':teams,
                                 'Location':'Neutral',
                                 'Opp':opps,
                                 'Spread':spreads,
                                 'ML':mls,
                                'Total':totals,
                                })
for col in ['Spread','ML','Total']:
    odds_shark_games[col] = pd.to_numeric(odds_shark_games[col], errors='coerce')
odds_shark_games['Date'] = pd.to_datetime(odds_shark_games['Date'])    
odds_shark_games = odds_shark_games[~odds_shark_games['Spread'].isna()]
# Fix team names
odds_shark_games['Team'].replace(teamhelp,inplace=True)
odds_shark_games['Opponent'].replace(teamhelp,inplace=True)
print('odds_shark_games Length:',len(odds_shark_games))

### Create from files
opp_conference_reference = conference_reference.rename(columns={'Team':'Opp',
                                                       'Conf':'OppConf'})

### Pre-Processing
odds = pd.concat([odds,odds_shark_games],ignore_index=True)
rankings['Date'] = pd.to_datetime(rankings['Date'])
odds['Date'] = pd.to_datetime(odds['Date'])
odds['Season'] = (odds['Date'].dt.month > 6)*1 + odds['Date'].dt.year
odds = odds.sort_values('Date', ascending=True)
team_agg_stats['Date'] = pd.to_datetime(team_agg_stats['Date'])
print('odds after merge Length:',len(odds))

##################################################
###### Processing ################################
##################################################

# -- Combine Odds with Conference -- #
temp = pd.merge(odds, conference_reference, how='left', on=['Team','Season'])
odds = pd.merge(temp, opp_conference_reference, how='left', on=['Opp','Season'])

# -- Combine Odds with Rankings -- #
# List of Dates
rnkeys = pd.unique(rankings['Date'])

# Create Dictionary to turn Dates into Dates of AP Rankings
### Initialize
date_ref_dict = {}
every_date = pd.unique(odds['Date'])
for d in every_date:
    daat = pd.to_datetime(d)
    date_ref_dict[d] = min(rnkeys, key=lambda x: (x>daat, abs(x-daat)))

# Duplicate Date column and then map it using the dictionary
odds['DateRef'] = odds['Date']
odds['DateRef'] = odds['DateRef'].replace(date_ref_dict)

# Create Reference DFs
rankings_ref = rankings[['Date','Team','Rank']].rename(columns={'Date':'DateRef'}).copy()
opp_rankings_ref = rankings_ref.rename(columns={'Team':'Opp',
                                                'Rank':'OppRank'})

# Merge
temp = pd.merge(odds, rankings_ref, on=['Team','DateRef'], how='left')
oddsv2 = pd.merge(temp, opp_rankings_ref, on=['Opp','DateRef'], how='left')
oddsv2 = oddsv2.drop_duplicates().reset_index(drop=True)

# -------------------------- #
# -- Create New Variables -- #
# -------------------------- #

# -- Profits --
oddsv2['ATSProfit'] = (oddsv2['ATSMargin'] > 0)*100 + (oddsv2['ATSMargin'] < 0)*-110
oddsv2['MLProfit'] = ((oddsv2['ML'] < 0)*(oddsv2['MOV'] > 0)*100 + # Favorite Winner
                      (oddsv2['ML'] > 0)*(oddsv2['MOV'] > 0)*(oddsv2['ML']) + # Underdog Winner
                      (oddsv2['ML'] < 0)*(oddsv2['MOV'] < 0)*(oddsv2['ML']) + # Favorite Loser
                      (oddsv2['ML'] > 0)*(oddsv2['MOV'] < 0)*-100 # Underdog Loser
                     )

#  -- Game Number --
oddsv2 = oddsv2.sort_values('Date', ascending=True)
oddsv2['G'] = oddsv2.groupby(['Team','Season'])['Date'].rank(method = 'first',ascending=True)
oddsv2['OppG'] = oddsv2.groupby(['Opp','Season'])['Date'].rank(method = 'first',ascending=True)
# Reset Memory
del odds

# -- Previous Game Stats --
# Initialize
pg_key_cols = ['Team','Season','G']
pg_stats_cols = ['MOV','Spread','ATSMargin','Location']
opp_pg_key_cols = ['Opp','Season','OppG']
### Create Reference Dictionary
previous_game_ref = oddsv2[pg_key_cols + pg_stats_cols].copy()
### Adjust Column Names
pg_new_cols = ['pg' +  x if x not in pg_key_cols else x for x in previous_game_ref.columns]
previous_game_ref.columns = pg_new_cols
### Modify G column for combining
previous_game_ref['G'] = previous_game_ref['G'] + 1
### Create Opp DF
opp_previous_game_ref = previous_game_ref.copy()
opp_previous_game_ref.columns = opp_pg_key_cols + ['Opppg' + y for y in pg_stats_cols]
# Merge
temp = pd.merge(oddsv2, previous_game_ref, on=pg_key_cols, how='left')
oddsv3 = pd.merge(temp, opp_previous_game_ref, on=opp_pg_key_cols, how='left')
# Reset Memory
del oddsv2

# -- Win/Loss & ATS --
# Basic Result Dummy's
oddsv3['ResultDummy'] = (oddsv3['MOV'] > 0)*1
oddsv3['SpreadResultDummy'] = np.where(oddsv3['ATSMargin'] == 0, 'Push',
                                         np.where(oddsv3['ATSMargin'] > 0, 'Cover', 'Loss'))

# Establish Temporary Variables
## These variables cateogrize the individual result in a game
### Full
oddsv3['tempW'] = (oddsv3['ResultDummy'] == 1)*1
oddsv3['tempL'] = (oddsv3['ResultDummy'] == 0)*1
oddsv3['tempATSW'] = (oddsv3['SpreadResultDummy'] == 'Cover')*1
oddsv3['tempATSL'] = (oddsv3['SpreadResultDummy'] == 'Loss')*1
oddsv3['tempATSP'] = (oddsv3['SpreadResultDummy'] == 'Push')*1
### Home
oddsv3['tempHomeW'] = (oddsv3['Location'] == 'Home')*(oddsv3['ResultDummy'] == 1)*1
oddsv3['tempHomeL'] = (oddsv3['Location'] == 'Home')*(oddsv3['ResultDummy'] == 0)*1
oddsv3['tempHomeATSW'] = (oddsv3['Location'] == 'Home')*(oddsv3['SpreadResultDummy'] == 'Cover')*1
oddsv3['tempHomeATSL'] = (oddsv3['Location'] == 'Home')*(oddsv3['SpreadResultDummy'] == 'Loss')*1
oddsv3['tempHomeATSP'] = (oddsv3['Location'] == 'Home')*(oddsv3['SpreadResultDummy'] == 'Push')*1
### Away
oddsv3['tempAwayW'] = (oddsv3['Location'] == 'Away')*(oddsv3['ResultDummy'] == 1)*1
oddsv3['tempAwayL'] = (oddsv3['Location'] == 'Away')*(oddsv3['ResultDummy'] == 0)*1
oddsv3['tempAwayATSW'] = (oddsv3['Location'] == 'Away')*(oddsv3['SpreadResultDummy'] == 'Cover')*1
oddsv3['tempAwayATSL'] = (oddsv3['Location'] == 'Away')*(oddsv3['SpreadResultDummy'] == 'Loss')*1
oddsv3['tempAwayATSP'] = (oddsv3['Location'] == 'Away')*(oddsv3['SpreadResultDummy'] == 'Push')*1
### Conf
oddsv3['tempConfW'] = (oddsv3['Conf'] == oddsv3['OppConf'])*(oddsv3['ResultDummy'] == 1)*1
oddsv3['tempConfL'] = (oddsv3['Conf'] == oddsv3['OppConf'])*(oddsv3['ResultDummy'] == 0)*1
oddsv3['tempConfATSW'] = (oddsv3['Conf'] == oddsv3['OppConf'])*(oddsv3['SpreadResultDummy'] == 'Cover')*1
oddsv3['tempConfATSL'] = (oddsv3['Conf'] == oddsv3['OppConf'])*(oddsv3['SpreadResultDummy'] == 'Loss')*1
oddsv3['tempConfATSP'] = (oddsv3['Conf'] == oddsv3['OppConf'])*(oddsv3['SpreadResultDummy'] == 'Push')*1

#### Sort Values ####
oddsv3 = oddsv3.sort_values('Date')

# Cumulatively Sum the Temporary Variables
## The cumulative sum will include the current game so that must be subtracted
### Loop
for sitch in ['','Home','Away','Conf']:
    for stat in ['W','L','ATSW','ATSL','ATSP']:
        oddsv3[sitch+stat] = oddsv3.groupby(['Season','Team'])['temp'+sitch+stat].cumsum() -\
                                oddsv3['temp'+sitch+stat]
        oddsv3 = oddsv3.drop('temp'+sitch+stat, axis=1)

# Add Result Percentages        
oddsv3['WLpct'] = oddsv3['W']/(oddsv3['W'] + oddsv3['L'])
oddsv3['HomeWLpct'] = oddsv3['HomeW']/(oddsv3['HomeW'] + oddsv3['HomeL'])
oddsv3['AwayWLpct'] = oddsv3['AwayW']/(oddsv3['AwayW'] + oddsv3['AwayL'])
oddsv3['ConfWLpct'] = oddsv3['ConfW']/(oddsv3['ConfW'] + oddsv3['ConfL'])
oddsv3['ATSpct'] = oddsv3['ATSW']/(oddsv3['ATSW'] + oddsv3['ATSL'])
oddsv3['HomeATSpct'] = oddsv3['HomeATSW']/(oddsv3['HomeATSW'] + oddsv3['HomeATSL'])
oddsv3['AwayATSpct'] = oddsv3['AwayATSW']/(oddsv3['AwayATSW'] + oddsv3['AwayATSL'])
oddsv3['ConfATSpct'] = oddsv3['ConfATSW']/(oddsv3['ConfATSW'] + oddsv3['ConfATSL'])
oddsv3['ConfGame'] = (oddsv3['Conf'] == oddsv3['OppConf'])*1

# Generate and Merge Opponent Records
# Season, Team, G, and record columns
desc = ['Season','Team','G']
record_stats = list(oddsv3.columns[list(oddsv3.columns).index('W'):])
opprecords = oddsv3[desc+record_stats].copy()
# Rename to Opponent Stats
temp = dict(zip(['Team','G']+record_stats,['Opp','OppG']+['Opp' + col for col in record_stats]))
opprecords = opprecords.rename(columns=temp)
# Combine
oddsv4 = pd.merge(oddsv3, opprecords, on = ['Season','Opp','OppG'], how='left')
# Reset Memory
del oddsv3

# -- Natty Tournament --
oddsv4 = pd.merge(oddsv4, NattyDates, on=['Season'], how='left')
oddsv4 = pd.merge(oddsv4, marchmadness, on = ['Season','Team'], how='left')
oddsv4 = pd.merge(oddsv4, oppmarchmadness, on = ['Season','Opp'], how='left')

oddsv4['TourneyGame'] = ((oddsv4['Date'] >= oddsv4['StartNatty']) & (~oddsv4['TourneySeed'].isna()))*1
oddsv4['TourneyPlayIn'] = ((oddsv4['TourneySeed'] == oddsv4['OppTourneySeed']) &
                                (oddsv4['TourneySeed'] + oddsv4['OppTourneySeed'] > 15))*1

temp = oddsv4[(oddsv4['TourneyGame'] == 1) &
                 (oddsv4['TourneyPlayIn'] != 1)].copy()
temp['TourneyRound'] = temp.groupby(['Season','Team'])['Date'].rank(ascending=True)
tourneyroundhelperdf = temp[['Date','Team','TourneyRound']]
oddsv4 = pd.merge(oddsv4, tourneyroundhelperdf, on=['Date','Team'], how='left')

# -- Rematch Stats --
# Create game ID for Rematch identification
oddsv4['UniqueGames'] = oddsv4.groupby(['Team','Opp','Season']).G.rank(method='first',ascending=True)

# Create df for merge
temp = oddsv4.copy()
temp['UniqueGames'] = temp['UniqueGames'] + 1
temp = temp[['Team','Opp','Season','UniqueGames','Location','MOV','Spread','ATSMargin']]
temp.columns = ['Team','Opp','Season','UniqueGames','RematchLocation','RematchMOV','RematchSpread','RematchATSMargin']
oddsv5 = pd.merge(oddsv4, temp, on=['Team','Opp','Season','UniqueGames'], how='left')
# Reset Memory
del oddsv4

# -- Strength of Schedule --
## $ Watch for D3 Teams (Maybe fix by only working with Teams where Conf != np.nan?)
# Initialize
rec_dict = {}
sched_dict = {}
wins_list = []
losses_list = []

# Dictionary of Teams for Schedule
all_scheds = pd.DataFrame(oddsv5.groupby(['Season','Team'])['Opp'].apply(list)).reset_index()
teams_of_all_scheds = pd.unique(all_scheds.Team)
for tm in teams_of_all_scheds:
    sched_dict[tm] = {}
## Fill Dict with Team Schedules for each Season
for i in range(0, len(all_scheds)):
    sched_dict[all_scheds.loc[i,'Team']][all_scheds.loc[i,'Season']] = all_scheds.loc[i,'Opp']

# Initialize Dicts of Teams for Records
all_teams = pd.unique(oddsv5['Team'])
for tm in all_teams:
    rec_dict[tm] = {}
## Initialize Dicts of all Seasons for each Team for Records
unique_team_seasons = oddsv5[['Team','Season']].copy().drop_duplicates().reset_index(drop=True)
for i in range(0,len(unique_team_seasons)):
    rec_dict[unique_team_seasons.loc[i,'Team']][unique_team_seasons.loc[i,'Season']] = {}
### Fill Dict with Team Records for each Date
for i in range(0,len(oddsv5)):
    rec_dict[oddsv5.loc[i,'Team']][oddsv5.loc[i,'Season']][oddsv5.loc[i,'Date']] = {'W':oddsv5.loc[i,'W']+(oddsv5.loc[i,'ResultDummy']==1)*1,
                                                                                     'L':oddsv5.loc[i,'L']+(oddsv5.loc[i,'ResultDummy']==0)*1}
#### Create 0-0 July 4th Record for each team that will match with the start of the season
for tm in rec_dict.keys():
    for szn in rec_dict[tm].keys():
        rec_dict[tm][szn][pd.Timestamp(str(szn)+'-7-04 00:00:00')] = {'W':0,
                                                                        'L':0}

# Loop through games to create SOS
for i in range(0,len(oddsv5)):
    wins = 0
    losses = 0
    g = oddsv5.loc[i,'G']
    team = oddsv5.loc[i,'Team']
    szn = oddsv5.loc[i,'Season']
    daat = oddsv5.loc[i,'Date']
    sched = sched_dict[team][szn][:(int(g)-1)]
    for t in [x for x in sched if x == x]:
        try:
            datefound = min(rec_dict[t][szn].keys(), key=lambda x: (x>daat, abs(x-daat)))
            wins += rec_dict[t][szn][datefound]['W']
            losses += rec_dict[t][szn][datefound]['L']
        except:
            continue
    wins_list.append(wins)
    losses_list.append(losses)

# Finalize the SOS Variable into the oddsv5 dataset
oddsv5['SOSW'] = wins_list
oddsv5['SOSL'] = losses_list
oddsv5['SOS'] = (oddsv5['SOSW']-oddsv5['L'])/(oddsv5['SOSW']+oddsv5['SOSL']-oddsv5['W']-oddsv5['L'])
oddsv5 = oddsv5.drop(['SOSW','SOSL'], axis=1)

# Opponent SOS
oppsosref = oddsv5[['Date','G','Team','SOS']].copy().rename(columns={'Team':'Opp',
                                                                     'G':'OppG',
                                                                    'SOS':'OppSOS'})
oddsv6 = pd.merge(oddsv5, oppsosref, on=['Date','OppG','Opp'], how='left')
# Reset Memory
del oddsv5

# -- Variance of Play --
### Variance of Play defined as Spread in Wins minus Spread in Losses ###
# Temp variables
oddsv6['tempSpreadInLoss'] = (oddsv6['ResultDummy'] == 0)*(oddsv6['Spread'])
oddsv6['tempSpreadInWin'] = (oddsv6['ResultDummy'] > 0)*(oddsv6['Spread'])

# Cumulatively Sum the Temp Variables
oddsv6['VOPW'] = (oddsv6.groupby(['Season','Team'])['tempSpreadInWin'].cumsum() -\
                                                        oddsv6['tempSpreadInWin'])/oddsv6['G']
oddsv6['VOPL'] = (oddsv6.groupby(['Season','Team'])['tempSpreadInLoss'].cumsum() -\
                                                        oddsv6['tempSpreadInLoss'])/oddsv6['G']
oddsv6['VOP'] = oddsv6['VOPW']-oddsv6['VOPL']
# Normalize all three
for var in ['VOPW','VOPL','VOP']:
    mn = oddsv6[var].mean()
    std = oddsv6[var].std()
    oddsv6[var] = (oddsv6[var]-mn)/std
# Remove Temp variables
oddsv7 = oddsv6.drop(['tempSpreadInLoss','tempSpreadInWin'],axis=1)
# Reset Memory
del oddsv6

# Opponent VOP
oppvopref = oddsv7[['Date','Team','G','VOPW','VOPL','VOP']].copy().rename(columns={'Team':'Opp',
                                                                                   'G':'OppG',
                                                                                'VOP':'OppVOP',
                                                                                'VOPW':'OppVOPW',
                                                                                'VOPL':'OppVOPL'})
oddsv8 = pd.merge(oddsv7, oppvopref, on=['Date','OppG','Opp'], how='left')
oddsv8['VOPsum'] = oddsv8['VOP'] + oddsv8['OppVOP']
# Reset Memory
del oddsv7

# -- Close Game Weighted Record -- 
# Sort Values
oddsv8 = oddsv8.sort_values('Date')

# Results weighted by Closeness of Games to determine clutch value
oddsv8['tempCGWR'] = np.maximum(0.1, (1-((abs(oddsv8['MOV'])/100)**3)*3000))*(oddsv8['MOV']/oddsv8['MOV'].abs())
oddsv8['CGWR'] = oddsv8.groupby(['Season','Team'])['tempCGWR'].cumsum() - oddsv8['tempCGWR']

# Drop Temp
oddsv9 = oddsv8.drop('tempCGWR',axis=1)
# Reset Memory
del oddsv8

# -- Merge Team DB with Player DB --
odds_wip = pd.merge(oddsv9, team_agg_stats.drop('MP',axis=1), on = ['Team','Season','Date'], how='left')

# Opponents
temp_col_list = all_agg_stats + ['Def' + col for col in total_stats_col]
# Opponent Stats
temp = team_agg_stats.drop('MP',axis=1)
temp.columns = ['Opp'+col if col in temp_col_list else col for col in team_agg_stats.drop('MP',axis=1).columns]
temp.rename(columns={'Team':'Opp'},inplace=True)
# Merge
final_odds = pd.merge(odds_wip, temp, on = ['Opp','Season','Date'], how='left')

##################################################
###### End Processing ############################
##################################################

# Test File Creation #
creation_name = 'Current Year Processed Stats'
final_odds.to_csv('saved_file.csv',index=False)

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().update(fileId='1PTk0cjqnB5m1OAUBZdNKylDZwm_oFAjo',
                                body=file_metadata, 
                                media_body=media,
                              fields=returned_fields).execute()
