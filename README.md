# coaching-automation
Wilton Coaching Automation

## Virtual Env
python3 -m venv .venv
source .venv/bin/activate

## Install dependencies
pip install -r requirements.txt

## Create a application using pyinstaller - emailing recommendation
pyinstaller --onefile --windowed --add-data "config/email_password.txt:config" recommendation-email-automation.py

