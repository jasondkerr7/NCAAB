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
previous_odds = pd.read_csv('https://docs.google.com/uc?id=1d6slsiCtovW0zJgG5eqrgAFzJEW17r7K')
# Team Help
temp = pd.read_csv('https://docs.google.com/spreadsheets/d/1D9eKEUM_B3gXs3ukfj0_704YzG3Iw4u2_ATdj21JvGE/export?format=csv&gid=0')
# Create from files
teamhelp = dict(zip(temp['Team Rankings'],temp['Pandas']))

# -- Odds -- #
# Initiate
start_date = (pd.to_datetime(previous_odds['Date'].max()) - timedelta(days=1)).strftime("%Y-%m-%d")
end_date = '2025-06-01'

# Setup Connection
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
user_agent = 'Chrome/60.0.3112.50'
options.add_argument(f'user-agent={user_agent}')
driver = webdriver.Chrome(service=service, options=options)

# Access Website
driver.get('https://betiq.teamrankings.com/college-basketball/betting-trends/custom-trend-tool')
driver.execute_script("document.body.style.zoom='80%'")
time.sleep(2)
y = driver.find_element(By.XPATH,'//select[@name="custom-filter-table_length"]').location['y']-150
driver.execute_script("window.scrollTo(0, "+str(y)+")")

## Change to 100 games per page
time.sleep(2.5)
try:
  driver.find_element(By.XPATH,'//select[@name="custom-filter-table_length"]').click()
except:
  try:
    # Close the Cookies Bar if it's up
    driver.find_element(By.XPATH,'//button[@class="onetrust-close-btn-handler onetrust-close-btn-ui banner-close-button ot-close-icon"]').click()
    time.sleep(1)
    print('%%%%%%%%%%%%%%%%%%%%%%%%%      Closed out the Cookies bar          %%%%%%%%%%%%%%%%%%%%%%%%')
    try:
      driver.find_element(By.XPATH,'//select[@name="custom-filter-table_length"]').click()
    except:
      driver.find_element(By.XPATH,'//button[@data-popup-action="no"]').click()
      print('%%%%%%%%%%%%%%%%%%%%%%%%%      Closed out another Pop Up          %%%%%%%%%%%%%%%%%%%%%%%%')
      time.sleep(1)
      driver.find_element(By.XPATH,'//select[@name="custom-filter-table_length"]').click()
  except:  
    driver.get_screenshot_as_file("screenshot.png")
    # Screenshot
    returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
    file_metadata = {'name': 'screenshot-error.png',
                    'parents':['1DdTC37ao2EK23f-dnQ5Tj9EvgoS9BaIW']}
    media = MediaFileUpload('screenshot.png',
                            mimetype='image/png')
    file = ggl_drive.files().create(body=file_metadata, media_body=media,
                                  fields=returned_fields).execute()
    sys.exit
  
time.sleep(1.2)
driver.find_element(By.XPATH,'//option[@value="100"]').click()
time.sleep(1)
## Sort Dates to pull chronological games
for i in range(0,10):
    try:
        driver.find_element(By.XPATH,'//th[@aria-label="Date: activate to sort column ascending"]').click()
        break
    except:
        time.sleep(1)
time.sleep(1)
for i in range(0,10):
    try:
        driver.find_element(By.XPATH,'//th[@aria-label="Date: activate to sort column descending"]').click()
        break
    except:
        time.sleep(1)

# Ensure there's enough sleep time for the first BeautifulSoup pull
time.sleep(5)

# Beautiful Soup and create Table
page_source = driver.page_source
soup = BeautifulSoup(page_source)
temp = pd.read_html(StringIO(str(soup.find_all('table',{'id':'custom-filter-table'}))))[0]
temp = temp[~temp['Team'].isna()]
temp['Date'] = pd.to_datetime(temp['Date'])
game_log_table = temp.copy()

# Loop through each new page
for i in range(0,1000):
    page_num = int(soup.find_all('a',{'class':'paginate_button current'})[0].text)
    driver.find_element(By.XPATH,'//a[@class="paginate_button next"][1]').click()
    time.sleep(1)
    for ii in range(0,30):
        page_source = driver.page_source
        soup = BeautifulSoup(page_source)
        if int(soup.find_all('a',{'class':'paginate_button current'})[0].text) == (page_num+1):
            break
        else:
            time.sleep(0.25)
    temp = pd.read_html(StringIO(str(soup.find_all('table',{'id':'custom-filter-table'}))))[0]
    temp = temp[~temp['Team'].isna()]
    temp['Date'] = pd.to_datetime(temp['Date'])
    game_log_table = pd.concat([game_log_table, temp], ignore_index=True)
    if temp.loc[len(temp)-1,'Date'] < pd.to_datetime(start_date):
      print('comparison to break - last date of the dataframe: ',temp.loc[len(temp)-1,'Date'])
      print('comparison to break - Start Date: ',pd.to_datetime(start_date))
      print('Broken at this Iteration: ',i,' // Page Number',page_num)
      break

# ----------
# Processing
# ----------

# Remove games outside of start and end date
odds_final_wip = game_log_table[game_log_table['Date'] < pd.to_datetime(end_date)].copy()
odds_final = odds_final_wip[odds_final_wip['Date'] > pd.to_datetime(start_date)].copy()
# Fix Score
odds_final['PF'] = pd.to_numeric(odds_final['Score'].str.split('-').str[0])
odds_final['PA'] = pd.to_numeric(odds_final['Score'].str.split('-').str[1])
odds_final.drop('Score',axis=1,inplace=True)
# Fix team names
odds_final['Team'].replace(teamhelp,inplace=True)
odds_final['Opponent'].replace(teamhelp,inplace=True)
# Fix column names
odds_final = odds_final.rename(columns={'Total (O/U)':'Total',
                                         'Money Line':'ML',
                                        'O/U Margin':'TotalMargin',
                                         'ATS Margin':'ATSMargin',
                                        'Opponent':'Opp'})


#---------
# Export #
#---------
# Final
final = pd.concat([previous_odds, odds_final],ignore_index=True)
final['Date'] = pd.to_datetime(final['Date'])
final.sort_values('Date',inplace=True)
final.drop_duplicates(inplace=True)

# File Creation
creation_name = 'Current Year Odds'
final.to_csv('saved_file.csv', index=False)

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().update(fileId='1d6slsiCtovW0zJgG5eqrgAFzJEW17r7K',
                                body=file_metadata, 
                                media_body=media,
                              fields=returned_fields).execute()
