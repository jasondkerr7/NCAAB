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
odds = pd.read_csv('https://docs.google.com/uc?id=1U229Lq93X4Cd9ovtYyVD7fQ3G4ragqwQ')
rankings = pd.read_csv('https://docs.google.com/uc?id=1gRwZVVxARkDCWkR9hXMopW3vOF46aunn')
conference_reference = pd.read_csv('https://docs.google.com/uc?id=1ewDetzYCoyS5hnVBMjXaiTSM_fLop3wy')[['Team','Conf','Season']]
# Team Help
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1D9eKEUM_B3gXs3ukfj0_704YzG3Iw4u2_ATdj21JvGE/export?format=csv&gid=0')

### Create from files
opp_conference_reference = conference_reference.rename({'Team':'Opp',
                                                       'Conf':'OppConf'})

### Pre-Processing
rankings['Date'] = pd.to_datetime(rankings['Date'])
odds['Date'] = pd.to_datetime(odds['Date'])
odds['Season'] = (odds['Date'].dt.month > 6)*1 + odds['Date'].dt.year
odds = odds.sort_values('Date', ascending=True)


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
odds['DateRef'].replace(date_ref_dict,inplace=True)

# Create Reference DFs
rankings_ref = rankings[['Date','Team','Rank']].rename(columns={'Date':'DateRef'}).copy()
opp_rankings_ref = rankings_ref.rename(columns={'Team':'Opp',
                                                'Rank':'OppRank'})

# Merge
temp = pd.merge(odds, rankings_ref, on=['Team','DateRef'], how='left')
oddsv2 = pd.merge(temp, opp_rankings_ref, on=['Opp','DateRef'], how='left')
cy_ncaabor = cy_ncaabor.drop_duplicates().reset_index(drop=True)

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
opp_previous_game_ref.columns = opp_pg_keys_cols + ['Opp' + y for y in pg_stats_cols]
# Merge
temp = pd.merge(oddsv2, previous_game_ref, on=pg_key_cols, how='left')
oddsv3 = pd.merge(temp, opp_previous_game_ref, on=opp_pg_key_cols, how='left')










