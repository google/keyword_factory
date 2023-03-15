# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from utils.config import Config
from utils.ads_searcher import RecBuilder, KeywordRemover
from utils.sheets import SheetsInteractor, create_new_spreadsheet, format_data_for_sheet
from concurrent import futures
from typing import List, Dict
from google.ads.googleads.client import GoogleAdsClient
from pathlib import Path
import logging
import requests
import os

_LOGS_PATH = Path('./server.log')
_CLASSIFIER_URL = os.getenv('cf_uri')

logging.basicConfig(filename=_LOGS_PATH,
                    level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')


def get_recommendations(client: GoogleAdsClient, accounts: List[str]):
    # Get KW recommendations from all accounts asynchronously
    kw_rec = []
    with futures.ThreadPoolExecutor() as executor:
        results = executor.map(
            lambda account: RecBuilder(
                client, account).build(),
            accounts)
    for res in results:
        if isinstance(res, list):
            kw_rec += res
    
    # Remove duplicates and return
    return list(dict.fromkeys(kw_rec))


def remove_keywords(client: GoogleAdsClient, recommendations: List[str], accoutns: List[str]):
    """Get all KWs from an account and remove duplicates from recommendations.
    Gets a list of the existing keywords in the given account, iterates over them
    and removes matches in the keyword recommendations dict.
    Args:
      client: Google Ads API client instance.
      recommendations: A list with all the KW recommendations.
      accounts: A list with all the selected accounts.
    """
    for account in accoutns:
        try:
            builder = KeywordRemover(client, account)
            builder.build(recommendations)
        except Exception as e:
            logging.exception(e)


def classify_keywords(kws) -> Dict[str, Dict[str, str]]:
    """ Classifys the list of keywords, using GCP NLP classification service.
    Args: List[str]
        list of keywords to categorize
    Returns: 
        a dict with the keyword as key - full categorization and confidence score """
    response = requests.post(_CLASSIFIER_URL, json={"kws": kws})
    return response.json()


def run(config: Config, accounts: List[str], run_type: str, uploaded_kws=[]):
    client = config.get_ads_client()
    sheets_service = config.get_sheets_service()
    if not config.spreadsheet_url:
        config.spreadsheet_url = create_new_spreadsheet(sheets_service)
        config.save_to_file()

    sheets_interactor = SheetsInteractor(sheets_service, config.spreadsheet_url)

    if run_type == "Full Run":
        kws = get_recommendations(client, accounts)
    elif run_type == "Filter":
        kws = uploaded_kws
    
    # Remove empty string if exists
    try:
        kws.remove('')
    except ValueError:
        pass

    
    try:
        # Dedup existing keywords
        remove_keywords(client, kws, accounts)
        # Categorize
        classified_kws = classify_keywords(kws)
        print(classify_keywords)
        # Write to spreadsheet
        sheets_interactor.write_to_sheet(values=format_data_for_sheet(classified_kws))
    except Exception as e:
        logging.exception(e)


