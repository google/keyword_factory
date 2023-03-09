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

_HEADER = ['keyword', 'account name', 'account id', 'campaign name',
           'campaign id', 'adgroup name', 'adgroup id','prominent adgroup', 'clicks', 'impressions', 'conversions', 'cost', 'ctr']
_RUN_DATETIME = datetime.now()
_RUN_METADATA = f'Last run was completed on {_RUN_DATETIME}'
_OUTPUT_SHEET = 'Output'
_SS_NAME = 'SeaTerA'

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

    def write_to_spreadsheet(self, ouput: Dict[str, Dict[Any, Any]]):
        data = []
        for sheet, values in ouput.items():
            self._clear_sheet(sheet)
            range = sheet + '!A1:' + \
                chr(len(values[0]) + 65) + str(len(values))
            data.append({'range': range, 'values': values})

        body = {'data': data, 'valueInputOption': "USER_ENTERED"}
        try:
            result = self.service.values().batchUpdate(
                spreadsheetId=self.spreadsheet_id, body=body).execute()
            logging.info(
                f"{(result.get('totalUpdatedRows') -4)} Rows updated.")
            return result
        except HttpError as e:
            logging.exception(e)
            return e
        
    def write_to_spreadsheet_single_column(self, output: List[str]):
        # Temp sheets writer
        formatted_output_list_of_lists = [[i] for i in output]
        self._clear_sheet(_OUTPUT_SHEET)
        range = _OUTPUT_SHEET + '!A1:A' + str(len(output))
        body = {'values': formatted_output_list_of_lists}
        result = self.service.values().update(
            spreadsheetId=self.spreadsheet_id, range=range,
            valueInputOption='USER_ENTERED', body=body).execute()

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

