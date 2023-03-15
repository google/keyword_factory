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

from yaml.loader import SafeLoader
from copy import deepcopy
from google.cloud import storage
from google.ads.googleads.client import GoogleAdsClient
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import Dict
import os
import yaml


BUCKET_NAME = os.getenv('bucket_name')
CONFIG_FILE_NAME = 'config.yaml'
CONFIG_FILE_PATH = BUCKET_NAME +  '/' + CONFIG_FILE_NAME
_ADS_API_VERSION = 'v11'

SHEETS_SERVICE_SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']

class Config:
    def __init__(self) -> None:
        self.file_path = CONFIG_FILE_PATH
        self.storage_client = storage.Client.from_service_account_json('./key.json')
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        config = self.load_config_from_file()
        if config is None:
            config = {}

        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret')
        self.refresh_token = config.get('refresh_token', '')
        self.developer_token = config.get('developer_token', '')
        self.login_customer_id = config.get('login_customer_id', '')
        self.spreadsheet_url = config.get('spreadsheet_url', '')

        self.check_valid_config()

    def check_valid_config(self):
        if self.client_id and self.client_secret and self.refresh_token and self.developer_token and self.login_customer_id:
            self.valid_config = True
        else:
            self.valid_config = False

    def load_config_from_file(self):
        try:
            blob = self.bucket.blob(CONFIG_FILE_NAME)
            with blob.open() as f:
                config = yaml.load(f, Loader=SafeLoader)
        except Exception as e:
            return None
        return config

    def save_to_file(self):
        try:
            config = deepcopy(self.to_dict())
            blob = self.bucket.blob(CONFIG_FILE_NAME)
            with blob.open('w') as f:
                yaml.dump(config, f)
            print(f"Configurations updated in {self.file_path}")
        except Exception as e:
            print(f"Could not write configurations to {self.file_path} file")
            print(e)

    def to_dict(self) -> Dict[str, str]:
        """ Return the core attributes of the object as dict"""
        return {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "developer_token": self.developer_token,
                "login_customer_id": self.login_customer_id,
                "spreadsheet_url": self.spreadsheet_url
        }

    def get_ads_client(self):
        return GoogleAdsClient.load_from_dict({
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'login_customer_id': self.login_customer_id,
            'developer_token': self.developer_token,
            'refresh_token': self.refresh_token,
            'use_proto_plus': True,
        }, version=_ADS_API_VERSION)

    def get_sheets_service(self):
        creds = None
        user_info = {
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
            "client_secret": self.client_secret
        }
        creds = Credentials.from_authorized_user_info(user_info, SHEETS_SERVICE_SCOPES)

        # If credentials are expired, refresh.
        if creds.expired:
            creds.refresh(Request())

        service = build('sheets',
                        'v4', credentials=creds)
        return service