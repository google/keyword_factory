import functions_framework
import itertools
import logging
import os
from classifier import Classifier
from entities import format_data_for_sheet, SheetsInteractor, Config

logging.basicConfig(level=logging.INFO)

@functions_framework.http
def classify(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        The request object should be a dict that holds one parameter: row_num
        row_num should be either empty string or a string number.
        If empty - it will read all rows up until last row with data.
    """
    request_json = request.get_json()
    config_path = os.getenv('config_path') or 'config.yaml'
    row_num = request_json['row_num']

    try:
        config = Config(config_path)
        sheet_service = config.get_sheets_service()
        sheets_interactor = SheetsInteractor(sheet_service, config.spreadsheet_url)
        
        read_range = "A2:A" + str(row_num)
        kws = sheets_interactor.read_from_spreadsheet(read_range) 
        results = Classifier().classify_list(list(itertools.chain.from_iterable(kws)))
        sheets_interactor.write_to_sheet(format_data_for_sheet(results))
        
        return '200'

    except Exception as e:
        logging.error(str(e))
        return '500'