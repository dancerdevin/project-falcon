from os import path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

"""
Connect to Google Sheets API and instantiate Google Sheet object for creation.
"""

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Google Sheets API parameters
API_NAME = "sheets"
API_VERSION = "v4"


class GoogleSheetsAPIClient:
  """Build Google Sheets API client."""
  def __init__(self):
    self.creds = None
    self.client = None
    # TODO: Simplify initialization and defer build_client() outside of __init__()
    self.build_client()

  def build_and_store_creds(self):
    """From API quickstart: check for valid credentials and, if none, build and store."""
     # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if path.exists("token.json"):
      self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not self.creds or not self.creds.valid:
      if self.creds and self.creds.expired and self.creds.refresh_token:
        self.creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        self.creds = flow.run_local_server(port=0)

      # Save the credentials for the next run
      with open("token.json", "w") as token:
        token.write(self.creds.to_json())

  def build_client(self):
    if not self.creds:
      self.build_and_store_creds()

    try:
      self.client = build(API_NAME, API_VERSION, credentials=self.creds)

    except HttpError as err:
      print("Error when attempting to build Google Sheets API client: \n")
      print(err)