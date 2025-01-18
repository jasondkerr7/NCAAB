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
driver.execute_script("document.body.style.zoom='80%'")
time.sleep(2)
y = driver.find_element(By.XPATH,'//select[@name="custom-filter-table_length"]').location['y']-150
driver.execute_script("window.scrollTo(0, "+str(y)+")")
time.sleep(2)
driver.get_screenshot_as_file("screenshot.png")
time.sleep(3)
try:
  driver.find_element(By.XPATH,'//select[@name="custom-filter-table_length"]').click()
  print('It Worzed!!')
except Exception as e:
  print('Herez the error:',e)

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': 'screenshot.png',
                'parents':['1DdTC37ao2EK23f-dnQ5Tj9EvgoS9BaIW']}
media = MediaFileUpload('screenshot.png',
                        mimetype='image/png')
file = ggl_drive.files().create(body=file_metadata, media_body=media,
                              fields=returned_fields).execute()
