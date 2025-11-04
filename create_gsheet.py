import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from property_level_analysis import address_data_to_gsheet


address_string = "7236 S Bell St"
datetime_string = "2025-10-28"

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  sheet_body = {
    "properties": {
      "title": "Test Spreadsheet"
    },
    "sheets": [
      {
        "properties": {
          "title": "Test Sheet"
        }
      }
    ]
  }

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets().create(body=sheet_body).execute()

    print(f"Spreadsheet created: {sheet.get("spreadsheetUrl")}")

    spreadsheet_id = sheet.get("spreadsheetId")

    address_dict = address_data_to_gsheet(address_string, datetime_string)

    column_list = []
    first_row_values_list = []
    for key, value in address_dict.items():
      column_list.append(key)
      first_row_values_list.append(value)

    values = [
      column_list,
      first_row_values_list
    ]

    range_string = "Test Sheet!A1:AZ3"

    value_range = {
      "values": values
    }

    result = service.spreadsheets().values().update(
      spreadsheetId = spreadsheet_id,
      range = range_string,
      valueInputOption = "RAW",
      body = value_range
    ).execute()

    print(f"{result.get('updatedCells')} cells updated.")


  except HttpError as err:
    print(err)


if __name__ == "__main__":
  main()