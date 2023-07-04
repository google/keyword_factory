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
import urllib
from google.auth import default
from google.cloud import functions_v2
import google.auth.transport.requests
import google.oauth2.id_token
import logging
import requests
import os
import json

_LOGS_PATH = Path('./server.log')
_CLASSIFIER_FUNCTION_NAME = os.getenv('cf_classifier_name') or "classifier-keyword-factory"

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


def get_current_location() -> str:
    """ Retrieve the current location of Cloud Run service """
    metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/region"
    metadata_headers = {"Metadata-Flavor": "Google"}
    response = requests.get(metadata_url, headers=metadata_headers)
    location = response.text.split('/')[-1]
    return location


def get_function_uri(name, location=None, project_id=None) -> str:
    """ Retrieve a Cloud function's uri by its name in a spacified region
      Args:
        name: a function name
        location: a function location, if None then the current service's location will be used
        project_id: a function project, if None then the current project will be used
      Return: uri - a uri for calling the function
    """
    functions_client = functions_v2.FunctionServiceClient()
    if not project_id:
        _, project_id = default()
    parent = f"projects/{project_id}"
    if not location:
        location = get_current_location()
    parent += f"/locations/{location}"
    response = functions_client.list_functions(request={"parent": parent})
    for function in response:
        if name == function.name.split("/")[-1]:
            url = function.service_config.uri
            return url


def classify_keywords(row_num) -> Dict[str, Dict[str, str]]:
    """ Classifys the list of keywords, using GCP NLP classification service.
    Args: row_num - number of rows to categorize from the spreadsheet
        List[str] of keywords to categorize
    """
    cf_uri = os.getenv('cf_uri')
    if not cf_uri:
        cf_uri = get_function_uri(_CLASSIFIER_FUNCTION_NAME)
    req = urllib.request.Request(cf_uri, method="POST")
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, cf_uri)
    req.add_header("Authorization", f"Bearer {id_token}")
    req.add_header('Content-Type', 'application/json')

    data = json.dumps({"row_num":str(row_num)})
    data = data.encode()
    response = urllib.request.urlopen(req,data=data)


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
        # Write to spreadsheet
        sheets_interactor.write_to_sheet(values=[[kw] for kw in kws])
        return len(kws)
    except Exception as e:
        logging.exception(e)

