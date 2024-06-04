import os
import glob
import pandas as pd
import tkinter as tk
from tkinter import simpledialog
from tkinter import filedialog, ttk, messagebox
from operations import copy_files_to_temp, setup_temp_directory, load_file, setup_treeview, select_all_files, verify_key_column, find_similar_columns

class DataMatcherApp:
    def __init__(self, root):
        self.root = root
        self.temp_dir = setup_temp_directory()
        print("Temporary directory path:", self.temp_dir)
        self.df = None
        self.master_key_file = None
        self.key_column = None
        self.notebook = ttk.Notebook(self.root)
        self.add_key_vars = {}
        self.setup_ui()

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.step1 = ttk.Frame(self.notebook)
        self.step2 = ttk.Frame(self.notebook)
        self.step3 = ttk.Frame(self.notebook)
        self.step4 = ttk.Frame(self.notebook)

        self.notebook.add(self.step1, text='1. Select Folder')
        self.notebook.add(self.step2, text='2. Select File')
        self.notebook.add(self.step3, text='3. Select Key Column')
        self.notebook.add(self.step4, text='4. Select Files to Merge')
        self.notebook.pack(expand=True, fill='both')

        self.setup_step1()
        self.setup_step2()
        self.setup_step3()
        # Do not have the self.setup_step4() call from here

    def setup_step1(self):
        ttk.Label(self.step1, text="Please select a folder to process:").pack(pady=20)
        ttk.Button(self.step1, text="Select Folder", command=self.select_folder).pack()
        self.progress = ttk.Progressbar(self.step1, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(pady=20)

    def setup_step2(self):
        self.file_listbox = tk.Listbox(self.step2, height=5)
        self.file_listbox.pack(fill='x', pady=20)
        ttk.Button(self.step2, text="Confirm File Selection", command=self.on_file_confirm).pack()

    def setup_step3(self):
        self.treeview = ttk.Treeview(self.step3)
        self.treeview.pack(fill='both', expand=True, pady=20)
        ttk.Label(self.step3, text="Select the key column:").pack(pady=10)
        self.column_selector = ttk.Combobox(self.step3)
        self.column_selector.pack(fill='x', expand=True, pady=20)
        ttk.Button(self.step3, text="Choose Column", command=self.confirm_column_selection).pack()

    def confirm_column_selection(self):
        selected_column = self.column_selector.get()
        if selected_column and selected_column in self.df.columns:
            self.key_column = selected_column
            messagebox.showinfo("Key Column Selected", f"Key Column: {self.key_column}")
            self.setup_step4()  # Call setup_step4() here
            self.notebook.select(self.step4)  # Move to next step
        else:
            messagebox.showerror("Error", "The selected column does not exist in the file.")

    def setup_step4(self):
        print("Setting up step 4...")
        self.file_checkbuttons = {}
        self.file_vars = {}
        label = ttk.Label(self.step4, text="Select files to merge:")
        label.pack(pady=10)
        scroll_frame = ttk.Frame(self.step4)
        scroll_canvas = tk.Canvas(scroll_frame)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=scroll_canvas.yview)
        scrollable_frame = ttk.Frame(scroll_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: scroll_canvas.configure(
                scrollregion=scroll_canvas.bbox("all")
            )
        )

        scroll_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        print("Populating files...")
        self.populate_files(scrollable_frame)

        select_all_button = ttk.Button(self.step4, text="Select All", command=lambda: select_all_files(self.file_vars))
        select_all_button.pack(pady=5)

        confirm_selection_button = ttk.Button(self.step4, text="Confirm Selection", command=self.confirm_multi_file_selection)
        confirm_selection_button.pack(pady=5)


        scroll_frame.pack(fill="both", expand=True)
        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        print("Step 4 setup complete.")


    def populate_files(self, parent_widget):
        print("Populating files in the temporary directory...")
        temp_directory = self.temp_dir
        print("Temporary directory:", temp_directory)
        file_pattern = os.path.join(temp_directory, "*")
        files = glob.glob(file_pattern)
        print("File pattern:", file_pattern)
        print("Files found:", files)

        if not files:
            label = ttk.Label(parent_widget, text="No Excel files found in the temporary directory.")
            label.pack(anchor='w', padx=10, pady=2)
        else:
            for file_path in files:
                filename = os.path.basename(file_path)
                var = tk.BooleanVar(value=False)  # Initialize BooleanVar with False
                chk = ttk.Checkbutton(parent_widget, text=filename, variable=var)
                chk.pack(anchor='w', padx=10, pady=2)
                self.file_checkbuttons[filename] = chk
                self.file_vars[filename] = var  # Store the BooleanVar associated with the filename

        print("File population complete.")


    def setup_step5(self, notebook, selected_files, master_key_file, key_column):
        # Initialize the frame for step 5 first
        step5 = ttk.Frame(notebook)
        notebook.add(step5, text='5. Review and Confirm')
        notebook.select(step5)  # Now, it's correct to select the step5 as it has been defined

        # Use the function to get suggested columns
        suggestions, low_similarity_files = find_similar_columns(selected_files, master_key_file, key_column, key_column)

        # Setup the UI components
        scroll_frame = ttk.Frame(step5)
        scroll_canvas = tk.Canvas(scroll_frame)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=scroll_canvas.yview)
        scrollable_frame = ttk.Frame(scroll_canvas)

        scroll_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        # Populate the scrollable area with file selections and suggestions
        self.populate_review_area(scrollable_frame, suggestions, low_similarity_files, key_column)

        scroll_frame.pack(fill="both", expand=True)
        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add the "Add New Key Column" button
        add_key_button = ttk.Button(step5, text="Add New Key Column", command=lambda: messagebox.showinfo("Info", "Feature not implemented yet"))
        add_key_button.pack(side="right", padx=10, pady=5)

        master_key_path = os.path.join(temp_dir, master_key_file)
        suggestions, low_similarity_files = find_similar_columns(selected_files, temp_dir, master_key_path, key_column)

    def populate_review_area(self, parent_widget, suggestions, low_similarity_files, default_key_column):
        for file_path, suggested_column in suggestions:
            frame = ttk.Frame(parent_widget)
            frame.pack(fill="x", padx=10, pady=2)

            file_label = ttk.Label(frame, text=file_path)
            file_label.pack(side="left", padx=(0, 10))

            dropdown = ttk.Combobox(frame, values=[suggested_column])
            dropdown.set(suggested_column)
            dropdown.pack(side="left")

            # Display warning if the file is in the low similarity list
            if file_path in low_similarity_files:
                warning_label = ttk.Label(frame, text="⚠️", foreground="red")
                warning_label.pack(side="left", padx=(5, 0))
            elif suggested_column == default_key_column:
                # If the column matches the default key, just use it without a warning
                dropdown['values'] = [default_key_column]
                dropdown.set(default_key_column)



    # Step utils
    def confirm_multi_file_selection(self):
        # Collect all filenames for which the corresponding variable in file_vars is True (checked)
        selected_files = [filename for filename, var in self.file_vars.items() if var.get()]

        if not selected_files:
            messagebox.showerror("Error", "No files selected. Please select at least one file before confirming.")
            return

        # Verify if the key column exists in all selected files
        missing_key_files, errors = verify_key_column(selected_files, self.temp_dir, self.key_column)

        if missing_key_files:
            messagebox.showinfo("Missing Key Column", "Missing key column in files: " + ', '.join(missing_key_files))
        if errors:
            messagebox.showerror("File Load Error", "\n".join(errors))

        # Corrected call to setup_step5
        self.setup_step5(self.notebook, selected_files, self.master_key_file, self.key_column)


    def prompt_for_file_selection_for_key_column(self, missing_key_files):
        # Create a new top-level window
        file_selection_window = tk.Toplevel(self.root)
        file_selection_window.title("Key Column Addition Confirmation")

        # Informative text label
        ttk.Label(file_selection_window, text="Some files are missing the key column. Would you like to add it?").pack(pady=10, padx=10)

        # Function to handle user confirmation
        def on_confirm():
            self.prompt_for_key_column_addition(missing_key_files)
            file_selection_window.destroy()

        # Function to handle user cancellation
        def on_cancel():
            file_selection_window.destroy()

        # Yes and No buttons
        confirm_button = ttk.Button(file_selection_window, text="Yes", command=on_confirm)
        confirm_button.pack(side=tk.LEFT, padx=15, pady=20)

        cancel_button = ttk.Button(file_selection_window, text="No", command=on_cancel)
        cancel_button.pack(side=tk.RIGHT, padx=15, pady=20)


    def prompt_for_key_column_addition(self, missing_key_files, selected_indices):
        add_key_window = tk.Toplevel(self.root)
        add_key_window.title("Map and Add Key Column")

        frame = ttk.Frame(add_key_window)
        frame.pack(padx=10, pady=10)

        # Labels and Listboxes for file selection
        ttk.Label(frame, text="Select the target file (to add the key to):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        target_file_listbox = tk.Listbox(frame, height=5, exportselection=False)
        target_file_listbox.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Select the source file (from which to map the key):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        source_file_listbox = tk.Listbox(frame, height=5, exportselection=False)
        source_file_listbox.grid(row=1, column=1, padx=5, pady=5)

        # Dropdowns for selecting identifier and key columns in the source file
        ttk.Label(frame, text="Identifier column in target file:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        target_id_column_selector = ttk.Combobox(frame)
        target_id_column_selector.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Identifier column in source file:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        source_id_column_selector = ttk.Combobox(frame)
        source_id_column_selector.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Key column in source file:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        key_column_selector = ttk.Combobox(frame)
        key_column_selector.grid(row=4, column=1, padx=5, pady=5)

        # Populate file listboxes
        file_pattern = os.path.join(self.temp_dir, "*")
        files = glob.glob(file_pattern)
        for file_path in files:
            file_name = os.path.basename(file_path)
            target_file_listbox.insert(tk.END, file_name)
            source_file_listbox.insert(tk.END, file_name)

        def load_columns_for_file(event, listbox, column_selector):
            selected_index = listbox.curselection()
            if selected_index:
                selected_file = listbox.get(selected_index[0])
                file_path = os.path.join(self.temp_dir, selected_file)
                try:
                    df = pd.read_excel(file_path, nrows=0) if file_path.endswith('.xlsx') else pd.read_csv(file_path, nrows=0)
                    column_selector['values'] = df.columns.tolist()
                except Exception as e:
                    messagebox.showerror("Error", f"Unable to load columns from {selected_file}: {str(e)}")

        target_file_listbox.bind('<<ListboxSelect>>', lambda e: load_columns_for_file(e, target_file_listbox, target_id_column_selector))
        source_file_listbox.bind('<<ListboxSelect>>', lambda e: load_columns_for_file(e, source_file_listbox, source_id_column_selector))
        source_file_listbox.bind('<<ListboxSelect>>', lambda e: load_columns_for_file(e, source_file_listbox, key_column_selector))

        # Confirm button
        def confirm_single_file_selection(self):
            selected_files = [filename for filename, var in self.file_vars.items() if var.get()]
            if selected_files:
                missing_key_files, errors = verify_key_column(selected_files, self.temp_dir, self.key_column)
                if missing_key_files:
                    messagebox.showinfo("Missing Key Column", f"Missing key column in files: {', '.join(missing_key_files)}")
                if errors:
                    messagebox.showerror("File Load Error", "\n".join(errors))
            else:
                messagebox.showerror("Error", "Please select at least one file to merge.")

        ttk.Button(frame, text="Confirm and Add Key Column", command=confirm_single_file_selection).grid(row=5, column=0, columnspan=2, padx=5, pady=10)

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            copy_files_to_temp(folder_path, self.temp_dir, self.progress, self.file_listbox, self.root)
            self.notebook.select(self.step2)  # Move to next step

    def update_file_listbox(self):
        self.file_listbox.delete(0, tk.END)
        file_pattern = os.path.join(self.temp_dir, "*")
        files = glob.glob(file_pattern)
        for file_path in files:
            self.file_listbox.insert(tk.END, os.path.basename(file_path))


    def on_file_confirm(self):
        selection = self.file_listbox.curselection()
        if selection:
            file_name = self.file_listbox.get(selection[0])
            file_path = os.path.join(self.temp_dir, file_name)
            self.master_key_file=file_path
            self.df, error = load_file(file_path)
            if self.df is not None:
                self.column_selector['values'] = self.df.columns.tolist()
                self.notebook.select(self.step3)  # Move to next step
                setup_treeview(self.df, self.treeview)  # Setup Treeview with DataFrame
            else:
                messagebox.showerror("Error", error)