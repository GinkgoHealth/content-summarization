from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import pandas as pd
import sys

def pull_from_Sheet(data=None, sheet_name='Master', cell_range='', 
    sheets_id_json='../content-summarization/notebooks/google_sheet_id.json',
    sheet_key='exercise_library_sheet',
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    ):
    """
    Pulls data from a Google Sheet using the Sheets API and returns a pandas dataframe.

    Args:
    - data: List of lists containing data to be converted to a dataframe (default None). 
        If data is provided, the Sheets API will not be called. otherwise, the Sheets API will be called.
    - sheet_name: The name of the sheet to pull data from (default 'Master').
    - cell_range: The range of cells to retrieve (default '').
    - sheets_id_json: The path to a JSON file containing the spreadsheet ID (default '../content-summarization/notebooks/google_sheet_id.json').
    - sheet_key: The key for the desired spreadsheet ID within the JSON file (default 'exercise_library_sheet').
    - SCOPES: The authentication scope to use 
        (default ['https://www.googleapis.com/auth/spreadsheets.readonly']).

    Returns:
    A pandas dataframe containing the data from the Google Sheet.

    See 2023-04-25 analyze prompt chain results notebook for usage.
    """
    if not data:
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(f'token.json'):
            creds = Credentials.from_authorized_user_file(f'token.json', SCOPES)
            print(f'token.json')
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    f'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(f'token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            print(creds)
            with open(sheets_id_json) as json_file:
                SPREADSHEET_ID = json.load(json_file)[sheet_key]
                # print(SPREADSHEET_ID)
            service = build('sheets', 'v4', credentials=creds)
            range = f'{sheet_name}!{cell_range}' if cell_range else sheet_name
            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                        range=range).execute()
            values = result.get('values', [])

            if not values:
                print('No data found.')
                return

            data = result.get('values')
            print(f"Complete: Data copied for {range} in spreadsheet")
            print(f'Number of rows: {len(data)}')
            try:
                print('Creating dataframe from existing data list')
                df = pd.DataFrame(data[1:], columns=data[0])
                
            except:
                try:
                    df = pd.DataFrame(data[1:])
                    print(f'Original columns: {[column for column in df.columns]}')
                    new_names = data[0]
                    print(f'Column name: {[column for column in new_names]}')
                    name_map = {col: new_names[i] if i < len(new_names) else f'Column {col}' for i, col in enumerate(df.columns)}

                    # Use the dictionary to rename the columns in the DataFrame
                    df = df.rename(columns=name_map)
                    print(f'Columns remapped')
                except Exception as error:
                    exc_type, exc_obj, tb = sys.exc_info()
                    f = tb.tb_frame
                    lineno = tb.tb_lineno
                    filename = f.f_code.co_filename
                    print("An error occurred on line", lineno, "in", filename, ":", error)
            return df
        except HttpError as err:
            print(err)
    else:
        print('Creating dataframe from existing data list')
        try:
            data = pd.DataFrame(data[1:], columns=data[0])
            # print(f'Columns: {[column for column in data.columns]}')
        except:
            try:
                df = pd.DataFrame(data[1:])
                print(f'Original columns: {[column for column in df.columns]}')
                new_names = data[0]
                print(f'Column name: {[column for column in new_names]}')
                name_map = {col: new_names[i] if i < len(new_names) else f'Column {col}' for i, col in enumerate(df.columns)}

                # Use the dictionary to rename the columns in the DataFrame
                df = df.rename(columns=name_map)
                print(f'Columns remapped')
            except Exception as error:
                exc_type, exc_obj, tb = sys.exc_info()
                f = tb.tb_frame
                lineno = tb.tb_lineno
                filename = f.f_code.co_filename
                print("An error occurred on line", lineno, "in", filename, ":", error)
        return df
    
def pull_kl_results(save=True,
    pickle_path=r'C:\Users\silvh\OneDrive\lighthouse\Ginkgo coding\content-summarization\output',
    csv_path=None
    ):
    """
    Get the most updated data from the 'prompt chain results' Google Sheet.
    
    Parameters:
        - save (bool): Whether or not to save the results as pickle/CSV. If True, 
            runs the `save_output` function.
        - pickle_path, csv_path (raw string): Where to save the results.

    Returns: DataFrame containing knowledge library prompt chain results.
    """
    kl_df = pull_from_Sheet(sheet_name='results', 
        sheets_id_json='google_sheet_id.json',
        sheet_key='prompt_chain_sheet')
    try:
        if save:
            save_output(kl_df, description='prompt_chain_results_sheet',
                pickle_path=pickle_path, csv_path=csv_path)
    except:
        print('Unable to save outputs')
    return kl_df