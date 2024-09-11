import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import sys

def get_resource_path(relative_path):
    """ Get the absolute path to a resource file. Handles PyInstaller paths. """
    try:
        # PyInstaller creates a temp folder and stores the path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Fallback to the current directory if not running as a PyInstaller executable
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Function definitions
def send_email(to, cc, subject, body):
    from_email = "headcoach@wiltontennisclub.co.uk"
    
    password_file = get_resource_path('config/email_password.txt')

    # Read the password from a file
    try:
        with open(password_file, 'r') as file:
            password = file.read().strip()
    except FileNotFoundError:
        messagebox.showerror("Error", "Password file not found!")
        exit()

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
        messagebox.showerror("Error", f"Failed to send email to {to}: {e}")
        exit()

def get_contacts(file_path, data_columns):
    try:
        contacts_df = pd.read_csv(file_path, usecols=data_columns)
    except Exception as e:
        print(f"Failed to read contacts from {file_path}: {e}")
        messagebox.showerror("Error", f"Failed to read contacts from {file_path}: {e}")
        return None
    return contacts_df

def loop_through_each_contact_send_email(contacts_df, mode):
    if contacts_df is None:
        return
    
    for index, row in contacts_df.iterrows():
        full_name = row['full name']
        recommendation = row['recommendation']

        # Check mode to determine email destination
        if mode == "live":
            email = row['email']
            cc_address = ["headcoach@wiltontennisclub.co.uk"]
        else:  # Test mode
            email = "ottosterner1@gmail.com"
            cc_address = [""]
        
        subject = f"{full_name} Group Recommendation for Next Term"
        body = (
            f"Dear Parent or Guardian,\n\n"
            f"Thank you for signing up your child for this term of coaching at Wilton Tennis Club.\n\n"
            f"{full_name} is recommended to sign up to the following group class for next term: {recommendation}.\n\n"
            f"Please let me know if you have any queries regarding this recommendation.\n\n"
            f"Kind regards,\n"
            f"Marc Beckles, Head Coach"
        )

        send_email(email, cc_address, subject, body)

def run_email_sending():
    global csv_file_path
    
    if csv_file_path == "":
        messagebox.showerror("Error", "Please select a CSV file first!")
        return

    # Confirm if mode is live
    if mode_var.get() == "live":
        confirm = messagebox.askyesno("Confirmation", "Are you sure you want to send emails in live mode?")
        if not confirm:
            return  # If the user cancels, stop the process

    contacts_df = get_contacts(csv_file_path, ["full name", "email", "recommendation"])
    
    if contacts_df is not None:
        loop_through_each_contact_send_email(contacts_df, mode_var.get())
        messagebox.showinfo("Success", "Emails have been sent successfully!")

def browse_file():
    global csv_file_path
    file_path = filedialog.askopenfilename(
        title="Select Contacts CSV",
        filetypes=(("CSV Files", "*.csv"),)
    )
    
    if file_path:
        csv_file_path = file_path
        lbl_file_path.config(text=f"Selected file: {file_path}")

# GUI setup
def create_gui():
    global lbl_file_path, mode_var
    root = tk.Tk()
    root.title("Email Sender")

    # Set window size
    root.geometry("500x300")

    # File selection label and button
    lbl_instruction = tk.Label(root, text="Select CSV file with contacts:")
    lbl_instruction.pack(pady=10)

    btn_browse = tk.Button(root, text="Browse", command=browse_file)
    btn_browse.pack()

    lbl_file_path = tk.Label(root, text="No file selected")
    lbl_file_path.pack(pady=5)

    # Radio buttons for mode selection
    mode_var = tk.StringVar(value="live")  # Default to 'live'
    lbl_mode = tk.Label(root, text="Choose mode:")
    lbl_mode.pack(pady=10)

    radio_live = tk.Radiobutton(root, text="Live Mode", variable=mode_var, value="live")
    radio_live.pack()

    radio_test = tk.Radiobutton(root, text="Test Mode", variable=mode_var, value="self")
    radio_test.pack()

    # Run button for email sending
    btn_run = tk.Button(root, text="Run Email Sending", command=run_email_sending, bg="green", fg="white")
    btn_run.pack(pady=20)

    root.mainloop()

# Main code
if __name__ == "__main__":
    csv_file_path = ""
    create_gui()
