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

import re
import logging
from typing import List, Any, Dict
from datetime import datetime
from googleapiclient.errors import HttpError

_HEADER = ['Keyword', 'Full Category Path', 'Top Level', 'Bottom Level', 'Confidence']
_RUN_DATETIME = datetime.now()
_RUN_METADATA = f'Last run was completed on {_RUN_DATETIME}'
_OUTPUT_SHEET = 'Output'
_SS_NAME = 'Keyword Factory'

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

    def read_from_spreadsheet(self, range) -> List[List[Any]]:
        results = self.service.values().get(
            spreadsheetId=self.spreadsheet_id, range=range).execute()
        values = results.get('values', [])
        return values

    def _clear_sheet(self, sheet_name):
        """Helper function to clear output sheet before writing to it."""
        range_name = sheet_name + '!A:Z'
        self.service.values().clear(
            spreadsheetId=self.spreadsheet_id, range=range_name, body={}).execute()


def create_new_spreadsheet(sheet_service):
    spreadsheet_title = _SS_NAME
    sheets = []
    worksheet = {
        'properties': {
            'title': _OUTPUT_SHEET
        }
    }

    sheets.append(worksheet)
    spreadsheet = {
        'properties': {
            'title': spreadsheet_title
            },
        'sheets': sheets
    }
    ss = sheet_service.spreadsheets().create(body=spreadsheet,
                                            fields='spreadsheetUrl').execute()
    return ss.get('spreadsheetUrl')


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