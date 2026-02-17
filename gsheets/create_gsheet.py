class GoogleSheet:
  """Initialize with Google Sheet schema and build Google Sheet."""
  def __init__(self, client, spreadsheet_title, sheet_one_title):
    # TODO: error handling to ensure client is connected and auth'd
    self.client = client
    self.sheet_one_title = sheet_one_title
    self.sheet_body = {
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
    
    # Create spreadsheet
    self.spreadsheet = self.client.spreadsheets().create(body=self.sheet_body).execute()

    print(f"Spreadsheet created: {self.spreadsheet.get("spreadsheetUrl")}")