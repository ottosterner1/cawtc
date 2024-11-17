import tkinter as tk
from tkinter import messagebox, filedialog
import datetime
import openpyxl
import pandas as pd

# Constants
DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
VALID_SESSION_TYPES = [
    "red","green","orange","yellow","junior","adults","tots", "red 1", "red 2", "red 3", "orange 1", "orange 2",
    "green 1", "green 2", "yellow 1", "yellow 2", "yellow 3",
    "bronze", "bronze plus", "silver", "gold", "platinum", "perf", "perf 2"
]
VALID_SEASONS = ["spring", "summer", "autumn", "winter"]
COLUMN_NAMES = ["Day of Week", "Sheet Name", "full name", "email"]  # Added Sheet Name
COACHING_CONTACT_COLUMNS = ["full name","dob","email"]

def read_contacts_table(file_path, sheet_name):    
    """
    Read names table in the contacts sheet

    Args:
     - file_path: string
     - sheet_name: string

    Returns:
     - contacts_dataframe: df containing list of contacts
    """
    try:
        # Read the sheet starting from the third row
        contacts_dataframe = pd.read_excel(
            file_path, sheet_name=sheet_name, skiprows=2)

        # Make the columns lower case and strip the white space
        contacts_dataframe.columns = contacts_dataframe.columns.str.lower().str.strip()

        for target_col in COACHING_CONTACT_COLUMNS:
            contacts_dataframe.columns = [
                target_col if isinstance(col, str) and target_col in col else col 
                for col in contacts_dataframe.columns
            ]

        contacts_dataframe = contacts_dataframe[COACHING_CONTACT_COLUMNS]

        # Find the index of the first row where "Full name" is NaN and drop all
        # rows after that
        first_empty_index = contacts_dataframe[
            contacts_dataframe.filter(like="full name").isna().any(axis=1)
        ].index
        if not first_empty_index.empty:
            contacts_dataframe = contacts_dataframe.iloc[: first_empty_index[0]]

    except Exception as e:
        messagebox.showerror("Error", f"Error reading the contacts: {str(e)}")
        exit()

    return contacts_dataframe

def get_contact_details_from_registers(
        registers_path, season_of_year, coaching_type_sheet, year):
    """
    This will cycle through each of the registers and get the contact details
    of each person in the session

    Args:
        season_of_year (str): The season of the year
        coaching_type_sheet (str): The coaching type sheet
        year (int): The year

    Returns:
        contacts_data_frame (DataFrame): A pandas DataFrame containing the
        contact details of each person in the session
    """
    try:
        # Data frame of contacts
        contacts_data_frame = pd.DataFrame(
            columns=COLUMN_NAMES)

        # Cycle through each of the days of the week / sheets
        for day in DAYS_OF_WEEK:
            # Open the register sheet
            registers = f"{registers_path}/{day} {season_of_year} {year}.xlsx"
            print(f"Opening file at: {registers}")
            wb = openpyxl.load_workbook(registers, read_only=True)

            # Find the sheet that contains the session type in its name
            sheet_names = [sheet for sheet in wb.sheetnames if coaching_type_sheet.lower() in sheet.lower()]

            # Cycle through each of the sheets
            for sheet_name in sheet_names:
                # Call the read contacts table function
                contacts = read_contacts_table(registers, sheet_name)
                # Add the day of the week and sheet name to the contacts data frame
                contacts["Day of Week"] = day
                contacts["Sheet Name"] = sheet_name  # Add sheet name to the DataFrame
                # Remove duplicate columns in contacts_data_frame
                contacts_data_frame = contacts_data_frame.loc[
                    :, ~contacts_data_frame.columns.duplicated()
                ]
                # Remove duplicate columns in contacts
                contacts = contacts.loc[:, ~contacts.columns.duplicated()]
                contacts = contacts.reset_index(drop=True)
                # Concatenate the contacts data frame
                contacts_data_frame = pd.concat(
                    [contacts_data_frame, contacts], ignore_index=True
                )
    except Exception as e:
        messagebox.showerror("Error", f"Error in get_contact_details_from_registers: {str(e)}")
        exit()

    return contacts_data_frame

def run_script(registers_path, output_path, season, session_type):
    """
    Execute the main script to retrieve contact details and save them to a CSV file.

    Args:
        registers_path (str): The directory path where the registers are located.
        output_path (str): The directory path where the output CSV file will be saved.
        season (str): The season of the year (e.g., 'spring', 'summer', 'autumn', 'winter').
        session_type (str): The type of coaching session (e.g., 'tots', 'red 1', 'green 2').

    Returns:
        None
    """
    current_year = datetime.datetime.now().year
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    contacts_df = get_contact_details_from_registers(registers_path, season, session_type, current_year)
    if contacts_df is not None:
        target_contacts_filename = f"{output_path}/contacts_list_{session_type}_{season}_{current_date}.csv"
        contacts_df.to_csv(target_contacts_filename, index=False)
        messagebox.showinfo("Success", f"Contacts have been successfully saved to: {target_contacts_filename}")
    else:
        messagebox.showerror("Error", "Failed to create the contacts data frame.")

def select_registers_path():
    """
    Open a dialog to select the directory containing the registers.

    Args:
        None

    Returns:
        None
    """
    path = filedialog.askdirectory(title="Select Registers Directory")
    if path:
        registers_path_var.set(path)

def select_output_path():
    """
    Open a dialog to select the directory where the output CSV will be saved.

    Args:
        None

    Returns:
        None
    """
    path = filedialog.askdirectory(title="Select Output Directory")
    if path:
        output_path_var.set(path)

def on_button_click():
    """
    Handle the button click event to run the script with user inputs.

    Args:
        None

    Returns:
        None
    """
    season = season_var.get().lower()
    session_type = session_type_var.get().lower()
    registers_path = registers_path_var.get()
    output_path = output_path_var.get()

    if season not in VALID_SEASONS:
        messagebox.showerror("Invalid Input", "Please enter a valid season.")
        return
    if session_type not in VALID_SESSION_TYPES:
        messagebox.showerror("Invalid Input", "Please enter a valid session type.")
        return
    if not registers_path:
        messagebox.showerror("Invalid Input", "Please select the registers directory.")
        return
    if not output_path:
        messagebox.showerror("Invalid Input", "Please select the output directory.")
        return

    run_script(registers_path, output_path, season, session_type)

# GUI Setup
root = tk.Tk()
root.title("Run Contact Details Script")

tk.Label(root, text="Enter Season:").pack(pady=5)
season_var = tk.StringVar()
tk.Entry(root, textvariable=season_var).pack(pady=5)

tk.Label(root, text="Enter Session Type:").pack(pady=5)
session_type_var = tk.StringVar()
tk.Entry(root, textvariable=session_type_var).pack(pady=5)

tk.Label(root, text="Select Registers Directory:").pack(pady=5)
registers_path_var = tk.StringVar()
tk.Entry(root, textvariable=registers_path_var, width=50).pack(pady=5)
tk.Button(root, text="Browse...", command=select_registers_path).pack(pady=5)

tk.Label(root, text="Select Output Directory:").pack(pady=5)
output_path_var = tk.StringVar()
tk.Entry(root, textvariable=output_path_var, width=50).pack(pady=5)
tk.Button(root, text="Browse...", command=select_output_path).pack(pady=5)

tk.Button(root, text="Run Script", command=on_button_click).pack(pady=20)

root.mainloop()
