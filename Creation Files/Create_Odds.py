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

# -- Odds -- #
# Initiate
start_date = '2021-06-01'
end_date = '2024-06-01'

# Setup Connection
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
user_agent = 'Chrome/60.0.3112.50'
options.add_argument(f'user-agent={user_agent}')
driver = webdriver.Chrome(service=service, options=options)

# Access Website
driver.get('https://betiq.teamrankings.com/college-basketball/betting-trends/custom-trend-tool')
driver.execute_script("document.body.style.zoom='25%'")
## Change to 100 games per page
time.sleep(1.5)
driver.find_element(By.XPATH,'//select[@name="custom-filter-table_length"]').click()
time.sleep(0.2)
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
for i in range(0,100):
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
        break

# Remove games before end_date
odds_final = game_log_table[game_log_table['Date'] < pd.to_datetime(end_date)]

#---------
# Export #
#---------

# File Creation
creation_name = 'Odds - '+str(pd.to_datetime(start_date).year)+'-'+str(pd.to_datetime(end_date).year)
odds_final.to_csv('saved_file.csv')

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv',
                'parents':['1DdTC37ao2EK23f-dnQ5Tj9EvgoS9BaIW']}
media = MediaFileUpload('saved_file.csv',
                        mimetype='text/csv')
file = ggl_drive.files().create(body=file_metadata, media_body=media,
                              fields=returned_fields).execute()
