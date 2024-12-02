import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import sys
import threading
import queue

# Function definitions
def send_email(to, cc, subject, body):
    from_email = "headcoach@wiltontennisclub.co.uk"
    
    # Try multiple methods to get the password
    password = None
    
    # First try environment variable
    password = os.environ.get('EMAIL_PASSWORD')
    
    # If not found, try PyInstaller's _MEIPASS for bundled version
    if not password:
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            password_file = os.path.join(base_path, 'email_password.txt')
            with open(password_file, 'r') as file:
                password = file.read().strip()
        except:
            pass

    if not password:
        return False, "Email password not found! Please ensure either EMAIL_PASSWORD environment variable is set or email_password.txt exists."
    
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
        return True, None
    except Exception as e:
        print(f"Failed to send email to {to}: {e}")
        return False, str(e)

def get_contacts(file_path, data_columns):
    try:
        contacts_df = pd.read_csv(file_path, usecols=data_columns)
        return True, contacts_df
    except Exception as e:
        return False, str(e)

def send_emails_worker(q, contacts_df, recipient_type, booking_date, booking_time, booking_password):
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
                f"{full_name} is recommended to sign up to the following group class for next term:\n\n{recommendation}\n\n"
                f"Bookings for next term open on {booking_date} at {booking_time}.\n\n"
                f"Once logged into the booking system, the groups will be password protected. You will require this password: {booking_password}\n\n"
                f"Here is the link to the Wilton coaching booking page: https://booking.wiltontennisclub.co.uk/. \n\n"
                f"Please let me know if you have any queries regarding this recommendation.\n\n"
                f"Kind regards,\n"
                f"Marc Beckles, Head Coach"
            )
        else:  # Adults
            body = (
                f"Dear {full_name},\n\n"
                f"Thank you for joining the coaching sessions this term at Wilton Tennis Club.\n\n"
                f"You are recommended to sign up for the following group class next term:\n\n{recommendation}\n\n"
                f"Bookings for next term open on {booking_date} at {booking_time}.\n\n"
                f"Once logged into the booking system, the groups will be password protected. You will require this password: {booking_password}\n\n"
                f"Here is the link to the Wilton coaching booking page: https://booking.wiltontennisclub.co.uk/. \n\n"
                f"Please let me know if you have any queries regarding this recommendation.\n\n"
                f"Kind regards,\n"
                f"Marc Beckles, Head Coach"
            )

        success, error = send_email(email, cc_address, subject, body)
        if not success:
            q.put(("error", f"Failed to send email to {email}: {error}"))
            return
        
        q.put(("progress", f"Email sent to {email}"))
    
    q.put(("done", None))

def process_queue():
    try:
        while True:
            msg_type, msg = message_queue.get_nowait()
            
            if msg_type == "error":
                messagebox.showerror("Error", msg)
                btn_run.config(state=tk.NORMAL, text="Send Emails")
                return
            elif msg_type == "done":
                btn_run.config(state=tk.NORMAL, text="Send Emails")
                messagebox.showinfo("Success", "All emails have been sent successfully!")
                return
            elif msg_type == "progress":
                print(msg)
            
            message_queue.task_done()
    except queue.Empty:
        root.after(100, process_queue)

def run_email_sending():
    global csv_file_path
    if csv_file_path == "":
        messagebox.showerror("Error", "Please select a CSV file first!")
        return

    # Check if the user has entered all required fields
    if not entry_date.get() or not entry_time.get() or not entry_password.get():
        messagebox.showerror("Error", "Please enter the date, time, and password for the bookings.")
        return

    # Ask for confirmation before sending emails
    recipient_type = recipient_type_var.get()
    if not messagebox.askyesno("Confirmation", 
        f"Are you sure you want to send emails to all {recipient_type} in the file?\n\n"
        f"Date: {entry_date.get()}\n"
        f"Time: {entry_time.get()}\n"
        f"Password: {entry_password.get()}\n\n"
        "Please double check these details before confirming."):
        return

    success, result = get_contacts(csv_file_path, ["full name", "email", "recommendation"])
    if not success:
        messagebox.showerror("Error", f"Failed to read contacts: {result}")
        return

    btn_run.config(state=tk.DISABLED, text="Sending...")
    
    # Start the email sending thread
    thread = threading.Thread(
        target=send_emails_worker,
        args=(message_queue, result, recipient_type_var.get(), 
              entry_date.get(), entry_time.get(), entry_password.get())
    )
    thread.daemon = True
    thread.start()
    
    # Start monitoring the message queue
    root.after(100, process_queue)

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
    global lbl_file_path, recipient_type_var, btn_run, root, entry_date, entry_time, entry_password, message_queue

    root = tk.Tk()
    root.title("Email Sender")
    root.geometry("500x600")

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

    lbl_date = tk.Label(root, text="Enter booking opening date (e.g., 01-Jan-2024):")
    lbl_date.pack(pady=10)
    entry_date = tk.Entry(root)
    entry_date.pack()

    lbl_time = tk.Label(root, text="Enter booking opening time (e.g., 09:00 AM):")
    lbl_time.pack(pady=10)
    entry_time = tk.Entry(root)
    entry_time.pack()

    lbl_password = tk.Label(root, text="Enter booking system password:")
    lbl_password.pack(pady=10)
    entry_password = tk.Entry(root)
    entry_password.pack()

    btn_run = tk.Button(root, text="Send Emails", command=run_email_sending, bg="green", fg="black")
    btn_run.pack(pady=20)

    root.mainloop()

def main():
    global csv_file_path, message_queue
    csv_file_path = ""
    message_queue = queue.Queue()
    create_gui()

if __name__ == "__main__":
    main()


