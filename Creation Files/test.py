##################################################
###### Setup #####################################
##################################################

## -- Import Required Packages -- ##

import gc
import psutil
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
guser = os.environ['G_USERNAME']
gpwd = os.environ['G_PASSWORD']

# Connect to the google service account
scope = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_info(
                              info=service_account_cred, 
                              scopes=scope)
ggl_drive = build('drive', 'v3', credentials=credentials)

# Setup Selenium Connection
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
user_agent = 'Chrome/60.0.3112.50'
options.add_argument(f'user-agent={user_agent}')
driver = webdriver.Chrome(service=service, options=options)

# Access Website
driver.get('https://briteswitch.com/RebatePro-EVChargers/power-filter.php')
# Login
driver.find_element(By.XPATH,'//input[@placeholder="Login"]').send_keys("jkerr@evconnect.com")
time.sleep(0.2)
driver.find_element(By.XPATH,'//input[@placeholder="Password"]').send_keys("49856")
time.sleep(0.4)
driver.find_element(By.XPATH,'//button[@type="submit"]').click()
time.sleep(2.1)

# Email Verification
for xyz in range(0,10):
  # Sleep for the Email to arrive
  time.sleep(20)
  # Retrieve Authorization Token
  server = 'imap.gmail.com'

  USERNAME = guser
  PASSWORD = gpwd

  mail = imaplib.IMAP4_SSL(server)
  # conn.set_debuglevel(False)
  mail.login(USERNAME, PASSWORD)
  mail.select('inbox')
  status, data = mail.search(None, 'ALL')
  status, first_email = mail.fetch(data[0].split()[-1], '(RFC822)')

  for r in first_email:
    if isinstance(r, tuple):
      message = email.message_from_bytes(r[1])
    if message.is_multipart():
      content = message.get_payload()[0].get_payload()
    else:
      content = message.get_payload()
    sending_email = message['from']
  try:
    token = re.search(".*Token: (.*)\\r", content).group(1)
    break
  except:
    continue 

driver.set_window_size(600, 700)
# Authorize with Token
driver.find_element(By.XPATH,'//input[@placeholder="Enter the emailed token"]').clear()
time.sleep(0.5)
driver.find_element(By.XPATH,'//input[@placeholder="Enter the emailed token"]').send_keys(token)
time.sleep(0.9)
driver.find_element(By.XPATH,'//input[@placeholder="Login"]').clear()
time.sleep(0.5)
driver.find_element(By.XPATH,'//input[@placeholder="Login"]').send_keys("jkerr@evconnect.com")
time.sleep(0.6)
try:
  driver.find_element(By.XPATH,'//button[text()="Authorize Device"]').click()
except:
  time.sleep(2)
  driver.find_element(By.XPATH,'//button[text()="Authorize Device"]').click()
time.sleep(0.6)
driver.set_window_size(1400, 820)

# Login Again
driver.find_element(By.XPATH,'//input[@placeholder="Login"]').clear()
time.sleep(0.2)
driver.find_element(By.XPATH,'//input[@placeholder="Login"]').send_keys("jkerr@evconnect.com")
time.sleep(0.2)
driver.find_element(By.XPATH,'//input[@placeholder="Password"]').send_keys("49856")
time.sleep(0.4)
driver.find_element(By.XPATH,'//button[@type="submit"]').click()
time.sleep(4.1)

# Screenshot what's going on
driver.save_screenshot('screenie.png')

# Prepare Download
try:
  driver.find_element(By.XPATH,'//button[@id="dropdownMenuButton"]').click() 
  time.sleep(0.8)
  driver.find_element(By.XPATH,'//a[@class="dropdown-item" and text()="Rebate Program"]').click() 
  time.sleep(0.7)
except:
  print('Still didnt work')

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': 'screen1e.png',
                'parents':['1DdTC37ao2EK23f-dnQ5Tj9EvgoS9BaIW']}
media = MediaFileUpload('screenie.png',
                        mimetype='image/png')
file = ggl_drive.files().create(body=file_metadata, 
                                media_body=media,
                              fields=returned_fields).execute()

