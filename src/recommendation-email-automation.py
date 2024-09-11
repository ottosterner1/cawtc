import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import sys
import threading

def get_resource_path(relative_path):
    """ Get the absolute path to a resource file. Handles PyInstaller paths. """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Function definitions
def send_email(to, cc, subject, body):
    from_email = "headcoach@wiltontennisclub.co.uk"
    password_file = get_resource_path('config/email_password.txt')
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

def loop_through_each_contact_send_email(contacts_df, recipient_type):
    if contacts_df is None:
        return
    
    for index, row in contacts_df.iterrows():
        full_name = row['full name']
        recommendation = row['recommendation']
        email = row['email']
        cc_address = [""]
        subject = f"{full_name} Group Recommendation for Next Term"
        
        if recipient_type == "parents":
            body = (
                f"Dear Parent or Guardian,\n\n"
                f"Thank you for signing up your child for this term of coaching at Wilton Tennis Club.\n\n"
                f"{full_name} is recommended to sign up to the following group class for next term: {recommendation}.\n\n"
                f"Please let me know if you have any queries regarding this recommendation.\n\n"
                f"Kind regards,\n"
                f"Marc Beckles, Head Coach"
            )
        else:  # Adults
            body = (
                f"Dear {full_name},\n\n"
                f"Thank you for joining the coaching sessions this term at Wilton Tennis Club.\n\n"
                f"You are recommended to sign up for the following group class next term: {recommendation}.\n\n"
                f"Please let me know if you have any queries regarding this recommendation.\n\n"
                f"Kind regards,\n"
                f"Marc Beckles, Head Coach"
            )

        send_email(email, cc_address, subject, body)

def run_email_sending_in_background():
    global csv_file_path
    if csv_file_path == "":
        messagebox.showerror("Error", "Please select a CSV file first!")
        return
    contacts_df = get_contacts(csv_file_path, ["full name", "email", "recommendation"])
    
    if contacts_df is not None:
        loop_through_each_contact_send_email(contacts_df, recipient_type_var.get())

    btn_run.config(state=tk.NORMAL, text="Send Emails")
    messagebox.showinfo("Success", "Emails have been sent successfully!")

def run_email_sending():
    btn_run.config(state=tk.DISABLED, text="Sending...")
    threading.Thread(target=run_email_sending_in_background).start()

def browse_file():
    global csv_file_path
    file_path = filedialog.askopenfilename(
        title="Select Contacts CSV",
        filetypes=(("CSV Files", "*.csv"),)
    )
    if file_path:
        csv_file_path = file_path
        lbl_file_path.config(text=f"Selected file: {file_path}")

def create_gui():
    global lbl_file_path, recipient_type_var, btn_run, root, mode_var

    root = tk.Tk()  # Tk() root window must be created before any Tkinter variables
    root.title("Email Sender")
    root.geometry("500x400")

    lbl_instruction = tk.Label(root, text="Select CSV file with contacts\n\nFile needs the following columns: full name, email, recommendation")
    lbl_instruction.pack(pady=10)

    btn_browse = tk.Button(root, text="Browse", command=browse_file)
    btn_browse.pack()

    lbl_file_path = tk.Label(root, text="No file selected")
    lbl_file_path.pack(pady=5)

    recipient_type_var = tk.StringVar(value="parents")
    lbl_recipient_type = tk.Label(root, text="Choose recipient type:")
    lbl_recipient_type.pack(pady=10)

    radio_parents = tk.Radiobutton(root, text="Parents", variable=recipient_type_var, value="parents")
    radio_parents.pack()

    radio_adults = tk.Radiobutton(root, text="Adults", variable=recipient_type_var, value="adults")
    radio_adults.pack()

    btn_run = tk.Button(root, text="Send Emails", command=run_email_sending, bg="green", fg="white")
    btn_run.pack(pady=20)

    mode_var = tk.StringVar(value="live")  # Initialize and force live mode after Tk root window

    root.mainloop()

def main():
    global csv_file_path
    csv_file_path = ""
    create_gui()

if __name__ == "__main__":
    main()


