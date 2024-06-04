import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import shutil
import os
import threading

class DataMatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Matcher Wizard")
        self.root.geometry("600x400")  # Set the fixed window size
        self.root.resizable(False, False)  # Prevent resizing

        # Initialize temp directory
        self.temp_dir = os.path.join(os.getcwd(), "temp_files")
        os.makedirs(self.temp_dir, exist_ok=True)

        # Setup GUI steps
        self.setup_steps()

        # Variables
        self.df = None  # Pandas DataFrame

    def setup_steps(self):
        # Step 1: Folder selection
        self.step1 = tk.Frame(self.root)
        self.step1.pack(fill='both', expand=True)
        
        tk.Label(self.step1, text="Step 1: Select a Folder").pack(pady=10)
        tk.Button(self.step1, text="Select Folder", command=self.select_folder).pack()
        self.progress = ttk.Progressbar(self.step1, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(pady=20)

        # Step 2: File selection
        self.step2 = tk.Frame(self.root)
        self.file_listbox = tk.Listbox(self.step2, height=5)
        self.file_listbox.pack(fill='x', pady=20)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        # Step 3: Key column selection and data preview
        self.step3 = tk.Frame(self.root)
        tk.Label(self.step3, text="Step 3: Select Key Column and Preview Data").pack(pady=10)
        
        self.column_frame = tk.Frame(self.step3)
        self.column_frame.pack(fill='x', pady=5)
        self.column_selector = ttk.Combobox(self.column_frame)
        self.column_selector.pack(side='left', fill='x', expand=True)
        self.btn_choose_column = tk.Button(self.column_frame, text="Choose Column", command=self.confirm_column_selection)
        self.btn_choose_column.pack(side='right', padx=10)
        
        self.preview_tree = ttk.Treeview(self.step3)
        self.preview_tree.pack(fill='both', expand=True, pady=20)

        # Initially, only step 1 is visible
        self.step2.pack_forget()
        self.step3.pack_forget()

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            threading.Thread(target=self.copy_files_to_temp, args=(folder_path,)).start()

    def copy_files_to_temp(self, folder_path):
        files = os.listdir(folder_path)
        num_files = len(files)
        self.progress['value'] = 0
        self.progress['maximum'] = num_files

        for i, filename in enumerate(files):
            src_path = os.path.join(folder_path, filename)
            dest_path = os.path.join(self.temp_dir, filename)
            if os.path.isfile(src_path):
                shutil.copy(src_path, dest_path)
                self.progress['value'] = i + 1
                self.file_listbox.insert(tk.END, filename)
            self.root.update_idletasks()

        self.step1.pack_forget()
        self.step2.pack(fill='both', expand=True)

    def on_file_select(self, event):
        try:
            widget = event.widget
            if widget.curselection():  # Ensure there is a selection
                index = int(widget.curselection()[0])
                file_name = widget.get(index)
                file_path = os.path.join(self.temp_dir, file_name)
                self.load_and_preview_file(file_path)
                self.step2.pack_forget()
                self.step3.pack(fill='both', expand=True)
            else:
                messagebox.showinfo("Info", "Please select a file from the list.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load the file: {e}")


    def load_and_preview_file(self, file_path):
        try:
            if file_path.endswith('.xlsx'):
                self.df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                self.df = pd.read_csv(file_path)
            else:
                messagebox.showerror("Error", "Unsupported file format.")
                return
            self.display_dataframe(self.df)
            self.column_selector['values'] = self.df.columns.tolist()
        except Exception as e:
            messagebox.showerror("Error", f"Error reading file: {e}")

    def display_dataframe(self, df):
        for i in self.preview_tree.get_children():
            self.preview_tree.delete(i)

        self.preview_tree["column"] = list(df.columns)
        self.preview_tree["show"] = "headings"
        for col in self.preview_tree["column"]:
            self.preview_tree.heading(col, text=col)

        for row in df.head(5).to_records(index=False):
            self.preview_tree.insert("", "end", values=list(row))

    def confirm_column_selection(self):
        if self.column_selector.get():
            self.key_column = self.column_selector.get()
            messagebox.showinfo("Key Column Selected", f"Key Column: {self.key_column}")
        else:
            messagebox.showerror("Error", "Please select a column first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DataMatcherApp(root)
    root.mainloop()