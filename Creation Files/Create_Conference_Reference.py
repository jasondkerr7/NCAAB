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
barttorvik_headers = pd.read_csv('https://docs.google.com/spreadsheets/d/1_alO289CpDPCFemFrC5D-sxL8WJqWj57Krny06a4K6M/export?format=csv&gid=0')

# Team Help
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1D9eKEUM_B3gXs3ukfj0_704YzG3Iw4u2_ATdj21JvGE/export?format=csv&gid=0')

# Create from files
teamhelp = dict(zip(temp['Bart Torvik'],temp['Pandas']))

# -- Pull Conference Reference -- #
# Initialize
yearrange = range(2006,2026)
conferences_bt = pd.DataFrame()
team_list = []
conf_list = []

for yr in yearrange:
  # get HTML from URL
  url = 'https://barttorvik.com/trank.php?year='+str(yr)+'&sort=&top=0&conlimit=All#'
  page = requests.get(url)
  soup = BeautifulSoup(page.text, 'lxml')
  
  # Loop through the rows
  for row in soup.find_all('tr',{'class':'seedrow'}):
      # get team and conference
      tm = row.find('td',{'class':'teamname'}).find('a').contents[0]
      try:
          cnf = row.select('a[href*="conf"]')[0].text
      except:
          cnf = row.find_all('td')[2].find('a').contents[0]
      
      # Append to list
      team_list.append(tm)
      conf_list.append(cnf)
  
  # Create Dataframe
  temp = pd.DataFrame({'Team':team_list,
                       'Conf':conf_list})
  temp['Season'] = yr
  # merge
  conferences_bt = pd.concat([conferences_bt, temp], ignore_index=True)

# Fix Team Names
conferences_bt = conferences_bt['Team'].replace(teamhelp)

##################################################
###### End Setup #################################
##################################################

# File Creation #
creation_name = 'Conference Key through 2025'
conferences_bt.to_csv('saved_file.csv')

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().update(fileId='1ewDetzYCoyS5hnVBMjXaiTSM_fLop3wy',
                                body=file_metadata, 
                                media_body=media,
                              fields=returned_fields).execute()
