# Google Drive Read-Only Unlocker

This tool allows you to extract text from Google Docs that have been set to "View Only" and have copying/downloading disabled.

## Requirements
- Python 3
- `requests`
- `beautifulsoup4`

## Setup
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the script and provide the URL of the restricted Google Doc:

```bash
python3 drive_unlocker.py "https://docs.google.com/document/d/YOUR_DOC_ID/edit"
```

The script will automatically:
1. Bypass the copy restriction.
2. Extract the text.
3. Save it to a file named `unlocked_YOUR_DOC_ID.txt`.

## Limitations
This tool works for documents shared as **"Anyone with the link can view"**. It cannot access private documents that require you to sign in to your Google account (unless you provide cookies/headers to the script, which is not implemented in this version).
