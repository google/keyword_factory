# Copyright 2023 Google LLC
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
import smart_open as smart_open
import logging

_ADS_API_VERSION = 'v14'
_CONFIG_SUFFIX = '-keyword_factory/config.yaml'
SHEETS_SERVICE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file', 
    'https://www.googleapis.com/auth/drive'
    ]

class Config:
    def __init__(self, ok_if_not_exists = False) -> None:

        self.file_path = self._config_file_path_set()
        config = self.load_config_from_file(ok_if_not_exists)
        if config is None:
            config = {}

        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret')
        self.refresh_token = config.get('refresh_token', '')
        self.developer_token = config.get('developer_token', '')
        self.login_customer_id = config.get('login_customer_id', '')
        self.spreadsheet_url = config.get('spreadsheet_url', '')

        self.check_valid_config()

    def _config_file_path_set(self):
        file_path = ''
        try:
            client = storage.Client()
            project_id = client.project
            file_path = project_id + _CONFIG_SUFFIX
        except:
            file_path = 'config.yaml'
        return file_path
    
    def check_valid_config(self):
        if self.client_id and self.client_secret and self.refresh_token and self.developer_token and self.login_customer_id:
            self.valid_config = True
        else:
            self.valid_config = False


    def load_config_from_file(self, ok_if_not_exists = False) -> dict:
        config_file_path = self.file_path
        try:
            with smart_open.open(config_file_path, "rb") as f:
                content = f.read()
        except BaseException as e:
            logging.error(f"Config file {config_file_path} was not found: {str(e)}")
            if ok_if_not_exists:
              return {}
            raise FileNotFoundError(config_file_path)
        try:
            config = yaml.load(content, Loader=SafeLoader)
        except BaseException as e:
            logging.error(f"Failed to parse config file {config_file_path}: {str(e)}")
            if ok_if_not_exists:
              return {}
            raise e
        return config


    def save_to_file(self):
        try:
            with smart_open.open(self.file_path, 'w') as f:
                yaml.dump(self.to_dict(), f)
            logging.info(f"Configurations updated in {self.file_path}")
        except Exception as e:
            logging.error(f"Could not write configurations to {self.file_path} file: {str(e)}")
            raise e


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
        user_info = {
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
            "client_secret": self.client_secret
        }
        creds = Credentials.from_authorized_user_info(user_info, SHEETS_SERVICE_SCOPES)

        # If credentials are expired, refresh.
        if creds.expired:
            creds.refresh(Request())

        service = build('sheets', 'v4', credentials=creds)
        return service