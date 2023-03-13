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
from utils.ads_searcher import MccBuilder
from typing import List

def get_all_child_accounts(config: Config, with_names: bool = False):
    google_ads_client = config.get_ads_client()
    accounts = MccBuilder(google_ads_client).get_accounts(with_names=with_names)
    return accounts

def get_account_labels(config: Config):
    google_ads_client = config.get_ads_client()
    labels = MccBuilder(google_ads_client).get_labels()
    return labels

def get_accounts_by_labels(config: Config, labels: List[str]):
    google_ads_client = config.get_ads_client()
    accounts = MccBuilder(google_ads_client).get_accounts_by_label(labels)
    return accounts