import pandas as pd
import os
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Escape the backslashes
coach_documents_path = "C:/Users/Otto/OneDrive/Tennis/Automation/files/coach-doc-overview/Coach Documents Overview Sheet.xlsx"
course_type_to_check = ["lta accreditation", "dbs expiry date", "pediatric fa", "first aid", "safeguarding"]
to_expiring_email_addresses = ["headcoach@wiltontennisclub.co.uk"]
to_epired_email_addresses = ["headcoach@wiltontennisclub.co.uk", "info@wiltontennisclub.co.uk", "coachingadmin@wiltontennisclub.co.uk"]
main_check_sheet_names = ["Program","Assistant"]
tennis_leader_course_check = ["dbs expiry date"]
tennis_leader_sheet_name = ["Tennis Leaders"]

# Check if the file exists
if not os.path.exists(coach_documents_path):
    print(f"File does not exist: {coach_documents_path}")
    sys.exit(1)

def send_email(to, cc, subject, body):
    from_email = "headcoach@wiltontennisclub.co.uk"
    password = "vmpm entp wbib oyck"

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

def accreditation_status(accreditation_date):
    today = pd.Timestamp(datetime.now())
    one_month_ago = today - relativedelta(months=1)

    if pd.isna(accreditation_date):
        return "invalid date"
    elif one_month_ago <= accreditation_date <= today:
        return "expired within the last month"
    elif accreditation_date < one_month_ago:
        return "expired more than a month ago"
    elif accreditation_date - today <= pd.Timedelta(days=90):
        return "expiring"
    else:
        return "valid"

def get_expiring_documents(coach_documents_pd, course_type_to_check):
    coach_documents_pd[course_type_to_check] = pd.to_datetime(coach_documents_pd[course_type_to_check], format='%d/%m/%Y', errors='coerce')
    coach_documents_course_type = coach_documents_pd[["name", "qualification", "email address", course_type_to_check]].copy()
    coach_documents_course_type["expiry_flag"] = coach_documents_course_type[course_type_to_check].apply(accreditation_status)
    expiring_course = coach_documents_course_type[coach_documents_course_type["expiry_flag"] == "expiring"]
    expired_course = coach_documents_course_type[coach_documents_course_type["expiry_flag"] == "expired within the last month"]

    return expiring_course, expired_course


for sheet_name in tennis_leader_sheet_name:

    # Read the coach documents overview sheet
    coach_documents_pd = pd.read_excel(coach_documents_path, sheet_name=sheet_name, skiprows=1, header=0)

    # Remove trailing white space and make the columns lower case and remove new line and make double or more spaces single
    coach_documents_pd.columns = coach_documents_pd.columns.str.lower().str.strip().str.replace("\n", " ").str.replace("  ", " ")

    coach_documents_pd['date of birth'] = pd.to_datetime(coach_documents_pd['date of birth'])

    # Calculate the date when they turned 16
    coach_documents_pd['date_turned_16'] = coach_documents_pd['date of birth'] + pd.DateOffset(years=16)

    # Get the current date
    current_date = datetime.now()

    # Determine if the current date is within the first month after turning 16
    coach_documents_pd['first_month_16'] = coach_documents_pd['date_turned_16'].apply(
        lambda x: x <= current_date < x + timedelta(days=30)
    )

    # Display the resulting DataFrame
    print(coach_documents_pd)

    ## Create a new df where the first_month_16 column is True
    tennis_leaders_to_notify = coach_documents_pd[coach_documents_pd['first_month_16'] == True]

    # Send emails to the filtered coaches
    for index, coach in tennis_leaders_to_notify.iterrows():
        name = row['name']
        email = "ottosterner1@icloud.com"
        cc_address = ["ottosterner1@gmail.com"]
        #email = row['email address']
        #cc_address = to_expiring_email_addresses
        subject = f"DBS Registration Reminder"
        body = f"""Dear Parent of {name},

{name} has recently turned 16 and is now eligible to complete a DBS check to coach at Wilton Tennis Club. Please complete this as soon as possible.

Once you've done this, please send a copy of your certificate to headcoach@wiltontennisclub.co.uk and CC in coachingadmin@wiltontennisclub.co.uk.

Kind regards,
Marc Beckles, Head Coach"""
        send_email(email, cc_address, subject, body)


for sheet_name in main_check_sheet_names:
    # Read the coach documents overview sheet
    coach_documents_pd = pd.read_excel(coach_documents_path, sheet_name=sheet_name, skiprows=1, header=0)

    # Remove trailing white space and make the columns lower case and remove new line and make double or more spaces single
    coach_documents_pd.columns = coach_documents_pd.columns.str.lower().str.strip().str.replace("\n", " ").str.replace("  ", " ")

    for course_type in course_type_to_check:
        expiring_course_dataframe, expired_course_dataframe = get_expiring_documents(coach_documents_pd, course_type)

        for index, row in expiring_course_dataframe.iterrows():
            name = row['name']
            email = "ottosterner1@icloud.com"
            cc_address = ["ottosterner1@gmail.com"]
            #email = row['email address']
            #cc_address = to_expiring_email_addresses
            expiry_date = row[course_type].strftime('%d/%m/%Y')
            subject = f"REMINDER: {course_type.replace('_', ' ').title()} Expiring Soon"
            body = f"""Dear {name},

Your {course_type.replace('_', ' ').title().lower()} is expiring on {expiry_date}. You've got until this date to get a new one, we suggest you book on this course ASAP as your certificate needs to be renewed by this date to coach at Wilton Tennis Club. 

Once you've done this, please send a copy of your certificate to headcoach@wiltontennisclub.co.uk and CC in coachingadmin@wiltontennisclub.co.uk.

Kind regards,
Marc Beckles, Head Coach"""
            send_email(email, cc_address, subject, body)

        for index, row in expired_course_dataframe.iterrows():        
            name = row['name']
            email = "ottosterner1@icloud.com"
            cc_address = ["ottosterner1@gmail.com"]
            #email = row['email address']
            #cc_address = to_expired_email_addresses
            expiry_date = row[course_type].strftime('%d/%m/%Y')
            subject = f"NOTICE: {course_type.replace('_', ' ').title()} Expired"
            body = f"""Dear {name},

Your {course_type.replace('_', ' ').title().lower()} expired on {expiry_date}. You can no longer coach at Wilton Tennis Club until you renew your certificate.

Please renew your certificate and send a copy to headcoach@wiltontennisclub.co.uk and CC in coachingadmin@wiltontennisclub.co.uk.

Kind regards,
Marc Beckles, Head Coach"""
            send_email(email, cc_address, subject, body)

        print(expiring_course_dataframe)
        print(expired_course_dataframe)







