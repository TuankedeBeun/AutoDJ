import os
import csv
import tkinter as tk
import numpy as np
from time import localtime
import pydub
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

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

class Song():
    def __init__(self, folderpath, filename, dropstart, dropend, key):
        self.folderpath = folderpath
        self.filename = filename
        self.filepath = folderpath + '/' + filename
        self.dropstart = dropstart
        self.dropend = dropend
        self.key = key

    def to_list(self):
        return [self.filename, self.dropstart, self.dropend, self.key]

class SongFolder():
    def __init__(self, folderpath, datafolder='C:/Users/tuank/Programming/Python/AutoDJ/analysis/songtester/data'):
        self.folderpath = folderpath
        self.datafolder = datafolder
        self.writer = self.initiate_data_file()
        self.songs = self.load_songs()
        self.total_songs = len(self.songs)

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
        datafilepath = self.datafolder + '/' + filename_formatted
        csv_file = open(datafilepath, mode='w')
        writer = csv.writer(csv_file)
        writer.writerow(["song_path", "drop start", "drop end", "key"])
        return writer

    def load_songs(self):
        song_file_names = os.listdir(self.folderpath)
        songs = []

        # only keep mp3 songs
        for filename in song_file_names:
            if (filename[-4:] == '.mp3'):
                song = Song(self.folderpath, filename, 0, 0, None)
                songs.append(song)

        return songs

    def save(self):
        for song in self.songs:
            self.writer.writerow(song.to_list())


class PropertySetter(tk.Tk):
    def __init__(self):
        super().__init__()

        # define properties
        self.default_music_directory = 'C:/Users/tuank/Music/Drum & Bass/'
        self.song_nr = 0
        self.song_folder = None
        self.song_paths = []
        self.song_pdb = None
        self.music_folder = None
        self.current_song = None
        self.current_dropstart = tk.IntVar(value=0)
        self.current_dropend = tk.IntVar(value=0)
        self.current_key = tk.StringVar(value='None')

        # create data file
        self.create_GUI()
        
    def create_GUI(self, width=800, height=700):
        # colors
        colors = {
            'bg': '#444444',
            'button': '#FFC000',
            'blue': '#4472C4'
        }
        
        # initiate window
        self.geometry("{width}x{height}".format(width = width, height = height))
        self.resizable(False, False)
        self.title('Song analyser')
        self.rowconfigure(3, weight=4)
        self.configure(background=colors['bg'])
        
        # song title
        self.songtitle = tk.Label(text = 'Artist - Song title', fg='white', bg=colors['bg'], font=('cambria', 25), wraplength=400)
        self.songtitle.grid(row=0, rowspan=3, columnspan=3)

        # load figure for audio signal
        fig = Figure(figsize=(8, 2.5), dpi=100)
        self.axis = fig.add_subplot(111)
        t = np.arange(0, 3, .01)
        self.axis.plot(t, 2 * np.sin(2 * np.pi * t))

        # create canvas for figure
        figure_frame = tk.Frame(master=self)
        figure_frame.grid(row=3, columnspan=6, sticky=tk.W)
        canvas = FigureCanvasTkAgg(fig, master=figure_frame)  # A tk.DrawingArea
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        # create toolbar
        toolbar = NavigationToolbar2Tk(canvas, figure_frame)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        def on_key_press(event):
            print("you pressed {}".format(event.key))
            key_press_handler(event, canvas, toolbar)

        canvas.mpl_connect("key_press_event", on_key_press)
        self.canvas = canvas

        # info text
        tk.Label(self, text='drop start', font=('cambria', 15), fg='white', bg=colors['bg']).grid(row=0, column=3)
        tk.Label(self, text='drop end', font=('cambria', 15), fg='white', bg=colors['bg']).grid(row=1, column=3)
        tk.Label(self, text='key', font=('cambria', 15), fg='white', bg=colors['bg']).grid(row=2, column=3)

        tk.Label(self, textvariable=self.current_dropstart, font=('cambria', 15), fg='white', bg=colors['bg']).grid(row=0, column=4)
        tk.Label(self, textvariable=self.current_dropend, font=('cambria', 15), fg='white', bg=colors['bg']).grid(row=1, column=4)
        tk.Label(self, textvariable=self.current_key, font=('cambria', 15), fg='white', bg=colors['bg']).grid(row=2, column=4)

        # folder
        img_folder = tk.PhotoImage(file='./images/folder_icon.png')
        tk.Button(self, command=self.open_folder, bg=colors['bg'], bd=0, image=img_folder).grid(row=4, column=0)

        # saving button
        img_file = tk.PhotoImage(file='./images/file_icon.png')
        tk.Button(self, command=self.save_data, bg=colors['bg'], bd=0, image=img_file).grid(row=4, column=1)

        # set buttons
        img_button = tk.PhotoImage(file='./images/button.png')
        tk.Button(self, command=self.set_drop_start, image=img_button, compound='center', text='Set drop start', fg='white', bg=colors['bg'], bd=0, font=('cambria', 15)).grid(row=4, column=2)
        tk.Button(self, command=self.set_drop_end, image=img_button, compound='center', text='Set drop end', fg='white', bg=colors['bg'], bd=0, font=('cambria', 15)).grid(row=4, column=3)
        tk.OptionMenu(self, 'Key', 'A','B','C','D','E','F','G').grid(row=4, column=4)
        tk.OptionMenu(self, 'Mode', 'major', 'minor').grid(row=4, column=5)

        # set piano
        img_piano = tk.PhotoImage(file='./images/piano_icon.png')
        tk.Button(self, command=self.open_piano, bg=colors['bg'], bd=0, image=img_piano).grid(row=0, rowspan=3, column=5)

        # previous / play / pause / restart / next buttons
        img_previous = tk.PhotoImage(file='./images/previous_icon.png')
        tk.Button(self, command=self.previous_song, bg=colors['bg'], bd=0, image=img_previous).grid(row=5, column=0, columnspan=2)

        img_play = tk.PhotoImage(file='./images/play_icon.png')
        tk.Button(self, command=self.play, bg=colors['bg'], bd=0, image=img_play).grid(row=5, column=2)

        img_pause = tk.PhotoImage(file='./images/pause_icon.png')
        tk.Button(self, command=self.pause, bg=colors['bg'], bd=0, image=img_pause).grid(row=5, column=3)

        img_restart = tk.PhotoImage(file='./images/restart_icon.png')
        tk.Button(self, command=self.restart, bg=colors['bg'], bd=0, image=img_restart).grid(row=5, column=4)
        
        img_next = tk.PhotoImage(file='./images/next_icon.png')
        tk.Button(self, command=self.next_song, bg=colors['bg'], bd=0, image=img_next).grid(row=5, column=5, columnspan=2)

        self.mainloop()
        
        return

    def open_folder(self):
        # load songs in chosen directory
        self.music_folder = tk.filedialog.askdirectory(initialdir=self.default_music_directory)
        self.song_folder = SongFolder(self.music_folder)
        self.load_song()
        return
    
    def load_song(self):
        self.current_song = self.song_folder.songs[self.song_nr]
        self.songtitle.config(text = self.current_song.filename[:-4])
        
        print('loading song ' + self.current_song.filename)
        # reads mp3 file and converts it into pydub's AudioSegment datatype
        audiosegment = pydub.AudioSegment.from_mp3(self.current_song.filepath)
        print('converting to numpy array')
        audio_np = np.array(audiosegment.get_array_of_samples())
        audio_np = audio_np.reshape((-1, 2)).sum(axis=1)
        audio_np_sparse = audio_np[::1000]

        # plotting
        print('plotting')
        time = np.linspace(0, audiosegment.duration_seconds, audio_np_sparse.size)
        self.axis.clear()
        self.axis.plot(time, audio_np_sparse)
        self.axis.set_xlim((0, time.max()))
        self.canvas.draw()

        # set song properties to display on screen
        self.current_dropstart.set(self.current_song.dropstart)
        self.current_dropend.set(self.current_song.dropend)
        self.current_key.set(self.current_song.key)
        print('loaded')

    def save_data(self):
        if (self.song_folder == None):
            tk.messagebox.showinfo('Fill properties')
        else:
            self.song_folder.save()

    def set_drop_start(self):
        pass

    def set_drop_end(self):
        pass

    def set_key(self):
        pass

    def open_piano(self):
        pass

    def previous_song(self):
        if (self.song_nr > 0):
            self.song_nr -= 1
            self.load_song()
    
    def next_song(self):
        if (self.song_nr < self.song_folder.total_songs - 1):
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