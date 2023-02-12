from analysis_functions import analyse_song
import tkinter as tk
from tkinter.filedialog import askopenfilename
from os.path import split

# Get song via file dialog
root = tk.Tk()
root.withdraw()
full_path = askopenfilename()

# Analyse song
folder_path, file_path = split(full_path)
properties = analyse_song(folder_path, file_path, plotting=True, play_drop=False, printing=True)
