import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from evaluation import run_instant_runoff

# Set up the main window
root = tk.Tk()
root.title("Instant Runoff Voting Assessment")

# Frame for file selection and preview
frame1 = ttk.Frame(root)
frame1.pack(padx=10, pady=10, fill='x', expand=True)

# Label for feedback
feedback_label = ttk.Label(root, text="")
feedback_label.pack(pady=(0, 10))

# Create style objects for ttk.Label
style = ttk.Style(root)
style.configure("Error.TLabel", foreground="red")
style.configure("Good.TLabel", foreground="green")


# Function to open file dialog and load Excel file
def load_excel():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    if file_path:
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, file_path)

        # If all checks pass
        style.configure("Good.TLabel", foreground="green")
        try:
            # Attempt to read the Excel file without headers
            df = pd.read_excel(file_path, header=None)
            update_table(df.head())

            column_names = ['Voter-ID', 'Region1', 'Region2']
            # Check if the number of column names matches the number of columns in the DataFrame
            if len(column_names) == df.shape[1]:
                # Assign new column names
                df.columns = column_names
            else:
                feedback_label.config(text="The Excel file should have exactly three columns (Voter-ID, Region 1, Region 2).", style="Error.TLabel",)
                return

            # Check if unique header names are included

            all_match = all(df.iloc[0, i].split('[')[0] == df.iloc[1, i].split('[')[0] for i in range(1,len(df.columns)))

            print(all_match)

            if not all_match:
                feedback_label.config(
                    text="Please remove the header from the Excel file.",
                    style="Error.TLabel", )
                return

            # If all checks pass
            feedback_label.config(text="Excel file looks good!", style="Good.TLabel",)

        except Exception as e:
                messagebox.showerror("Error", str(e))
                feedback_label.config(style="Error.TLabel", text="")

# Function to open directory dialog and select output directory
def select_output_dir():
    dir_path = filedialog.askdirectory()
    if dir_path:
        output_dir_entry.delete(0, tk.END)
        output_dir_entry.insert(0, dir_path)

# Function to update the table with Excel data
def update_table(data):
    for i in table.get_children():
        table.delete(i)

    headers = ['Voter-ID', 'Region1', 'Region2']

    # Set the table's columns to these headers
    table["columns"] = headers

    # Configure the table to not show the default first column (if needed)
    table["show"] = "headings"  # This hides the default first column

    # Configure each column's heading
    for header in headers:
        table.heading(header, text=header)

    for column in table["columns"]:
        table.heading(column, text=column)
    df_rows = data.to_numpy().tolist()
    for row in df_rows:
        table.insert("", "end", values=row)

# Function to run the Instant Runoff Voting process
def run_voting():
    file_path = file_path_entry.get()
    output_dir = output_dir_entry.get()
    consider_invalid = consider_invalid_var.get()
    if file_path and output_dir:
        try:
            # Adjust the function to accept the output directory as an argument
            run_instant_runoff(file_path,output_dir, consider_invalid)
            messagebox.showinfo("Success", "Voting assessment completed. Check the output files in the specified directory.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    else:
        messagebox.showwarning("Warning", "Please select an Excel file and output directory first.")



# Entry for file path
file_path_entry = ttk.Entry(frame1, width=40)
file_path_entry.pack(side=tk.LEFT, expand=True, padx=(0, 10))

# Button to load Excel file
load_button = ttk.Button(frame1, text="Load Excel", command=load_excel)
load_button.pack(side=tk.LEFT, padx=(0, 10))

# Frame for output directory selection
frame2 = ttk.Frame(root)
frame2.pack(padx=10, pady=10, fill='x', expand=True)

# Entry for output directory path
output_dir_entry = ttk.Entry(frame2, width=40)
output_dir_entry.pack(side=tk.LEFT, expand=True, padx=(0, 10))

# Button to select output directory
select_dir_button = ttk.Button(frame2, text="Select Output Directory", command=select_output_dir)
select_dir_button.pack(side=tk.LEFT, padx=(0, 10))

# Checkbox for considering invalid votes
consider_invalid_var = tk.BooleanVar()
consider_invalid_check = ttk.Checkbutton(root, text="Consider invalid votes (voters that have not ranked all candidates)", variable=consider_invalid_var)
consider_invalid_check.pack(pady=(0, 10))

# Table to preview Excel data
table = ttk.Treeview(root)
table.pack(padx=10, pady=10, fill='x', expand=True)

# Button to run the Instant Runoff Voting process
run_button = ttk.Button(root, text="Instant-Runoff Vote evaluation", command=run_voting)
run_button.pack(pady=(0, 10))

# Run the application
root.mainloop()
