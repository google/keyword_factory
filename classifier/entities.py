# Slim versions of entitis used in backend, to be used
# by the GCF

import yaml
import re
from yaml.loader import SafeLoader
from google.cloud import storage
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Any, Dict
from datetime import datetime
from googleapiclient.errors import HttpError

_CONFIG_FILE_NAME = 'config_v2.yaml'
_HEADER = ['Keyword', 'Full Category Path', 'Top Level', 'Bottom Level', 'Confidence']
_RUN_DATETIME = datetime.now()
_RUN_METADATA = f'Last run was completed on {_RUN_DATETIME}'
_OUTPUT_SHEET = 'Output'
_SHEETS_SERVICE_SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']

class SheetsInteractor:
    def __init__(self, service, spreadsheet_url):
        self.service = service.spreadsheets()
        self.spreadsheet_url = spreadsheet_url
        self.spreadsheet_id = self._get_spreadsheet_id()

    def _get_spreadsheet_id(self) -> str:
        # Returns spreadsheet ID from spreadsheet URL
        if not self.spreadsheet_url:
            raise Exception(
                "No spreadsheet URL found. Follow instructions in README and add spreadsheet URL in config.yaml")

        spreadsheet_regex = '/d/(.*?)/edit'
        spreadsheet_match = re.search(spreadsheet_regex, self.spreadsheet_url)

        if spreadsheet_match == None:
            raise Exception("Couldn't extract spreadsheet ID from URL.")

        spreadsheet_id = spreadsheet_match.group(1)
        return spreadsheet_id


    def write_to_sheet(self, values, sheet=_OUTPUT_SHEET):
        self._clear_sheet(sheet)
        range = sheet + '!A1:' + chr(len(values[0]) + 65) + str(len(values))
        body = {
            'values': values
        }
        self.service.values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range,
            valueInputOption='RAW',
            body=body             
        ).execute()

    def read_from_spreadsheet(self, range, sheet=_OUTPUT_SHEET) -> List[List[Any]]:
        range = _OUTPUT_SHEET + "!" + range
        results = self.service.values().get(
            spreadsheetId=self.spreadsheet_id, range=range).execute()
        values = results.get('values', [])
        return values

    def _clear_sheet(self, sheet_name):
        """Helper function to clear output sheet before writing to it."""
        range_name = sheet_name + '!A:Z'
        self.service.values().clear(
            spreadsheetId=self.spreadsheet_id, range=range_name, body={}).execute()


def format_data_for_sheet(data: Dict[str, Dict[str, Any]]) -> List[List[Any]]:
    """ Gets a dict with recommendations and categorizations and formats 
    it to be writable to spreadsheet"""
    
    values = [_HEADER]
    for kw, cat_info in data.items():
        full_cat = cat_info.get('full category', '')
        conf = cat_info.get('confidence', '')
        if full_cat:
            top_cat = full_cat.split('/')[1]
            bottom_cat = full_cat.split('/')[-1]
        else:
            top_cat = ''
            bottom_cat = ''
            
        values.append([kw, full_cat, top_cat, bottom_cat, conf])        

    return values


class Config():
    """Represents and holds a config file"""
    def __init__(self, bucket_name):
        config = self._read_config_file(bucket_name)
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.refresh_token = config['refresh_token']
        self.spreadsheet_url = config['spreadsheet_url']

    def _read_config_file(self, bucket_name):
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)       
        try:
            blob = bucket.blob(_CONFIG_FILE_NAME)
            with blob.open() as f:
                config = yaml.load(f, Loader=SafeLoader)
            return config
        except Exception as e:
            raise FileNotFoundError
    
    def get_sheets_service(self):
        creds = None
        user_info = {
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
            "client_secret": self.client_secret
        }
        creds = Credentials.from_authorized_user_info(user_info, _SHEETS_SERVICE_SCOPES)

        # If credentials are expired, refresh.
        if creds.expired:
            creds.refresh(Request())

        service = build('sheets',
                        'v4', credentials=creds)
        return service