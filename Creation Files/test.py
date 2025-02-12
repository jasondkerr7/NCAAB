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
import psutil
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
odds = pd.read_csv('https://docs.google.com/uc?id=1U229Lq93X4Cd9ovtYyVD7fQ3G4ragqwQ').rename(columns={'Opponent':'Opp'})
rankings = pd.read_csv('https://docs.google.com/uc?id=1gRwZVVxARkDCWkR9hXMopW3vOF46aunn')
conference_reference = pd.read_csv('https://docs.google.com/uc?id=1ewDetzYCoyS5hnVBMjXaiTSM_fLop3wy')[['Team','Conf','Season']]
# Team Help
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1D9eKEUM_B3gXs3ukfj0_704YzG3Iw4u2_ATdj21JvGE/export?format=csv&gid=0')

### Create from files
opp_conference_reference = conference_reference.rename(columns={'Team':'Opp',
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
odds['DateRef'] = odds['DateRef'].replace(date_ref_dict)

# Create Reference DFs
rankings_ref = rankings[['Date','Team','Rank']].rename(columns={'Date':'DateRef'}).copy()
opp_rankings_ref = rankings_ref.rename(columns={'Team':'Opp',
                                                'Rank':'OppRank'})

# Merge
temp = pd.merge(odds, rankings_ref, on=['Team','DateRef'], how='left')
oddsv2 = pd.merge(temp, opp_rankings_ref, on=['Opp','DateRef'], how='left')
oddsv2 = oddsv2.drop_duplicates().reset_index(drop=True)

oddsv2['ResultDummy'] = (oddsv2['MOV'] > 0)*1
oddsv2['SpreadResultDummy'] = np.where(oddsv2['ATSMargin'] == 0, 'Push',
                                         np.where(oddsv2['ATSMargin'] > 0, 'Cover', 'Loss'))

oddsv2['G'] = oddsv2.groupby(['Team','Season'])['Date'].rank(method = 'first',ascending=True)
oddsv2['OppG'] = oddsv2.groupby(['Opp','Season'])['Date'].rank(method = 'first',ascending=True)

# -------------------------- #
# -- Create New Variables -- #
# -------------------------- #
print("Entered VOP with RAM Usage of -- ",psutil.virtual_memory().percent)
# -- Variance of Play --
### Variance of Play defined as Spread in Wins minus Spread in Losses ###

# Temp variables
oddsv2['tempSpreadInLoss'] = (oddsv2['ResultDummy'] == 0)*(oddsv2['Spread'])
oddsv2['tempSpreadInWin'] = (oddsv2['ResultDummy'] > 0)*(oddsv2['Spread'])

# Cumulatively Sum the Temp Variables
oddsv2['VOPW'] = (oddsv2.groupby(['Season','Team'])['tempSpreadInWin'].cumsum() -\
                                                        oddsv2['tempSpreadInWin'])/oddsv2['G']
oddsv2['VOPL'] = (oddsv2.groupby(['Season','Team'])['tempSpreadInLoss'].cumsum() -\
                                                        oddsv2['tempSpreadInLoss'])/oddsv2['G']
oddsv2['VOP'] = oddsv2['VOPW']-oddsv2['VOPL']

print("Normalized with RAM Usage of -- ",psutil.virtual_memory().percent)

# Normalize all three
for var in ['VOPW','VOPL','VOP']:
    mn = oddsv2[var].mean()
    std = oddsv2[var].std()
    oddsv2[var] = (oddsv2[var]-mn)/std
# Remove Temp variables
oddsv7 = oddsv2.drop(['tempSpreadInLoss','tempSpreadInWin'],axis=1)

# Opponent VOP
oppvopref = oddsv7[['Date','Team','VOPW','VOPL','VOP']].copy().rename(columns={'Team':'Opp',
                                                                                'VOP':'OppVOP',
                                                                                'VOPW':'OppVOPW',
                                                                                'VOPL':'OppVOPL'})
oddsv8 = pd.merge(oddsv7, oppvopref, on=['Date','Opp'], how='left')
oddsv8['VOPsum'] = oddsv8['VOP'] + oddsv8['OppVOP']

print("Ended with RAM Usage of -- ",psutil.virtual_memory().percent)
