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

  spreadsheet_title = "BatchUpdate Test Spreadsheet with Colors CLEANED"
  sheet_one_title = "Test Sheet"

  sheet_body = {
    "properties": {
      "title": spreadsheet_title
    },
    "sheets": [
      {
        "properties": {
          "title": sheet_one_title
        }
      }
    ]
  }

  try:
    service = build("sheets", "v4", credentials=creds)

    # Create spreadsheet
    spreadsheet = service.spreadsheets().create(body=sheet_body).execute()

    print(f"Spreadsheet created: {spreadsheet.get("spreadsheetUrl")}")

    spreadsheet_id = spreadsheet.get("spreadsheetId")

    address_dict = address_data_to_gsheet(address_string, datetime_string)

    # Populate spreadsheet with values using spreadsheet.values().batchUpdate()
    column_list = []
    first_row_values_list = []
    for key, value in address_dict.items():
      column_list.append(key)
      first_row_values_list.append(value)

    # Dynamically map ranges and values to body data
    ranges = [
      (sheet_one_title + "!A1:AZ1", column_list),
      (sheet_one_title + "!A2:AZ2", first_row_values_list)
    ]

    values_body = {
      "valueInputOption": "RAW",
      "data": [
        {"range": range, "values": [values]} for range, values in ranges
      ]
    }

    service.spreadsheets().values().batchUpdate(
      spreadsheetId = spreadsheet_id,
      body = values_body
    ).execute()
    print("spreadsheets.values.batchUpdate executed.")

    # Format spreadsheet using spreadsheet.batchUpdate(). First get sheet ID
    sheet_id = None
    
    for sheet in spreadsheet["sheets"]:
      if sheet["properties"]["title"] == sheet_one_title:
        sheet_id = sheet["properties"]["sheetId"]
    if sheet_id is None:
      raise Exception("Error: No match with sheet title found.")

    format_body = {
      "requests": [
        {
          "repeatCell": {
            "range": {
              "sheetId": sheet_id,
              "startRowIndex": 0,
              "endRowIndex": 1
            },
            "cell": {
              "userEnteredFormat": {
                "backgroundColor": {"green": 1},
                "textFormat": {
                  "foregroundColor": {"blue": 1}
                }
              }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat.foregroundColor)"
          },
        }
      ]
    }

    service.spreadsheets().batchUpdate(
      spreadsheetId = spreadsheet_id,
      body = format_body
    ).execute()
    print("spreadsheets.batchUpdate executed.")


  except HttpError as err:
    print(err)


if __name__ == "__main__":
  main()