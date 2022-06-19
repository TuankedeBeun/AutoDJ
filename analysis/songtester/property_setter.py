import os
import csv
import tkinter as tk
import numpy as np
from time import localtime
import pydub
import pyaudio
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

#TODO: csv writer should use ; delimiter
#TODO: csv writer should overwrite existing data
#TODO: set cursor at specific location (maybe drag)
#TODO: a set drop start/end must indicate a beep sound

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
        self.songs = self.load_songs()
        self.total_songs = len(self.songs)
        self.datafilepath = None
        self.initiate_data_file()

    def initiate_data_file(self):
        now = localtime() #TODO: probably easier way to get a default date string
        filename = "analysis_{folder:s}_{day:s}-{month:s}-{year:s}T{hour:s}-{min:s}-{sec:s}.csv"
        filename_formatted = filename.format(
            folder = os.path.basename(self.folderpath),
            day = str(now.tm_mday).zfill(2),
            month = str(now.tm_mon).zfill(2),
            year = str(now.tm_year).zfill(4),
            hour = str(now.tm_hour).zfill(2),
            min = str(now.tm_min).zfill(2),
            sec = str(now.tm_sec).zfill(2)
        )
        self.datafilepath = self.datafolder + '/' + filename_formatted
        csv_file = open(self.datafilepath, mode='w')
        writer = csv.writer(csv_file, delimiter=';') #TODO: delimiter is not yet ;
        writer.writerow(["song_path", "drop start", "drop end", "key"])
        csv_file.close()

    def load_songs(self):
        song_file_names = os.listdir(self.folderpath)
        songs = []

        # only keep mp3 songs
        for filename in song_file_names:
            if (filename[-4:] == '.mp3'):
                song = Song(self.folderpath, filename, 0, 0, 'None')
                songs.append(song)

        return songs

    def save(self):
        csv_file = open(self.datafilepath, mode='a')
        writer = csv.writer(csv_file)

        for song in self.songs:
            print('saving | ' + song.filename)
            writer.writerow(song.to_list())

        csv_file.close()


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
        self.current_tone = tk.StringVar(value='A')
        self.current_mode = tk.StringVar(value='major')
        self.current_key = tk.StringVar(value='None')
        self.audioplayer = None

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
        self.geometry("{width}x{height}+350+50".format(width = width, height = height))
        self.resizable(False, False)
        self.title('Song analyser')
        self.rowconfigure(3, weight=4)
        self.configure(background=colors['bg'])
        
        # song title
        self.songtitle = tk.Label(text = 'Artist - Song title', fg='white', bg=colors['bg'], font=('cambria', 25), wraplength=400)
        self.songtitle.grid(row=0, rowspan=3, columnspan=3)

        # load figure for audio signal
        self.fig = Figure(figsize=(8, 2.5), dpi=100)
        self.axis = self.fig.add_subplot(111)
        t = np.arange(0, 3, .01)
        self.axis.plot(t, 2 * np.sin(2 * np.pi * t))

        # create canvas for figure
        figure_frame = tk.Frame(master=self)
        figure_frame.grid(row=3, columnspan=6, sticky=tk.W)
        canvas = FigureCanvasTkAgg(self.fig, master=figure_frame)  # A tk.DrawingArea
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

        # set drop buttons
        img_button = tk.PhotoImage(file='./images/button.png')
        tk.Button(self, command=self.set_drop_start, image=img_button, compound='center', text='Set drop start', fg='white', bg=colors['bg'], bd=0, font=('cambria', 15)).grid(row=4, column=2)
        tk.Button(self, command=self.set_drop_end, image=img_button, compound='center', text='Set drop end', fg='white', bg=colors['bg'], bd=0, font=('cambria', 15)).grid(row=4, column=3)

        # set key option menus
        keys = ('A','B','C','D','E','F','G')
        modes = ('major', 'minor')
        tk.OptionMenu(self, self.current_tone, *keys, command=self.set_key).grid(row=4, column=4)
        tk.OptionMenu(self, self.current_mode, *modes, command=self.set_key).grid(row=4, column=5)

        # set piano
        img_piano = tk.PhotoImage(file='./images/piano_icon.png')
        tk.Button(self, command=self.open_piano, bg=colors['bg'], bd=0, image=img_piano).grid(row=0, rowspan=3, column=5)

        # previous / play / pause / reset / next buttons
        img_previous = tk.PhotoImage(file='./images/previous_icon.png')
        tk.Button(self, command=self.previous_song, bg=colors['bg'], bd=0, image=img_previous).grid(row=5, column=0, columnspan=2)

        img_play = tk.PhotoImage(file='./images/play_icon.png')
        tk.Button(self, command=self.play, bg=colors['bg'], bd=0, image=img_play).grid(row=5, column=2)

        img_pause = tk.PhotoImage(file='./images/pause_icon.png')
        tk.Button(self, command=self.pause, bg=colors['bg'], bd=0, image=img_pause).grid(row=5, column=3)

        img_reset = tk.PhotoImage(file='./images/restart_icon.png')
        tk.Button(self, command=self.reset, bg=colors['bg'], bd=0, image=img_reset).grid(row=5, column=4)
        
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
        time = np.linspace(0, int(audiosegment.duration_seconds), audio_np_sparse.size)
        self.axis.clear()
        self.axis.plot(time, audio_np_sparse)
        self.axis.set_xlim((0, time.max()))
        cursor = self.axis.axvline(linewidth=2, color='r')
        self.canvas.draw()

        # set song properties to display on screen
        self.current_dropstart.set(self.current_song.dropstart)
        self.current_dropend.set(self.current_song.dropend)
        self.current_key.set(self.current_song.key)

        # instantiate audio player
        print('loading audio player')
        self.audioplayer = AudioPlayer(self, audiosegment, cursor)

        print('loaded')

    def save_data(self):
        if isinstance(self.song_folder, SongFolder):
            print('Saving')
            self.song_folder.save()
        else:
            tk.messagebox.showinfo('Fill properties')

    def set_drop_start(self):
        if isinstance(self.audioplayer, AudioPlayer):
            dropstart = round(self.audioplayer.now, 3)
            self.current_dropstart.set(dropstart)
            self.current_song.dropstart = dropstart

    def set_drop_end(self):
        if isinstance(self.audioplayer, AudioPlayer):
            dropend = round(self.audioplayer.now, 3)
            self.current_dropend.set(dropend)
            self.current_song.dropend = dropend

    def set_key(self, event):
        key = self.current_tone.get()

        if self.current_mode.get() == 'minor':
            key += 'm'
        
        self.current_key.set(key)
        self.current_song.key = key

    def open_piano(self):
        pass

    def previous_song(self):
        self.pause()

        if (self.song_nr > 0):
            self.song_nr -= 1
            self.load_song()
    
    def next_song(self):
        self.pause()

        if (self.song_nr < self.song_folder.total_songs - 1):
            self.song_nr += 1
            self.load_song()

    def play(self):
        if isinstance(self.audioplayer, AudioPlayer):
            self.audioplayer.play(*self.axis.get_xlim())

    def pause(self):
        if isinstance(self.audioplayer, AudioPlayer):
            self.audioplayer.pause()

    def reset(self):
        if isinstance(self.audioplayer, AudioPlayer):
            self.audioplayer.reset()

class AudioPlayer():
    def __init__(self, root, audio, cursor):
        self.root = root
        self.audio = audio
        self.cursor = cursor
        self.start = 0
        self.end = int(self.audio.duration_seconds)
        self.now = 0
        self.playing = False
        self.paused = False
        self.interval = 0.1

        # set up pyaudio stream
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format = self.p.get_format_from_width(audio.sample_width),
            channels = audio.channels,
            rate = audio.frame_rate,
            frames_per_buffer = 10000,
            output = True)

    def play(self, start, end):
        self.paused = False

        if (not self.playing) or ((self.start, self.end) != (start, end)):
            # playing from start of the interval
            self.start = start
            self.end = end
            self.now = start
            self.playing = True
            print('Playing')

        while (self.now < self.end) and not self.paused:
            # write audio data to pyaudio stream
            data = self.audio[self.now*1000: (self.now + self.interval)*1000]._data
            self.stream.write(data)

            # update cursor
            print('time = ' + str(self.now))
            self.cursor.set_xdata(self.now)
            self.root.canvas.draw_idle()
            self.root.update()
            self.now += self.interval
        
        if self.now >= self.end:
            self.playing = False

    def pause(self):
        self.paused = True

    def reset(self):
        self.now = self.start

        if self.paused:
            self.cursor.set_xdata(self.now)
            self.root.canvas.draw_idle()
            self.root.update()

tester = PropertySetter()