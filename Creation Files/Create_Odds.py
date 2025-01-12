##################################################
###### Setup #####################################
##################################################

## -- Import Required Packages -- ##

import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import pandas as pd
import re
import numpy as np
import time
import pickle
import glob
import os
import matplotlib.pyplot as plt
import statsmodels.formula.api as sm
import statsmodels.api as SM
import math
from statsmodels.stats.outliers_influence import variance_inflation_factor
from datetime import datetime, date, timedelta
from datetime import time as datetime_time
from io import StringIO
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
