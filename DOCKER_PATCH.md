# Docker Compatibility Patch

This file contains the modifications needed to make the authentication function Docker-compatible.

## Required Change to `authenticate_gdrive()` function

Replace the existing `authenticate_gdrive()` function (lines ~36-70) with this Docker-compatible version:

```python
def authenticate_gdrive():
    """
    Authenticate with Google Drive API.
    Looks for credentials in the following order:
    1. token.pickle (saved credentials)
    2. credentials.json (OAuth client credentials)
    3. service-account.json (Service account credentials)
    
    Checks both current directory and /app/credentials (for Docker)
    """
    creds = None
    
    # Define possible credential paths (for Docker compatibility)
    credential_dirs = ['.', '/app/credentials']
    
    # Helper function to find file in credential directories
    def find_file(filename):
        for cred_dir in credential_dirs:
            filepath = os.path.join(cred_dir, filename)
            if os.path.exists(filepath):
                return filepath
        return None
    
    # Check for saved credentials
    token_path = find_file('token.pickle')
    if token_path:
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, try to authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Try service account first
            service_account_path = find_file('service-account.json')
            if service_account_path:
                print(f"Using service account authentication from: {service_account_path}")
                creds = service_account.Credentials.from_service_account_file(
                    service_account_path, scopes=SCOPES)
            else:
                # Try OAuth credentials
                credentials_path = find_file('credentials.json')
                if credentials_path:
                    print(f"Using OAuth authentication from: {credentials_path}")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    # Save credentials for future use
                    token_save_path = find_file('token.pickle') or 'token.pickle'
                    with open(token_save_path, 'wb') as token:
                        pickle.dump(creds, token)
                else:
                    raise FileNotFoundError(
                        "No credentials found! Please provide either:\n"
                        "1. credentials.json (OAuth) - Download from Google Cloud Console\n"
                        "2. service-account.json (Service Account) - Download from Google Cloud Console\n"
                        "Place credentials in ./credentials/ directory or current directory"
                    )
    
    return build('drive', 'v3', credentials=creds)
```

## What Changed?

1. **Added credential directory search**: The function now looks in both the current directory and `/app/credentials/` (Docker mount point)
2. **Added helper function**: `find_file()` searches multiple directories for credential files
3. **Better logging**: Shows which credential file is being used
4. **More helpful error message**: Mentions the `./credentials/` directory

## How to Apply

1. Open `radiology_report_generator.py`
2. Find the `authenticate_gdrive()` function
3. Replace it with the version above
4. Save the file

That's it! The script will now work both locally and in Docker.

## Alternative: Use sed to apply the patch

If you're comfortable with command-line tools, you can create a script to automatically apply this change, but manual replacement is recommended to avoid errors.
