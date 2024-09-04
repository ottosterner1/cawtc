from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

print("Hello")


def download_excel_file(drive, file_id, output_file):
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(output_file, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def authenticate_drive():
    gauth = GoogleAuth()
    
    # Ensure this path is correct and the file exists
    settings_file = 'config/client_secrets.json'
    credentials_file = 'config/my_credentials.json'
    
    if not os.path.exists(settings_file):
        raise FileNotFoundError(f'Client secrets file not found: {settings_file}')
    
    # Load client configuration from file
    try:
        gauth.LoadClientConfigFile(settings_file)
    except Exception as e:
        raise ValueError(f'Failed to load client config file: {e}')
    
    # Load saved credentials
    try:
        gauth.LoadCredentialsFile(credentials_file)
    except Exception as e:
        raise ValueError(f'Failed to load credentials file: {e}')
    
    # Check if credentials are missing or expired
    if gauth.credentials is None or gauth.credentials.access_token_expired:
        if gauth.credentials is None:
            print("No credentials found. Starting authentication.")
        elif gauth.credentials.access_token_expired:
            print("Credentials expired. Refreshing token.")
        
        try:
            gauth.LocalWebserverAuth()  # This will open a browser window for authentication
            gauth.SaveCredentialsFile(credentials_file)
        except Exception as e:
            raise RuntimeError(f'Failed to authenticate or save credentials: {e}')
    
    return GoogleDrive(gauth)