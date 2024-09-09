from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import pandas as pd

# Function definitions
def send_email(to, cc, subject, body):
    """
    This function sends an email to the specified recipient with the specified subject and body
    
    Arguments:
    to: str: The email address of the recipient
    cc: list: A list of email addresses to CC
    subject: str: The subject of the email
    body: str: The body of the email

    Returns:
    None
    """
    from_email = "headcoach@wiltontennisclub.co.uk"
    
    # Read the password from a file
    with open('config/email_password.txt', 'r') as file:
        password = file.read().strip()

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to
    msg['CC'] = ", ".join(cc)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, [to] + cc, text)
        server.quit()
        print(f"Email sent to {to}")
    except Exception as e:
        print(f"Failed to send email to {to}: {e}")
        exit()

def get_contacts(file_path, data_columns):
    """
    This function reads the contacts from the specified file and returns a dataframe
    
    Arguments:
    file_path: str: The path to the contacts file
    data_columns: list: A list of column names to read from the file

    Returns:
    contacts_df: DataFrame: A pandas DataFrame containing the contacts
    """
    try:
        contacts_df = pd.read_csv(file_path, usecols=data_columns)
    except Exception as e:
        print(f"Failed to read contacts from {file_path}: {e}")
        exit()

    return contacts_df

def loop_through_each_contact_send_email(contacts_df, mode):
    """
    This function loops through each contact in the contacts dataframe and sends an email
    
    Arguments:
    contacts_df: DataFrame: A pandas DataFrame containing the contacts
    mode: str: The mode of operation ('live' or 'self')

    Returns:
    None
    """

    
    for index, row in contacts_df.iterrows():
        full_name = row['full name']
        recommendation = row['recommendation']


        if mode == "self":
            email = "ottosterner1@gmail.com"
            cc_address = [""]
        else:
            email = row['email']
            cc_address = ["headcoach@wiltontennisclub.co.uk"]

        subject = f"TEST!: NEW RECOMMENDATION!"
        body = (
            f"Dear Parent or Guardion,\n\n"
            f"Your child {full_name} has a new recommendation for {recommendation}.\n\n"

            f"Kind regards,\n"
            f"Marc Beckles, Head Coach"
        )

        send_email(email, cc_address, subject, body)


# Main code
if __name__ == "__main__":
    CONTACTS_FILE_PATH = "data/contacts.csv"
    DATA_COLUMNS = ["full name", "email", "recommendation"]

    # Prompt the user for the mode
    mode = input("Would you like to run the reminders live or for yourself? (live/self): ").strip().lower()

    contacts_df = get_contacts(CONTACTS_FILE_PATH, DATA_COLUMNS)

    if mode == "live":
        print("Starting live run...")
        loop_through_each_contact_send_email(contacts_df, mode)
    elif mode == "self":
        print("Starting run for myself...")
        loop_through_each_contact_send_email(contacts_df, mode)
    else:
        print("Invalid mode selected. Please choose 'live' or 'self'.")