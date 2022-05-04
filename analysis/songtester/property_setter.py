import os
import csv
import tkinter as tk
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
from time import localtime

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

        # define properties
        self.default_music_directory = 'C:/Users/tuank/Music/Drum & Bass/'
        self.song_nr = 0
        self.song_paths = []
        self.song_pdb = None
        self.current_song = {
            'song_path' : None,
            'drop_start' : None,
            'drop_end' : None,
            'key' : None
        }

        # create data file
        self.writer = self.initiate_data_file()
        self.create_GUI()
        
    def create_GUI(self, width=1200, height=600):
        # colors
        colors = {
            'bg': '#B4C7E7',
            'button': '#FFC000',
            'blue': '#4472C4'
        }
        
        # initiate window
        self.geometry("{width}x{height}".format(width = width, height = height))
        self.resizable(False, False)
        self.title('Song analyser')
        self.rowconfigure(1, weight=2)
        self.configure(background=colors['bg'])
        
        # song title
        self.songtitle = tk.Label(text = 'Artist - Song title', bg=colors['bg'], font=('cambria', 40), wraplength=width-100)
        self.songtitle.grid(row=0, columnspan=7)
        
        def resize_image(file_path, factor):
            img = Image.open(file_path)
            img_resized = img.resize((round(img.size[0]*factor), round(img.size[1]*factor)))
            img_tk = ImageTk.PhotoImage(image=img_resized)
            return img_tk

        # graph
        img_graph = resize_image('./images/dummy_graph.png', 0.5)
        tk.Label(self, bg=colors['bg'], image=img_graph).grid(row=1, columnspan=5)

        # info text
        text = '''
        Drop start:\t00:00:00
        Drop end:\t00:00:00
        Key:\t\t-'''
        tk.Label(self, text=text, font=('cambria', 20), bg=colors['bg'], justify=tk.LEFT).grid(row=1, column=5, columnspan=2, sticky=tk.W)

        # folder
        img_folder = tk.PhotoImage(file='./images/folder_icon.png')
        tk.Button(self, command=self.open_folder, bg=colors['bg'], bd=0, image=img_folder).grid(row=2, column=0)

        # saving button
        img_file = tk.PhotoImage(file='./images/file_icon.png')
        tk.Button(self, command=self.save_song, bg=colors['bg'], bd=0, image=img_file).grid(row=2, column=1)

        # set buttons
        tk.Button(self, command=self.set_drop_start, text='Set drop start', bg=colors['button'], font=('cambria', 15), width=15).grid(row=2, column=2)
        tk.Button(self, command=self.set_drop_end, text='Set drop end', bg=colors['button'], font=('cambria', 15), width=15).grid(row=2, column=3)
        tk.OptionMenu(self, 'Set key', 'A','B','C').grid(row=2, column=4)

        # set piano
        img_piano = tk.PhotoImage(file='./images/piano_icon.png')
        tk.Button(self, command=self.open_piano, bg=colors['bg'], bd=0, image=img_piano).grid(row=2, column=6)

        # previous / play / pause / restart / next buttons
        resize_factor = 0.5

        img_previous = resize_image('./images/previous_icon.png', resize_factor)
        tk.Button(self, command=self.previous_song, bg=colors['bg'], bd=0, image=img_previous).grid(row=3, column=0, columnspan=2)

        img_play = resize_image('./images/play_icon.png', resize_factor)
        tk.Button(self, command=self.play, bg=colors['bg'], bd=0, image=img_play).grid(row=3, column=2)

        img_pause = resize_image('./images/pause_icon.png', resize_factor)
        tk.Button(self, command=self.pause, bg=colors['bg'], bd=0, image=img_pause).grid(row=3, column=3)

        img_restart = resize_image('./images/restart_icon.png', resize_factor)
        tk.Button(self, command=self.restart, bg=colors['bg'], bd=0, image=img_restart).grid(row=3, column=4)
        
        img_next = resize_image('./images/next_icon.png', resize_factor)
        tk.Button(self, command=self.next_song, bg=colors['bg'], bd=0, image=img_next).grid(row=3, column=5, columnspan=2)

        self.mainloop()
        
        return

    def initiate_data_file(self):
        now = localtime()
        filename = "analysis_{day:2d}{month:2d}{year:4d}-{hour:2d}:{min:2d}.csv"
        filename_formatted = filename.format(
            day = now.tm_mday,
            month = now.tm_mon,
            year = now.tm_year,
            hour = now.tm_hour,
            min = now.tm_min
            )
        csv_file = open(filename_formatted, mode='w')
        writer = csv.writer(csv_file)
        writer.writerow(["song_path", "drop start", "drop end", "key"])
        return writer

    def open_folder(self):
        # load songs in chosen directory
        music_folder = tk.filedialog.askdirectory(initialdir=self.default_music_directory)
        songs = os.listdir(music_folder)

        # only keep mp3 songs
        for song in songs:
            if (song[-4:] != '.mp3'):
                songs.remove(song)
        
        self.song_paths = songs
        self.load_song()
        return
    
    def load_song(self):
        self.current_song['song_path'] = self.song_paths[self.song_nr]
        self.songtitle.config(text = self.current_song['song_path'][:-4])

    def save_song(self):
        #TODO: implement check if song is already saved --> overwrite
        if (None in self.current_song.values()):
            tk.messagebox.showinfo('Fill properties')
        else:
            self.writer.writerow([self.song_paths[self.song_nr]])

    def set_drop_start(self):
        pass

    def set_drop_end(self):
        pass

    def set_key(self):
        pass

    def open_piano(self):
        pass

    def previous_song(self):
        #TODO: load song if already in csv file
        if (self.song_nr > 0):
            self.song_nr -= 1
            self.load_song()
    
    def next_song(self):
        #TODO: load song if already in csv file
        if (self.song_nr < len(self.song_paths) - 1):
            self.song_nr += 1
            self.load_song()

    def play(self, event):
        pass

    def pause(self, event):
        pass

    def restart(self, event):
        pass

    def select_region(self, event):
        pass

tester = PropertySetter()