import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-this'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tennis.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'

    
    # AWS Cognito Config
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_COGNITO_REGION = os.environ.get('AWS_COGNITO_REGION')
    AWS_COGNITO_USER_POOL_ID = os.environ.get('AWS_COGNITO_USER_POOL_ID')
    AWS_COGNITO_CLIENT_ID = os.environ.get('AWS_COGNITO_CLIENT_ID')
    AWS_COGNITO_CLIENT_SECRET = os.environ.get('AWS_COGNITO_CLIENT_SECRET')
    COGNITO_DOMAIN = os.environ.get('COGNITO_DOMAIN')
    
    # OAuth endpoints
    OAUTH_AUTHORIZE_URL = f"https://{COGNITO_DOMAIN}/oauth2/authorize"
    OAUTH_TOKEN_URL = f"https://{COGNITO_DOMAIN}/oauth2/token"
    OAUTH_USERINFO_URL = f"https://{COGNITO_DOMAIN}/oauth2/userInfo"
    
    # Metadata URL
    COGNITO_METADATA_URL = f'https://cognito-idp.{AWS_COGNITO_REGION}.amazonaws.com/{AWS_COGNITO_USER_POOL_ID}/.well-known/openid-configuration'
    
    # OAuth client configuration
    OAUTH_CLIENT_KWARGS = {
        'scope': 'email openid profile',
        'response_type': 'code'
    }

    def __init__(self):
        print(f"Cognito Domain: {self.COGNITO_DOMAIN}")