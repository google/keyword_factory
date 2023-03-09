from utils.config import Config
from utils.ads_searcher import MccBuilder
from typing import List

def get_all_child_accounts(config: Config):
    google_ads_client = config.get_ads_client()
    accounts = MccBuilder(google_ads_client).get_accounts(with_names=False)
    return accounts

def get_account_labels(config: Config):
    google_ads_client = config.get_ads_client()
    labels = MccBuilder(google_ads_client).get_labels()
    return labels

def get_accounts_by_labels(config: Config, labels: List[str]):
    google_ads_client = config.get_ads_client()
    accounts = MccBuilder(google_ads_client).get_accounts_by_label(labels)
    return accounts