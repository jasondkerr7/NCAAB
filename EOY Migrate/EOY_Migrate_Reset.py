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
# Current Year Files
cy_odds = pd.read_csv('https://docs.google.com/uc?id='+codds_id)
cy_playerstats = pd.read_csv('https://docs.google.com/uc?id='+cplayerstats_id)
cy_rankings = pd.read_csv('https://docs.google.com/uc?id='+crankings_id)
cy_processed = pd.read_csv('https://docs.google.com/uc?id='+cprocessed_id)

# -- Merge Files -- #
final_odds = cy_odds.iloc[:0]
final_playerstats = cy_playerstats.iloc[:0]
final_rankings = cy_rankings.iloc[:0]
final_processed = cy_processed.iloc[:0]


# -- Replace CY Files -- #

# Odds
# File Creation
creation_name = 'Current Year Odds'
final_odds.to_csv('saved_file.csv',index=False)

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().update(fileId=codds_id,
                                body=file_metadata, 
                                media_body=media,
                            fields=returned_fields).execute()

# Player Stats
# File Creation
creation_name = 'Current Year Player Stats'
final_playerstats.to_csv('saved_file.csv',index=False)

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().update(fileId=cplayerstats_id,
                                body=file_metadata, 
                                media_body=media,
                            fields=returned_fields).execute()

# Rankings
# File Creation
creation_name = 'Current Year Rankings'
final_rankings.to_csv('saved_file.csv',index=False)

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().update(fileId=crankings_id,
                                body=file_metadata, 
                                media_body=media,
                            fields=returned_fields).execute()

# Processed
# File Creation
creation_name = 'Current Year Processed Stats'
final_processed.to_csv('saved_file.csv',index=False)

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().update(fileId=cprocessed_id,
                                body=file_metadata, 
                                media_body=media,
                            fields=returned_fields).execute()