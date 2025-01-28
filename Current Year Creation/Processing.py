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
# Previous Odds
odds = pd.read_csv('https://docs.google.com/uc?id=1U229Lq93X4Cd9ovtYyVD7fQ3G4ragqwQ')
rankings = pd.read_csv('https://docs.google.com/uc?id=1gRwZVVxARkDCWkR9hXMopW3vOF46aunn')
### Pre-Processing
rankings['Date'] = pd.to_datetime(rankings['Date'])
odds['Date'] = pd.to_datetime(odds['Date'])
odds['Season'] = np.where(odds['Date'].dt.month > 6, odds['Date'].dt.year + 1, odds['Date'].dt.year)
# Team Help
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1D9eKEUM_B3gXs3ukfj0_704YzG3Iw4u2_ATdj21JvGE/export?format=csv&gid=0')
# Create from files

##################################################
###### Processing ################################
##################################################

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


