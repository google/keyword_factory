from utils.config import Config
from utils.ads_searcher import RecBuilder, KeywordRemover
from utils.sheets import SheetsInteractor, create_new_spreadsheet
from concurrent import futures
from typing import List
from google.ads.googleads.client import GoogleAdsClient
from pathlib import Path
import logging

_LOGS_PATH = Path('./server.log')

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


# def _filter_run(client: GoogleAdsClient, accounts: List[str], uploaded_kws: List[str]):
#     remove_keywords(client, uploaded_kws, accounts)


# def _full_run(client: GoogleAdsClient, accounts: List[str]):
#     recommendations = get_recommendations(client, accounts)
#     remove_keywords(client, recommendations, accounts)
 

def run(config: Config, accounts: List[str], run_type: str, uploaded_kws=[]):
    client = config.get_ads_client()
    sheets_service = config.get_sheets_service()
    if not config.spreadsheet_url:
        config.spreadsheet_url = create_new_spreadsheet(sheets_service)
        config.save_to_file()

    sheets_interactor = SheetsInteractor(sheets_service, config.spreadsheet_url)

    if run_type == "Full Run":
        # _full_run(client, accounts)
        kws = get_recommendations(client, accounts)
    elif run_type == "Filter":
        # _filter_run(client, accounts, uploaded_kws)
        kws = uploaded_kws
    
    sheets_interactor.write_to_spreadsheet_single_column(kws)

