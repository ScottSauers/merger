import pandas as pd
import tkinter as tk
import glob
import shutil
import os
from tkinter import messagebox
from tkinter import ttk
from scipy.stats import wasserstein_distance


def setup_temp_directory():
    temp_dir = os.path.join(os.getcwd(), "temp_files")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def clear_temp_directory():
    temp_dir = os.path.join(os.getcwd(), "temp_files")
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        os.remove(file_path)

def copy_files_to_temp(folder_path, temp_dir, progress, file_listbox, root):
    files = os.listdir(folder_path)
    progress['value'] = 0
    progress['maximum'] = len(files)

    # Check if the files are already in the temporary directory
    existing_files = os.listdir(temp_dir)
    if set(files) == set(existing_files):
        # Files are already in the temporary directory, populate the file listbox
        for i, filename in enumerate(existing_files):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                progress['value'] = i + 1
                file_listbox.insert(tk.END, filename)
                root.update_idletasks()
    else:
        # Files are not in the temporary directory, copy them from the selected folder
        for i, filename in enumerate(files):
            src_path = os.path.join(folder_path, filename)
            dest_path = os.path.join(temp_dir, filename)
            if os.path.isfile(src_path):
                shutil.copy(src_path, dest_path)
                progress['value'] = i + 1
                file_listbox.insert(tk.END, filename)
                root.update_idletasks()

    progress['value'] = 0

def validate_file(file_path):
    allowed_extensions = ['.xlsx', '.csv']  # Define the allowed file types
    return any(file_path.endswith(ext) for ext in allowed_extensions)

def load_file(file_path):
    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            return None, "Unsupported file format."
        return df, None
    except Exception as e:
        return None, str(e)

def setup_treeview(df, treeview):
    # Clear existing columns and data in treeview
    treeview.delete(*treeview.get_children())
    treeview['columns'] = list(df.columns)
    #print("TreeView columns:", treeview['columns'])

    # Reset the configuration to avoid residual settings
    for col in treeview['columns']:
        treeview.heading(col, text=col, anchor='w')
        treeview.column(col, anchor="w", width=100)

    # Populate treeview with data
    for index, row in df.iterrows():
        # The row data must be a tuple in the exact order of the columns
        treeview.insert("", "end", values=tuple(row[col] for col in df.columns))

    # Make sure the treeview is updated with new settings
    treeview.update()

def select_all_files(file_vars):
    for var in file_vars.values():
        var.set(True)


def verify_key_column(selected_files, temp_dir, key_column):
    missing_key_files = []
    errors = []

    for filename in selected_files:
        file_path = os.path.join(temp_dir, filename)
        try:
            # Load the file based on its extension
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)

            # Check if the key column exists in the dataframe
            if key_column not in df.columns:
                missing_key_files.append(filename)

        except Exception as e:
            # Store error messages in a list to handle later or return
            errors.append(f"Error loading {filename}: {str(e)}")
            continue

    return missing_key_files, errors

def populate_files(parent_widget):
    temp_dir = "/temp_files"
    print("Populating files in the temporary directory...")
    print("Temporary directory:", temp_dir)
    file_pattern = os.path.join(temp_dir, "*")
    print("File pattern:", file_pattern)
    files = glob.glob(file_pattern)
    print("Files found:", files)

    file_checkbuttons = {}
    file_vars = {}

    if not files:
        label = ttk.Label(parent_widget, text="No Excel files found in the temporary directory.")
        label.pack(anchor='w', padx=10, pady=2)
    else:
        for file_path in files:
            filename = os.path.basename(file_path)
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(parent_widget, text=filename, variable=var)
            chk.pack(anchor='w', padx=10, pady=2)
            file_checkbuttons[filename] = chk
            file_vars[filename] = var
    print("File population complete.")
    return file_checkbuttons, file_vars

def add_key_column_by_matching(temp_dir, target_file, source_file, target_id_column, source_id_column, key_column):
    target_path = os.path.join(temp_dir, target_file)
    source_path = os.path.join(temp_dir, source_file)

    # Load data from files based on file extension
    def load_data(file_path):
        if file_path.endswith('.xlsx'):
            return pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type for {file_path}")

    try:
        df_target = load_data(target_path)
        df_source = load_data(source_path)
    except ValueError as e:
        print(f"Error loading data files: {str(e)}")
        raise

    # Validate existence of necessary columns in dataframes
    if target_id_column not in df_target.columns:
        raise ValueError(f"Target identifier column '{target_id_column}' does not exist in target file.")
    if key_column not in df_source.columns or source_id_column not in df_source.columns:
        raise ValueError(f"Source identifier column '{source_id_column}' or key column '{key_column}' does not exist in source file.")

    # Create a mapping from the source dataframe based on the identifier and key columns
    key_mapping = df_source.dropna(subset=[key_column]).set_index(source_id_column)[key_column].to_dict()

    # Map the key column from the source to the target dataframe based on matching identifier columns
    df_target[key_column] = df_target[target_id_column].map(key_mapping)

    # Save the updated target dataframe back to the file
    def save_data(df, file_path):
        if file_path.endswith('.xlsx'):
            df.to_excel(file_path, index=False)
        elif file_path.endswith('.csv'):
            df.to_csv(file_path, index=False)
        else:
            raise ValueError(f"Unsupported file type for {file_path}")

    try:
        save_data(df_target, target_path)
    except ValueError as e:
        print(f"Error saving updated data to file: {str(e)}")
        raise

    print(f"Key column '{key_column}' added to '{target_file}' based on matching identifier column '{target_id_column}' from '{source_file}'.")


def find_similar_columns(selected_files, temp_dir, master_key_file, key_column):
    master_key_path = os.path.join(temp_dir, master_key_file)  # Full path to the master key file

    # Attempt to load the master key file based on its extension
    try:
        if master_key_path.lower().endswith('.csv'):
            key_data = pd.read_csv(master_key_path)
        elif master_key_path.lower().endswith('.xlsx'):
            key_data = pd.read_excel(master_key_path)
        else:
            raise ValueError(f"Unsupported file format for the master key file: {master_key_file}")
    except Exception as e:
        raise ValueError(f"Failed to load master key file due to: {str(e)}")

    if key_column not in key_data.columns:
        raise ValueError(f"Key column '{key_column}' not found in the file {master_key_file}")

    key_hist = key_data[key_column].value_counts(normalize=True)
    results = []
    similarity_scores = []

    for filename in selected_files:
        file_path = os.path.join(temp_dir, filename)
        try:
            if file_path.lower().endswith('.csv'):
                data = pd.read_csv(file_path)
            elif file_path.lower().endswith('.xlsx'):
                data = pd.read_excel(file_path)
            else:
                continue  # Skip files with unsupported formats
        except Exception as e:
            raise ValueError(f"Failed to load data from {filename} due to: {str(e)}")

        columns = data.columns.tolist()
        selected_columns = columns[:20] + columns[-5:]  # example slice, adjust as necessary

        max_similarity = 0
        most_similar_column = None

        for column in selected_columns:
            if column in data.columns:
                column_hist = data[column].value_counts(normalize=True)
                emd = wasserstein_distance(key_hist, column_hist)
                similarity = 1 / (1 + emd)

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_column = column

        results.append((filename, most_similar_column))
        similarity_scores.append(max_similarity)

    avg_similarity = sum(similarity_scores) / len(similarity_scores)
    low_similarity_files = [filename for filename, score in zip(selected_files, similarity_scores) if score < avg_similarity * 0.8]

    return results, low_similarity_files