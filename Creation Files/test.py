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

# Setup Connection
service = Service()
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
user_agent = 'Chrome/60.0.3112.50'
options.add_argument(f'user-agent={user_agent}')
driver = webdriver.Chrome(service=service, options=options)

# Access Website
driver.get('chrome://settings/downloads')

time.sleep(2)

driver.save_screenshot('screenie.png')

with open('screenie.png', 'rb') as content_file:
  file_content = content_file.read()

# Upload File
returned_fields="id, name, mimeType, webViewLink, exportLinks, parents"
file_metadata = {'name': creation_name+'.csv'}
media = MediaFileUpload('screenie.png',
                        mimetype='image/png')
file = ggl_drive.files().update(fileId='1JSa-KqrY3TnE9tyiUxoznbHPwL2JimqT',
                                body=file_metadata, 
                                media_body=media,
                              fields=returned_fields).execute()

