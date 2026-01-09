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

# Initialize
if datetime.today().month < 7:
  yearref = datetime.today().year
else:
  yearref = datetime.today().year + 1

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
# IDs
codds_id = '1d6slsiCtovW0zJgG5eqrgAFzJEW17r7K'
cplayerstats_id = '1yYXa7aWdXYYE2D6vdbElkThdOlIgM5zz'
crankings_id = '1YI5txYdHgmB3Sw_wwxY0eLsaXzD4dyrr'
cprocessed_id = '1PTk0cjqnB5m1OAUBZdNKylDZwm_oFAjo'
podds_id = '1U229Lq93X4Cd9ovtYyVD7fQ3G4ragqwQ'
pplayerstats_id = '17p3ZBuoFeYSj4E64pRuLUJBL7LpSvfin'
prankings_id = '1gRwZVVxARkDCWkR9hXMopW3vOF46aunn'
pprocessed_id = '1JSa-KqrY3TnE9tyiUxoznbHPwL2JimqT'
# Current Year Files
cy_odds = pd.read_csv('https://docs.google.com/uc?id='+codds_id)
cy_playerstats = pd.read_csv('https://docs.google.com/uc?id='+cplayerstats_id)
cy_rankings = pd.read_csv('https://docs.google.com/uc?id='+crankings_id)
cy_processed = pd.read_csv('https://docs.google.com/uc?id='+cprocessed_id)
# Previous Year Files
prev_odds = pd.read_csv('https://docs.google.com/uc?id='+podds_id)
prev_playerstats = pd.read_csv('https://docs.google.com/uc?id='+pplayerstats_id)
prev_rankings = pd.read_csv('https://docs.google.com/uc?id='+prankings_id)
prev_processed = pd.read_csv('https://docs.google.com/uc?id='+pprocessed_id)

# -- Merge Files -- #
# Prepare for sort with column type fix
cy_odds['Date'] = pd.to_datetime(cy_odds['Date'])
cy_playerstats['Date'] = pd.to_datetime(cy_playerstats['Date'])
cy_rankings['Date'] = pd.to_datetime(cy_rankings['Date'])
cy_processed['Date'] = pd.to_datetime(cy_processed['Date'])
prev_odds['Date'] = pd.to_datetime(prev_odds['Date'])
prev_playerstats['Date'] = pd.to_datetime(prev_playerstats['Date'])
prev_rankings['Date'] = pd.to_datetime(prev_rankings['Date']
prev_processed['Date'] = pd.to_datetime(prev_processed['Date']))
# Sort for proper merging
cy_odds.sort_values(['Date'], ascending=True)
cy_playerstats.sort_values(['Date'], ascending=True)
cy_rankings.sort_values(['Date','Rank'], ascending=True)
cy_processed.sort_values(['Date','Rank'], ascending=True)
prev_odds.sort_values(['Date'], ascending=True)
prev_playerstats.sort_values(['Date'], ascending=True)
prev_rankings.sort_values(['Date','Rank'], ascending=True)
prev_processed.sort_values(['Date','Rank'], ascending=True)
# Merge CY and Prev files
final_odds = pd.concat([prev_odds, cy_odds],axis=0,ignore_index=True)
final_playerstats = pd.concat([prev_playerstats, cy_playerstats],axis=0,ignore_index=True)
final_rankings = pd.concat([prev_rankings, cy_rankings],axis=0,ignore_index=True)
final_processed = pd.concat([prev_processed, cy_processed],axis=0,ignore_index=True)

# -- Confirm Correct Merging -- #
odds_bool = (len(cy_odds) + len(prev_odds) == len(final_odds))
playerstats_bool = (len(cy_playerstats) + len(prev_playerstats) == len(final_playerstats))
rankings_bool = (len(cy_rankings) + len(prev_rankings) == len(final_rankings))
processed_bool = (len(cy_processed) + len(prev_processed) == len(final_processed))

if odds_bool and playerstats_bool and rankings_bool and processed_bool:

    # -- Replace Prev Files -- #

    # Odds
    # File Creation
    creation_name = 'Odds - 2021-'+str(yearref-1)
    final_odds.to_csv('saved_file.csv',index=False)

    # Upload File
    returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
    file_metadata = {'name': creation_name+'.csv'}
    media = MediaFileUpload('saved_file.csv',
                            mimetype='text/csv')
    file = ggl_drive.files().update(fileId=podds_id,
                                    body=file_metadata, 
                                    media_body=media,
                                fields=returned_fields).execute()

    # Player Stats
    # File Creation
    creation_name = 'Player Stats through '+str(yearref-1)
    final_playerstats.to_csv('saved_file.csv',index=False)

    # Upload File
    returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
    file_metadata = {'name': creation_name+'.csv'}
    media = MediaFileUpload('saved_file.csv',
                            mimetype='text/csv')
    file = ggl_drive.files().update(fileId=pplayerstats_id,
                                    body=file_metadata, 
                                    media_body=media,
                                fields=returned_fields).execute()

    # Rankings
    # File Creation
    creation_name = 'Rankings through '+str(yearref-1)
    final_rankings.to_csv('saved_file.csv',index=False)

    # Upload File
    returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
    file_metadata = {'name': creation_name+'.csv'}
    media = MediaFileUpload('saved_file.csv',
                            mimetype='text/csv')
    file = ggl_drive.files().update(fileId=prankings_id,
                                    body=file_metadata, 
                                    media_body=media,
                                fields=returned_fields).execute()

    # Processed
    # File Creation
    creation_name = 'Processed Stats 2021-'+str(yearref-1)
    final_processed.to_csv('saved_file.csv',index=False)

    # Upload File
    returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
    file_metadata = {'name': creation_name+'.csv'}
    media = MediaFileUpload('saved_file.csv',
                            mimetype='text/csv')
    file = ggl_drive.files().update(fileId=pprocessed_id,
                                    body=file_metadata, 
                                    media_body=media,
                                fields=returned_fields).execute()

    # Check that uploads worked before moving to clearing out the Current Year Files
    new_odds = pd.read_csv('https://docs.google.com/uc?id='+podds_id)
    new_playerstats = pd.read_csv('https://docs.google.com/uc?id='+pplayerstats_id)
    new_rankings = pd.read_csv('https://docs.google.com/uc?id='+prankings_id)
    new_processed = pd.read_csv('https://docs.google.com/uc?id='+pprocessed_id)

    print('Odds DF Length - Old:' ,len(prev_odds),' // New: ',len(new_odds))
    print('Player Stats DF Length - Old:' ,len(prev_playerstats),' // New: ',len(new_playerstats))
    print('Rankings DF Length - Old:' ,len(prev_rankings),' // New: ',len(new_rankings))
    print('Processed DF Length - Old:' ,len(prev_processed),' // New: ',len(new_processed))

else:
    print(('' if odds_bool else 'Odds Issue'),
            ('' if playerstats_bool else 'Player Stats Issue'),
            ('' if rankings_bool else 'Rankings Issue'),
            ('' if processed_bool else 'Processed Issue'))


