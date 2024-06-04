import tkinter as tk
import glob
from ttkthemes import ThemedTk
from ui import DataMatcherApp
from operations import clear_temp_directory

def main():
    clear_temp_directory()
    root = ThemedTk(theme="adapta")
    root.title("Data Matcher Wizard")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = int(screen_width / 1.2)
    window_height = int(screen_height / 1.2)
    x_position = (screen_width - window_width) // 2  # Center the window
    y_position = (screen_height - window_height) // 2  # Center the window
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
    root.resizable(True, True)
    app = DataMatcherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()