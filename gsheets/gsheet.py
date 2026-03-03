class GoogleSheet:
  """Initialize with Google Sheet client and build Google Sheet."""
  def __init__(self, client, spreadsheet_title, sheet_one_title):
    # TODO: error handling to ensure client is connected and auth'd
    self.client = client
    self._sheet_one_title = sheet_one_title
    self._sheet_body = {
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
    
    # TODO: Simplify complicated initialization (ensure idempotence)
    # Create spreadsheet
    self._spreadsheet = self.client.spreadsheets().create(body=self._sheet_body).execute()

    print(f"Spreadsheet created: {self._spreadsheet.get("spreadsheetUrl")}")