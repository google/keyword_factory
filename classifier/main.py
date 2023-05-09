import functions_framework
import itertools
from classifier import Classifier
from entities import format_data_for_sheet, SheetsInteractor, Config

@functions_framework.http
def classify(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
    """

    request_json = request.get_json()
    bucket_name = request_json['bucket_name']
    row_num = request_json['row_num']

    config = Config(bucket_name)
    sheet_service = config.get_sheets_service()
    sheets_interactor = SheetsInteractor(sheet_service, config.spreadsheet_url)
    
    range = "A1:A" + str(row_num)
    kws = sheets_interactor.read_from_spreadsheet(range) 
    results = Classifier().classify_list(list(itertools.chain.from_iterable(kws)))
    sheets_interactor.write_to_sheet(format_data_for_sheet(results))
    
    # TODO: Add try except and reponde accordingly 
    return 200