"""
Filename: retrieving_contact_details_from_registers.py
Description: This script automates the process of getting name and
             contact details from Marc Beckles' coaching registers.
Author: Otto Sterner
Date: 22-May-2024
Version: 1.0.0

Usage:
    python contact_details_registers.py
"""

import tkinter as tk
from tkinter import messagebox
import datetime
import openpyxl
import pandas as pd

# Constants
REGISTERS_PATH = (
    "C:\\Users\\Otto\\OneDrive\\Tennis\\Automation\\files\\week-registers-test"
)
TARGET_EMAIL_LIST = (
    "C:\\Users\\Otto\\OneDrive\\Tennis\\Automation\\files\\output-contacts\\"
)
DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
VALID_SESSION_TYPES = [
    "tots",
    "red 1",
    "red 2",
    "red 3",
    "orange 1",
    "orange 2",
    "green 1",
    "green 2",
    "yellow 1",
    "yellow 2",
    "yellow 3",
    "bronze",
    "bronze plus",
    "silver",
    "gold",
    "platinum",
    "perf",
    "perf 2",
]
VALID_SEASONS = ["spring", "summer", "autumn", "winter"]


def read_contacts_table(file_path, sheet_name):
    """
    Read names table in the contacts sheet

    Args:
     - file_path: string

    Returns:
     - contacts_dataframe: df containing list of contacts
    """
    try:
        # Read the sheet starting from the third row
        contacts_dataframe = pd.read_excel(
            file_path, sheet_name=sheet_name, skiprows=2)

        # Make the columns lower case and strip the white space
        contacts_dataframe.columns = contacts_dataframe.columns.str.lower().str.strip()

        # Rename columns that contain 'full name' to 'full name'
        contacts_dataframe.columns = ['full name' if isinstance(col, str) and 'full name' in col else col for col in contacts_dataframe.columns]
        contacts_dataframe.columns = ['email' if isinstance(col, str) and 'email' in col else col for col in contacts_dataframe.columns]

        contacts_dataframe = contacts_dataframe[
            [
                col
                for col in contacts_dataframe.columns
                if "full name" in str(col) or "email" in str(col)
            ]
        ]

        # Find the index of the first row where "Full name" is NaN and drop all
        # rows after that
        first_empty_index = contacts_dataframe[
            contacts_dataframe.filter(like="full name").isna().any(axis=1)
        ].index
        if not first_empty_index.empty:
            contacts_dataframe = contacts_dataframe.iloc[: first_empty_index[0]]

    except Exception as e:
        print("Error reading the contacts, error message: " + str(e))
        exit()

    return contacts_dataframe


def get_contact_details_from_registers(
        season_of_year, coaching_type_sheet, year):
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
    # Data frame of contacts
    contacts_data_frame = pd.DataFrame(
        columns=["Day of Week", "full name", "email"])

    # Cycle through each of the days of the week / sheets
    for day in DAYS_OF_WEEK:

        # Open the register sheet
        registers = f"{REGISTERS_PATH}\\{day} {season_of_year} {year}.xlsx"
        print(f"Opening file at: {registers}")
        wb = openpyxl.load_workbook(registers, read_only=True)

        # Find the sheet that contains the session type in its name
        sheet_names = [
            sheet for sheet in wb.sheetnames if coaching_type_sheet in sheet]

        # Cycle through each of the sheets
        for sheet_name in sheet_names:
            # Call the read contacts table function
            contacts = read_contacts_table(registers, sheet_name)
            # Add the day of the week to the contacts data frame
            contacts["Day of Week"] = day
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
    return contacts_data_frame


if __name__ == "__main__":
    # Input the season
    SEASON = ""
    while SEASON.lower() not in VALID_SEASONS:
        SEASON = input(
            """
        Please enter the season, the choices are:
        - Spring
        - Summer
        - Autumn
        - Winter
        Your Choice: """
        )
        if SEASON.lower() not in VALID_SEASONS:
            print("Invalid choice. Please enter a valid season.")

    # Input the session type
    SESSION_TYPE = ""
    while SESSION_TYPE.lower() not in VALID_SESSION_TYPES:
        SESSION_TYPE = input(
            f"""
        Enter the session type:
        Options: {', '.join(VALID_SESSION_TYPES).title()}
        Your Choice: """
        )
        if SESSION_TYPE.lower() not in VALID_SESSION_TYPES:
            print("Invalid choice. Please enter a valid session type.")

    # Get the current year and date
    current_year = datetime.datetime.now().year
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Call function to retrive the contact details from all of the registers
    contacts_df = get_contact_details_from_registers(
        SEASON, SESSION_TYPE, current_year)

    # Print the contacts data frame
    print("The contacts data frame is:")
    print(contacts_df)
    print(
        "The data frame has been successfully created, the contacts will be saved to a csv file."
    )

    # Write the output data frame to a csv
    target_contacts_filename = (
        TARGET_EMAIL_LIST
        + "contacts_list_"
        + SESSION_TYPE
        + "_"
        + SEASON
        + "_"
        + current_date
        + ".csv"
    )

    print("Saving the contacts to: " + target_contacts_filename)
    contacts_df.to_csv(target_contacts_filename, index=False)

    print("The contacts have been successfully saved to a csv file.")
