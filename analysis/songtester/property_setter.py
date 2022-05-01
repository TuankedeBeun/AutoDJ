import os
import tkinter as tk
import matplotlib.pyplot as plt
from PIL import Image, ImageTk


'''
Classes for setting song properties by listening and manually asserting data
- GUI class:
    * Tkinter window
    * graphs Global Power History with matplotlib
    * button for choosing directory
    * button for previous/next song
    * user can set start/end times
    * buttons for play/pause/reset
    * button for setting drop start (set a peep-sound)
    * button for setting drop end (set a peep-sound)
    * button for opening small piano keyboard
    * drop down menu for setting key
    * on screen record of current and saved properties
    * button for saving current data
    * pop-up message when clicking prev/next without saving
    * connected with Data Manager

- Data Manager class:
    * automatically loads existing data
    * functions for:
        - returning saved data
        - saving data
'''

os.chdir('C:\\Users\\tuank\\Programming\\Python\\AutoDJ\\analysis\\songtester')

class PropertySetter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.create_GUI()
        
    def create_GUI(self, width=1600, height=900):
        # packing manager: grid
        
        # colors
        colors = {
            'bg': '#B4C7E7',
            'button': '#FFC000',
            'blue': '#4472C4'
        }
        
        # initiate window
        self.title('Song analyser')
        self.rowconfigure(1, weight=2)
        self.configure(background=colors['bg'])
        
        # song title
        txt_songtitle = tk.Label(text = 'Artist - Song title', bg=colors['bg'], font=('cambria', 50))
        txt_songtitle.grid(row=0, columnspan=4)
        
        # graph
        img_graph = Image.open('./images/dummy_graph.png')
        resize_factor = 0.5
        img_graph = img_graph.resize((round(img_graph.size[0]*resize_factor), round(img_graph.size[1]*resize_factor)))
        tkImage = ImageTk.PhotoImage(image=img_graph)
        tk.Label(self, bg=colors['bg'], image=tkImage).grid(row=1, columnspan=5)

        # info text
        text = '''
        Drop start:\t01:02:14
        Drop end:\t01:54:01
        Key:\t\tBm'''
        tk.Label(self, text=text, font=('cambria', 20), bg=colors['bg'], justify=tk.LEFT).grid(row=1, column=5, columnspan=2, sticky=tk.W)

        # folder
        img_folder = tk.PhotoImage(file='./images/folder_icon.png')
        tk.Button(self, bg=colors['bg'], bd=0, image=img_folder).grid(row=2, column=0)

        # saving button
        img_file = tk.PhotoImage(file='./images/file_icon.png')
        tk.Button(self, bg=colors['bg'], bd=0, image=img_file).grid(row=2, column=1)

        # set buttons
        tk.Button(self, text='Set drop start', bg=colors['button']).grid(row=2, column=2)
        tk.Button(self, text='Set drop end', bg=colors['button']).grid(row=2, column=3)
        tk.OptionMenu(self, 'Set key', 'A','B','C').grid(row=2, column=4)

        # set piano
        img_piano = tk.PhotoImage(file='./images/piano_icon.png')
        tk.Button(self, bg=colors['bg'], bd=0, image=img_piano).grid(row=2, column=6)

        # previous / play / pause / restart / next buttons
        img_previous = tk.PhotoImage(file='./images/previous_icon.png')
        tk.Button(self, bg=colors['bg'], bd=0, image=img_previous).grid(row=3, column=0, columnspan=2)

        img_play = tk.PhotoImage(file='./images/play_icon.png')
        tk.Button(self, bg=colors['bg'], bd=0, image=img_play).grid(row=3, column=2)

        img_pause = tk.PhotoImage(file='./images/pause_icon.png')
        tk.Button(self, bg=colors['bg'], bd=0, image=img_pause).grid(row=3, column=3)

        img_restart = tk.PhotoImage(file='./images/restart_icon.png')
        tk.Button(self, bg=colors['bg'], bd=0, image=img_restart).grid(row=3, column=4)
        
        img_next = tk.PhotoImage(file='./images/next_icon.png')
        tk.Button(self, bg=colors['bg'], bd=0, image=img_next).grid(row=3, column=5, columnspan=2)

        self.mainloop()
        
        return


tester = PropertySetter()