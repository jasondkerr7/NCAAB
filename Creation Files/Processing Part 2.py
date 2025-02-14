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
oddsv6 = pd.read_csv('https://docs.google.com/uc?id=1JSa-KqrY3TnE9tyiUxoznbHPwL2JimqT').rename(columns={'Opponent':'Opp'})
rankings = pd.read_csv('https://docs.google.com/uc?id=1gRwZVVxARkDCWkR9hXMopW3vOF46aunn')
conference_reference = pd.read_csv('https://docs.google.com/uc?id=1ewDetzYCoyS5hnVBMjXaiTSM_fLop3wy')[['Team','Conf','Season']]
# Team Help
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1D9eKEUM_B3gXs3ukfj0_704YzG3Iw4u2_ATdj21JvGE/export?format=csv&gid=0')

### Create from files
opp_conference_reference = conference_reference.rename(columns={'Team':'Opp',
                                                       'Conf':'OppConf'})

### Pre-Processing
rankings['Date'] = pd.to_datetime(rankings['Date'])
oddsv6['Date'] = pd.to_datetime(oddsv6['Date'])
oddsv6['Season'] = (oddsv6['Date'].dt.month > 6)*1 + oddsv6['Date'].dt.year
oddsv6 = oddsv6.sort_values('Date', ascending=True)

##################################################
###### Processing ################################
##################################################

print('VOP')
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
oppvopref = oddsv7[['Date','Team','VOPW','VOPL','VOP']].copy().rename(columns={'Team':'Opp',
                                                                                'VOP':'OppVOP',
                                                                                'VOPW':'OppVOPW',
                                                                                'VOPL':'OppVOPL'})
oddsv8 = pd.merge(oddsv7, oppvopref, on=['Date','Opp'], how='left')
oddsv8['VOPsum'] = oddsv8['VOP'] + oddsv8['OppVOP']
# Reset Memory
del oddsv7

print('CGWR')
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

##################################################
###### End Processing ############################
##################################################

print('File Creation')
# Test File Creation #
creation_name = 'Processed Stats 2021-2024'
oddsv9.to_csv('saved_file.csv',index=False)

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().update(fileId='17p3ZBuoFeYSj4E64pRuLUJBL7LpSvfin',
                                body=file_metadata, 
                                media_body=media,
                              fields=returned_fields).execute()
