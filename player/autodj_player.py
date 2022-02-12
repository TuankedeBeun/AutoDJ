import os
import tkinter as tk
import numpy as np
import pyaudio
from pydub import AudioSegment
from time import sleep
from Auto_DJ_BPM import To_numpy, Power_history
import matplotlib.pyplot as plt

# TO DO
# - create ~10 mixing methods
#    - build up one - drop other and switch back
#    - 
# - improve beat matching by using new Power History function from V3
# - build in weights for chance to pick a certain mixing method
# - ticking noise at silent parts (Nymfo - Crystal Clear)


class Player():
    # This is the main DJ player class, which plays songs and mixes them.
    # It also comes with a GUI, in which you can set the directory to the music
    # files. There should already be a file containing all the drop/key data in
    # that folder.
    
    def __init__(self, folder, song1=False, song2=False, method=False):           
        # load music data
        self.folder = folder
        os.chdir(folder)
        self.properties, self.songlist = self.get_properties()
        self.Nsongs = len(self.songlist)
        self.unplayed = np.arange(self.Nsongs)
        
        # create GUI
        self.create_GUI() #creates songtitles/BPMs/keys
        
        # number of mixing methods
        self.mixing_methods = ['crossfade', 'drop end switch', 'drop-to-drop',
                               'double drop', 'cut drop', 'hpf dropfade',
                               'bass switch', 'drop background', 'start from drop']
        # list of keys
        self.key_names = ['A','Bb','B','C','Db','D','Eb','E','F','F#','G','Ab']
        
        # time tick size
        self.tick_step = 1/4
        
        # current track
        self.track_nr = 0                
        
        # placeholders
        self.song_nrs = [0, 0]
        self.songs = [None, None]
        self.framerates = [0, 0]
        self.BPMs = [0, 0]
        self.songstarts = [0, 0]
        self.dropstarts = [0, 0]
        self.dropends = [0, 0]
        self.keys = list(np.random.randint(0, 11, 2))
        self.dts = [1, 1]
        self.ticks = [0, 0]
        self.ms = [0, 0]
        
        # load in two new songs
        self.track_nr = 1
        self.next_song(next_song_nr=song1)
        self.track_nr = 0
        self.next_song(next_song_nr=song2)
        
        # set mixing method
        if method is not False:
            mix = self.mixing_methods[method]
            self.mix.set(mix)
            self.trans_in, self.trans_out, start_side = self.set_shift_times(mix)
            self.ticks[1] = start_side
        else:
            self.pick_mix()
        self.ms_time()
        self.set_beat_offset()
        
        # toggles
        self.loading = False
        self.paused = False
        self.streaming = False
        self.transitioning = False
        
        # initiate stream
        self.stream()
        
        # keep GUI window open
        self.canvas.update()
        self.canvas.mainloop()
        
        return
    
    def create_GUI(self):
        # create GUI window with basic layout and:
        # - play & stop button
        # - instant switch button (optional)
        # - choose next song
        # - playing info
        
        # some coordinates
        width = 1200
        height = 600
        xcenter1 = 500
        xcenter2 = 700
        xmid1 = 250
        xmid2 = 950
        ymid = 250
        ybottom = 525
        
        # colors
        bg_color = '#333333'
        wheel = '#222222'
        white = '#cccccc'
        red = '#881111'
        purple = '#771188'
        blue = '#061655'  
        green = '#22bb11'
        orange = '#997711'
        slider = '#ccaa22'
        
        # initiate window
        self.root = tk.Tk()
        self.root.title('Automatic DJ')
        self.canvas = tk.Canvas(self.root, width=width, heigh=height)
        
        # LAYOUT
        # background
        self.canvas.create_rectangle(0, 0, width, height, fill=bg_color)
        self.canvas.create_line(xcenter1, 0, xcenter1, height, fill=white)
        self.canvas.create_line(xcenter2, 0, xcenter2, height, fill=white)
        self.canvas.create_text(width/2, 50, text='Auto DJ',
                                font=('Calisto', 35, 'italic'), 
                                anchor=tk.CENTER, fill=white)
        self.canvas.create_text(80, 50, text='Track 1',
                                font=('Calisto', 25), 
                                anchor=tk.CENTER, fill=white)
        self.canvas.create_text(width-80, 50, text='Track 2',
                                font=('Calisto', 25), 
                                anchor=tk.CENTER, fill=white)
        # wheel 1
        self.canvas.create_oval(xmid1-200, ymid-200, xmid1+200, ymid+200, fill=wheel, outline=white, width=10)
        self.canvas.create_oval(xmid1-45, ymid-45, xmid1+45, ymid+45, outline=white, width=2)
        self.canvas.create_oval(xmid1-30, ymid-30, xmid1+30, ymid+30, outline=bg_color, width=16)
        self.canvas.create_oval(xmid1-7, ymid-7, xmid1+7, ymid+7, outline=white, width=4)
        # wheel 2
        self.canvas.create_oval(xmid2-200, ymid-200, xmid2+200, ymid+200, fill=wheel, outline=white, width=10)
        self.canvas.create_oval(xmid2-45, ymid-45, xmid2+45, ymid+45, outline=white, width=2)
        self.canvas.create_oval(xmid2-30, ymid-30, xmid2+30, ymid+30, outline=bg_color, width=16)
        self.canvas.create_oval(xmid2-7, ymid-7, xmid2+7, ymid+7, outline=white, width=4)
        
        # info box 1
        self.canvas.create_rectangle(30, ybottom+50, xcenter1-170, ybottom-50, fill=wheel, outline=red, width=5)
        self.canvas.create_rectangle(xcenter1-150, ybottom-80, xcenter1-30, ybottom-20, fill=wheel, outline=purple, width=5)
        self.canvas.create_rectangle(xcenter1-150, ybottom-10, xcenter1-30, ybottom+50, fill=wheel, outline=blue, width=5)
        # info box 2
        self.canvas.create_rectangle(xcenter2+30, ybottom+50, width-170, ybottom-50, fill=wheel, outline=red, width=5)
        self.canvas.create_rectangle(width-150, ybottom-80, width-30, ybottom-20, fill=wheel, outline=purple, width=5)
        self.canvas.create_rectangle(width-150, ybottom-10, width-30, ybottom+50, fill=wheel, outline=blue, width=5)
        
        # play button
        play_button = tk.Button(self.canvas, text='Play', command=self.play, 
                            font=('Calisto', 26, 'italic'), width=5, bg=green)
        play_button.place(x=width/2, y=150, anchor=tk.CENTER)
        
        # pause button
        pause_button = tk.Button(self.canvas, text='Pause', command=self.pause,
                            font=('Calisto', 18, 'italic'), width=5, bg=orange)
        pause_button.place(x=xcenter1+10, y=225, anchor=tk.W)
        
        # stop button
        stop_button = tk.Button(self.canvas, text='Stop', command=self.stop,
                            font=('Calisto', 18, 'italic'), width=5, bg=red)
        stop_button.place(x=xcenter2-10, y=225, anchor=tk.E)
        
        # song picking button
        self.pick_button = tk.Button(self.canvas, text='Pick', command=self.switch,
                                     font=('Calisto', 18, 'italic'), width=5, bg=blue,
                                     fg=white)
        self.pick_button.place(x=width/2, y=460, anchor=tk.CENTER)
                    
        # song picking menu within a new frame
        frame = tk.Frame(self.canvas, height=5, width=5, bd=2, bg=wheel)
        frame.place(x=width/2, y=260, anchor=tk.N)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        # scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.grid(row=0, column=1, sticky='ns')
        # listbox
        menu = tk.Listbox(frame, justify='left', width=22, height=8,
                          bg=wheel, fg=white, borderwidth=0,
                          yscrollcommand=scrollbar.set,
                          font=('Calisto', 11, 'italic'))
        menu.grid(row=0, column=0, sticky='nsew')
        # fill in entries
        for song in self.songlist:
            menu.insert('end', song)
        # couple command
        scrollbar.config(command=menu.yview)
        
        self.songpicker = menu
        
        # transition slider
        self.canvas.create_line(xcenter1+30, ybottom-25, xcenter1+30, ybottom+25, fill=orange, width=4)
        self.canvas.create_line(xcenter2-30, ybottom-25, xcenter2-30, ybottom+25, fill=orange, width=4)
        for i in range(11):
            x = xcenter1 + 30 + i/11*(xcenter2 - xcenter1 - 60)
            self.canvas.create_line(x, ybottom-25, x, ybottom+25, fill=orange, width=2)
        
        self.slider = self.canvas.create_rectangle(xcenter1+24, ybottom+20, 
                        xcenter1+36, ybottom-20, fill=wheel, outline=slider, width=2)
        
        # tkinter variables
        self.songs_tk = [tk.StringVar(self.canvas), tk.StringVar(self.canvas)]
        self.BPMs_tk = [tk.IntVar(self.canvas), tk.IntVar(self.canvas)]
        self.keys_tk = [tk.StringVar(self.canvas), tk.StringVar(self.canvas)]
        self.mix = tk.StringVar(self.canvas)
        self.Nsongsplayed = tk.IntVar(self.canvas, value=-2)
        self.streamtime = tk.StringVar(self.canvas, value='streamtime 00:00')
        
        # info text
        tk.Label(self.canvas, textvariable=self.songs_tk[0], font=('Calisto', 15), 
                 wraplength=260, justify='left',
                 bg=wheel, fg=white).place(x=50, y=ybottom, anchor=tk.W)
        tk.Label(self.canvas, textvariable=self.songs_tk[1], font=('Calisto', 15), 
                 wraplength=260, justify='left',
                 bg=wheel, fg=white).place(x=xcenter2+50, y=ybottom, anchor=tk.W)
        tk.Label(self.canvas, textvariable=self.BPMs_tk[0], font=('Calisto', 20), 
                 bg=wheel, fg=white).place(x=xcenter1-90, y=ybottom-50, anchor=tk.CENTER)
        tk.Label(self.canvas, textvariable=self.BPMs_tk[1], font=('Calisto', 20),
                 bg=wheel, fg=white).place(x=width-90, y=ybottom-50, anchor=tk.CENTER)
        tk.Label(self.canvas, textvariable=self.keys_tk[0], font=('Calisto', 20),
                 bg=wheel, fg=white).place(x=xcenter1-90, y=ybottom+20, anchor=tk.CENTER)
        tk.Label(self.canvas, textvariable=self.keys_tk[1], font=('Calisto', 20),
                 bg=wheel, fg=white).place(x=width-90, y=ybottom+20, anchor=tk.CENTER)
        # mix label
        tk.Label(self.canvas, textvariable=self.mix, font=('Calisto', 15),
                 bg=bg_color, fg=orange).place(x=width/2, y=ybottom+40, anchor=tk.CENTER)
        # number of songs played
        tk.Label(self.canvas, text='number of songs played:', font=('Calisto', 14), 
                 bg=bg_color, fg=white).place(x=xcenter1-75, y=20, anchor=tk.E)
        tk.Label(self.canvas, textvariable=self.Nsongsplayed, font=('Calisto', 14), 
                 bg=bg_color, fg=white).place(x=xcenter1-50, y=20, anchor=tk.E)
        # stream time
        tk.Label(self.canvas, textvariable=self.streamtime, font=('Calisto', 14), 
                 bg=bg_color, fg=white).place(x=xcenter2+50, y=20, anchor=tk.W)
        
        # spinny thing on wheel
        spinny1 = self.canvas.create_line(xmid1+30, ymid, xmid1+40, ymid, width=6,
                                fill=white)
        spinny2 = self.canvas.create_line(xmid2+30, ymid, xmid2+40, ymid, width=6,
                                fill=white)
        
        self.spinnys = [spinny1, spinny2]
        
        # load canvas
        self.canvas.pack()
        
        return
        
    
    def get_properties(self):
        # create songlist and get properties from data file
        songlist = os.listdir()
        
        # check if music data file available
        if 'Music_data.npy' not in songlist:
            print('No music data file in given folder')
            return
        else:
            properties = np.load('Music_data.npy')
            songlist.remove('Music_data.npy')
        
        # delete '.mp3'
        for i in range(len(songlist)):
            songlist[i] = songlist[i][:-4]
        
        return properties, songlist
    
    def stream(self):
        # set up stream
        
        if not self.properties.any():
            print('Cannot start stream without music data')
            return
        else:
            print('\nStarting stream')
        
        # set up stream
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
                format = self.p.get_format_from_width(self.songs[0].sample_width),
                channels = self.songs[0].channels,
                rate = int(self.framerates[0]),
                frames_per_buffer = 80000,
                output = True)
    
    def ms_time(self):
        main = self.track_nr
        side = (main + 1) % 2
        self.ms[main] = int(1000*self.songstarts[main] + self.ticks[main]*self.dts[main])
        self.ms[side] = int(1000*self.songstarts[side] + self.ticks[side]*self.dts[side])
    
    def play(self):
        # start playing music
        # there will be a while loop which will check for changes every time
        # play song via pyaudio
        
        # if paused
        if self.paused:
            self.paused = False
            return
        elif self.streaming:
            return
        
        # play stream
        print('Playing')
        print('-'*60)
        self.streamtime0 = self.stream.get_time()
        self.streaming = True
        
        # play first bit of first song
        data = self.songs[0][:self.ms[0]]._data
        self.stream.write(data)
        
        # main loop
        while len(data) > 0:
            while self.paused:
                self.canvas.update()
                self.canvas.update_idletasks()
                sleep(0.1)
            
            # write data
            self.animate()
            data = self.get_data()
            self.stream.write(data)
            self.ms_time()
        
        self.canvas.mainloop()
    
    def get_data(self):
        # set new data for stream
        main = self.track_nr
        side = (main + 1) % 2
        
        if self.ticks[main] < self.trans_in:
            data = self.songs[main][self.ms[main]:
                        self.ms[main] + int(self.tick_step*self.dts[main])]._data
                
            self.ticks[main] += self.tick_step
            
        elif (self.ticks[main] >= self.trans_in and
                      self.ticks[main] < self.trans_out):
            # use mixing algorithm class
            mixer = Mixing_methods(self)
            data = mixer.get_data(self.mix.get())
            
            self.ticks[main] += self.tick_step
            self.ticks[side] += self.tick_step
            self.transitioning = True
            
            self.pick_button.config(state=tk.DISABLED)
            
        elif self.ticks[main] >= self.trans_out and self.transitioning:
            self.tick_step = 1
            data = self.songs[side][self.ms[side] + self.beat_offset: 
                        self.ms[side] + int(self.tick_step*self.dts[side])]._data
            
            self.ticks[side] += self.tick_step
            self.transitioning = False
            
        elif not self.transitioning:
            self.tick_step = 1/4
            data = self.songs[side][self.ms[side]: 
                        self.ms[side] + int(self.tick_step*self.dts[side])]._data
            
            self.ticks[side] += self.tick_step
            
            # change song
            self.track_nr = (self.track_nr + 1) % 2
            self.next_song()
            self.pick_mix()
            self.set_beat_offset()
            self.ms_time()
            self.pick_button.config(state=tk.NORMAL)
            
        else:
            data = []
            print('data not loaded')
        
        return data
    
    def next_song(self, next_song_nr = False):
        # choose new song and mixing method
        if next_song_nr is False:
            next_song_nr = self.pick_song()
            
        # set song and song number for side
        side = (self.track_nr + 1) % 2
        self.song_nrs[side] = next_song_nr
        self.songs_tk[side].set(self.songlist[next_song_nr])
        self.songs[side] = AudioSegment.from_mp3(self.songlist[next_song_nr] + '.mp3')
        
        # load properties
        (fps, BPM, songstart, dropstart, dropend, key, reliable) = self.properties[self.song_nrs[side]]
        self.framerates[side] = fps
        self.BPMs[side] = BPM
        self.songstarts[side] = songstart
        self.dropstarts[side] = dropstart
        self.dropends[side] = dropend
        self.keys[side] = key
        self.dts[side] = int(1000*4*60/BPM)
        
        # update tkinter variables
        self.BPMs_tk[side].set(int(BPM))
        self.keys_tk[side].set(self.key_names[int(key)])
        
        # update info
        self.Nsongsplayed.set(self.Nsongsplayed.get() + 1)
        
        # register played songs
        self.unplayed = np.delete(self.unplayed, np.where(self.unplayed == next_song_nr))
        
        return
    
    def pick_song(self):
        # pick a song and mixing method
        
        # key must be neighbours
        keys = [(self.keys[self.track_nr] - 5) % 12,
                self.keys[self.track_nr],
                (self.keys[self.track_nr] + 5) % 12]
        unplayed_keys = self.properties[self.unplayed, 5]
        reliable_songs = self.properties[self.unplayed, 6]
        reliable_keys = unplayed_keys + 12*(1 - reliable_songs)
        choices = self.unplayed[np.isin(reliable_keys, keys)]
            
        # if no songs with appropriate keys left, pick a random one
        if len(choices) == 0:
            choices = self.unplayed
            
        # pick random song
        next_song_nr = np.random.choice(choices)
            
        return next_song_nr
    
    def pick_mix(self):
        
        # pick an appriopriate mixing method
        methods = self.mixing_methods.copy()
        green_light = False
        # transitioning time must be at least one bar before current tick
        while not green_light:
            mix = np.random.choice(methods)
            methods.remove(mix)
            trans_in, trans_out, start_side = self.set_shift_times(mix)
            green_light = self.ticks[self.track_nr] + 1 < trans_in
            
        self.trans_in = trans_in
        self.trans_out = trans_out
        self.ticks[(self.track_nr + 1) % 2] = start_side
        self.mix.set(mix)
        
        return
    
    def switch(self):
        # switch to selected song
        index = self.songpicker.curselection()
        song = self.songlist[index[0]]
        print(song)
        
        self.next_song(next_song_nr=index[0])
        self.pick_mix()
        self.set_beat_offset()
        self.ms_time()
        
        return
    
    def set_shift_times(self, mix):
        #determine the transition period
        main = self.track_nr
        side = (main + 1) % 2
        
        dropstart_main = round(1000*(self.dropstarts[main] - 
                                         self.songstarts[main])/self.dts[main])
        dropend_main = round(1000*(self.dropends[main] - 
                                       self.songstarts[main])/self.dts[main])
        dropstart_side = round(1000*(self.dropstarts[side] -
                                      self.songstarts[side])/self.dts[side])
        
        if mix == 'test':
            print('method', self.mix.get())
            trans_in = 8
            trans_out = 16
            start_side = dropstart_side - 8
        
        elif mix == 'crossfade':
            trans_in = dropend_main
            trans_out = dropend_main + 16
            start_side = 0
        
        elif mix == 'drop end switch':
            trans_in = dropend_main - 16
            trans_out = dropend_main
            start_side = 0
        
        elif mix == 'drop-to-drop':
            trans_in = dropend_main - 16
            trans_out = dropend_main
            start_side = dropstart_side - 16
            
        elif mix == 'double drop':
            trans_in = dropstart_main - 8
            trans_out = dropstart_main + 16
            start_side = dropstart_side - 8
        
        elif mix == 'cut drop':
            trans_in = dropstart_main + 24
            trans_out = dropstart_main + 32
            start_side = dropstart_side - 8
        
        elif mix == 'hpf dropfade':
            trans_in = dropstart_main + 32
            trans_out = dropstart_main + 48
            start_side = 16
        
        elif mix == 'bass switch':
            trans_in = dropend_main + 8
            trans_out = dropend_main + 24
            start_side = 8
        
        elif mix == 'drop background':
            trans_in = dropstart_main + 12
            trans_out = dropstart_main + 32
            start_side = dropstart_side - 20
        
        elif mix == 'start from drop':
            trans_in = dropstart_main
            trans_out = dropstart_main + 32
            start_side = 0
            
        return trans_in, trans_out, start_side
    
    def set_beat_offset(self):
        # compute beat offset
        main = self.track_nr
        side = (main + 1) % 2
        main_time = 1000*self.dropstarts[main]
        side_time = 1000*self.dropstarts[side]
        seg_main = self.songs[main][int(main_time + 1/8*self.dts[main]):
                                    int(main_time + 3/8*self.dts[main])]
        seg_side = self.songs[side][int(side_time + 1/8*self.dts[side]):
                                    int(side_time + 3/8*self.dts[side])]
        self.beat_offset = beat_matching(seg_main, seg_side)
        return
    
    def animate(self):
        # animate stuff on GUI
        # some coordinates
        #width = 1200
        #height = 600
        xcenters = [530, 670]
        ybottom = 525
        xmids = [250, 950]
        ymid = 250
        
        main = self.track_nr
        side = (main + 1) % 2
        
        # stream time
        seconds = self.stream.get_time() - self.streamtime0
        minutes = int(seconds/60)
        seconds = seconds % 60
        self.streamtime.set('streamtime %.2d:%.2d' % (minutes, seconds))
        
        # spinny things
        angle1 = np.pi*self.ticks[main]/2
        self.canvas.coords(self.spinnys[main],
                           [xmids[main] + 30*np.cos(angle1), ymid + 30*np.sin(angle1),
                           xmids[main] + 40*np.cos(angle1), ymid + 40*np.sin(angle1)])
        
        if self.transitioning:
            angle2 = np.pi*self.ticks[side]/2
            self.canvas.coords(self.spinnys[side],
                               [xmids[side] + 30*np.cos(angle2), ymid + 30*np.sin(angle2),
                               xmids[side] + 40*np.cos(angle2), ymid + 40*np.sin(angle2)])
        
            # transitioning slider
            frac = ((self.ticks[main] - self.trans_in) /
                    (self.trans_out - self.trans_in))
            x = xcenters[main] + frac*(xcenters[side] - xcenters[main])
            self.canvas.coords(self.slider, [x-6, ybottom-20, x+6, ybottom+20])
        
        self.canvas.update()
        return
    
    def pause(self):
        # pause the playing
        # when play button is pressed, the playing continues
        self.paused = True
        
        return
    
    def stop(self):
        # stop stream   
        self.stream.stop_stream()
        
        # terminate pyaudio
        self.p.terminate()
        print('stream stopped')
        
        # close GUI
        self.root.quit()
        self.root.destroy()
        
        return
        

#%% Mixing methods

class Mixing_methods():
    def __init__(self, P):
        
        main = P.track_nr
        side = (main + 1) % 2
        self.main = main
        
        # song segment
        self.player = P
        self.d1 = P.songs[main][P.ms[main]: 
                          P.ms[main] + int(P.tick_step*P.dts[main])]
        
        d2_start = P.ms[side] + P.beat_offset
        if d2_start > 0:
            d2 = P.songs[side][d2_start: P.ms[side] + int(P.tick_step*P.dts[side]) + P.beat_offset]
        else:
            silence = AudioSegment.silent(duration=abs(d2_start))
            d2 = silence + P.songs[side][0: P.ms[side] + int(P.tick_step*P.dts[side]) + P.beat_offset]
        self.d2 = speed_correction(d2, P.BPMs[main]/P.BPMs[side])
        
        # handy variable
        self.step = int(P.tick_step*self.player.dts[main])
        
        # transition progress
        self.frac = ((P.ticks[main] - P.trans_in) / (P.trans_out - P.trans_in))
        self.frac_next = ((P.ticks[main] - P.trans_in + P.tick_step) / 
                          (P.trans_out - P.trans_in))
        self.tick = self.player.ticks[self.main] - self.player.trans_in
        self.Nticks = self.player.trans_out - self.player.trans_in
    
    def get_data(self, method_nr):
        # methods of altering d1 and d2
        if method_nr == 'test': self.testmix()
        elif method_nr == 'crossfade': self.crossfade()
        elif method_nr == 'drop end switch': self.dropend_switch()
        elif method_nr == 'drop-to-drop': self.drop_to_drop()
        elif method_nr == 'double drop': self.double_drop()
        elif method_nr == 'cut drop': self.cut_drop()
        elif method_nr == 'hpf dropfade': self.hpf_dropfade()
        elif method_nr == 'bass switch': self.bass_switch()
        elif method_nr == 'drop background': self.drop_background()
        elif method_nr == 'start from drop': self.start_from_drop()
        
        #combine
        data = self.d1.overlay(self.d2)._data
        
        return data
        
        
    def testmix(self):
        # testmethod 
        
        # make first song less loud
        self.d1 -= 5
        
        return
    
    def crossfade(self):
        # mixing method 0: fade in - fade out after drop in 8 bars
        
        # fade in second track
        dB_range = 30
        if self.frac < 0.5:
            self.d2 = self.d2.fade(to_gain = -dB_range*(1 - 2*self.frac_next), 
                                   from_gain = -dB_range*(1 - 2*self.frac),
                                   start = 0,
                                   end = self.step)
        # fade out first track
        else:
            self.d1 = self.d1.fade(to_gain = -dB_range*(2*self.frac_next - 1), 
                                   from_gain = -dB_range*(2*self.frac - 1),
                                   start = 0,
                                   end = self.step)
        
        return
    
    def dropend_switch(self):
        # mixing method 1: start 16 bars before end of drop, fade out at drop
                
        # fade in second track
        dB_range = 10
        dim2 = 2
        if self.tick < 8:
            self.d2 = self.d2.fade(to_gain = -dB_range*(1 - (self.tick + self.player.tick_step)/8), 
                                   from_gain = -dB_range*(1 - self.tick/8),
                                   start = 0,
                                   end = self.step) - dim2
                                   
         
        # fade out first track
        elif self.tick == self.Nticks - self.player.tick_step:
            self.d1 = self.d1.fade_out(self.step)
            self.d2 = self.d2.fade(to_gain = 0,
                                   from_gain = -dim2,
                                   start = 0,
                                   end = self.step)
            
        else:
            self.d2 = self.d2 - dim2
                
        return
    
    def drop_to_drop(self):
        # mixing method 2: fade in second track to drop when first track
        # drop ends
        
        dB_range1 = 30
        dB_range2 = 5
        dB_diff = dB_range1 - dB_range2
        # start fading in quickly
        if self.tick < 8:
            self.d2 = self.d2.fade(to_gain = -dB_diff*(1 - (self.tick + self.player.tick_step)/8), 
                                   from_gain = -dB_diff*(1 - self.tick/8),
                                   start = 0,
                                   end = self.step) - dB_range2
        # fade in last part quickly
        elif self.tick >= 8:
            self.d2 = self.d2.fade(to_gain = -dB_range2*(1 - (self.tick - 8 + self.player.tick_step)/8), 
                                   from_gain = -dB_range2*(1 - (self.tick - 8)/8),
                                   start = 0,
                                   end = self.step)
            
        # last minute fade out
        if self.tick == self.Nticks - self.player.tick_step:
            self.d1 = self.d1.fade_out(self.step)
        
        return
    
    def double_drop(self):
        # mixing method 3: double drop
        
        dB_range = 30
        max1 = self.player.songs[self.player.track_nr].dBFS
        max2 = self.player.songs[(self.player.track_nr + 1) % 2].dBFS
        
        # fade in second track before drop
        buildup = self.tick/8
        buildup_next = buildup + self.player.tick_step/8
        
        # dim both tracks to keep headspace
        dim1 = max([(max1 - max2), 0]) + 2
        dim2 = max([(max2 - max1), 0]) + 2
        
        if buildup < 1:
            self.d1 = self.d1.fade(to_gain = -dim1*buildup_next, 
                                   from_gain = -dim1*buildup,
                                   start = 0,
                                   end = self.step)
            self.d2 = self.d2.fade(to_gain = -dB_range*(1 - buildup_next), 
                                   from_gain = -dB_range*(1 - buildup),
                                   start = 0,
                                   end = self.step) - dim2
        
        # last beat fade in/fade out                 
        elif self.tick == self.Nticks - self.player.tick_step:
            self.d1 = self.d1.fade_out(int(self.player.dts[self.main]/4)) - dim1
            self.d2 = self.d2.fade(to_gain = 0, 
                                   from_gain = -dim2,
                                   start = 0,
                                   end = self.step)
        else:
            self.d1 = self.d1 - dim1
            self.d2 = self.d2 - dim2
        
        return
    
    def cut_drop(self):
        # mixing method 4: fade in second track
        dB_range = 20
        
        self.d2 = self.d2.fade(to_gain = -dB_range*(1 - self.frac_next), 
                               from_gain = -dB_range*(1 - self.frac),
                               start = 0,
                               end = self.step)
        
        # fade out first track in the last bar
        if self.tick == self.Nticks:
            self.d1 = self.d1.fade_out(self.step)
        
        return
    
    def hpf_dropfade(self):
        # mixing method 5: increase high pass filter frequency and fade out
        
        # hpf part and fade
        cut_off_freq = int(40*2**(self.tick/4))
        dB_range1 = 12
        dB_range2 = 20
        
        self.d1 = self.d1.high_pass_filter(cut_off_freq)
        
        if self.tick < 8:
            self.d2 = self.d2.fade(to_gain = -dB_range2*(1 - (self.tick + self.player.tick_step)/8), 
                                   from_gain = -dB_range2*(1 - self.tick/8),
                                   start = 0,
                                   end = self.step)
        
        if self.frac >= 0.5:
            self.d1 = self.d1.fade(to_gain = -dB_range1*(2*self.frac_next - 1), 
                                   from_gain = -dB_range1*(2*self.frac - 1),
                                   start = 0,
                                   end = self.step)
            
        # last second fade out
        if self.tick == self.Nticks - self.player.tick_step:
            self.d1 = self.d1.fade_out(self.step)
        
        return
    
    def bass_switch(self):
        # mixing method 6:
        # first half: only treble on seconds track (hpf)
        # second half: only treble on first track (hpf) + fade
        
        cut_off_freq = 500
        dB_range = 15
        
        # hpf second track
        if self.frac < 0.5:
            self.d2 = self.d2.high_pass_filter(cut_off_freq)
        # hpf first track
        else:
            self.d1 = self.d1.high_pass_filter(cut_off_freq)
        
        if self.tick < 6:
            self.d2 = self.d2.fade(to_gain = -dB_range*(1 - (self.tick + self.player.tick_step)/6), 
                                   from_gain = -dB_range*(1 - self.tick/6),
                                   start = 0,
                                   end = self.step)
        
        if self.tick >= self.Nticks - 6:
            self.d1 = self.d1.fade(to_gain = -dB_range*(1 - (self.Nticks - self.tick - self.player.tick_step)/6), 
                                   from_gain = -dB_range*(1 - (self.Nticks - self.tick)/6),
                                   start = 0,
                                   end = self.step)
        
        return
    
    def drop_background(self):
        # mixing method 7: 
        # first 4 bars: fade out first track and fade in second track
        # the rest: build up of second track until drop
        dB_range1 = 4
        dB_range2 = 20
        
        if self.tick < 4:
            self.d1 = self.d1.fade(to_gain = -dB_range1*(self.tick + self.player.tick_step)/4, 
                                   from_gain = -dB_range1*self.tick/4,
                                   start = 0,
                                   end = self.step)
            self.d2 = self.d2.fade(to_gain = -dB_range2*(1 - (self.tick + self.player.tick_step)/4), 
                                   from_gain = -dB_range2*(1 - self.tick/4),
                                   start = 0,
                                   end = self.step)
        else:
            self.d1 -= dB_range1
        
        # fade out first track in last beat
        if self.tick == self.Nticks - self.player.tick_step:
            self.d1 = self.d1.fade_out(self.step)
        
        return
    
    def start_from_drop(self):
        # mixing method 8: 
        # start next song without bass when drop of current song begins
        
        # fade out second track at last bar
        dB_range1 = 15
        dB_range2 = 2
        fade_length = 2
        fade_frac = (fade_length - (self.Nticks - self.tick))/fade_length
        fade_frac_next = fade_frac + self.player.tick_step/fade_length
        if fade_frac >= 0 and fade_frac < 1:
            self.d1 = self.d1.fade(to_gain = -dB_range1*fade_frac_next, 
                                   from_gain = -dB_range1*fade_frac,
                                   start = 0,
                                   end = self.step)
            self.d2 = self.d2.fade(to_gain = -dB_range2*(1 - fade_frac_next), 
                                   from_gain = -dB_range2*(1 - fade_frac),
                                   start = 0,
                                   end = self.step)
        
        # dim second track
        self.d2 = self.d2.high_pass_filter(300) - dB_range2
        
        # fade in second track in last beat
        if self.tick == self.Nticks - self.player.tick_step:
            self.d1 = self.d1.fade_out(self.step)
            self.d2 = self.d2.fade(to_gain = 0,
                                   from_gain = -dB_range2,
                                   start = 0,
                                   end = self.step)
        
        return

#%% Additional functions

def speed_correction(song, speed):
    
    if speed > 1:
        total_ms = len(song)
        
        # cut segment at 4th beat
        cut_location = int(0.75*total_ms)
        segment1 = song[:cut_location]
        segment2 = song[cut_location:]
        
        # crossfade them together
        ms_to_remove = round(total_ms - total_ms/speed)
        song = segment1.append(segment2, crossfade=ms_to_remove)
        
    
    elif speed < 1:
        total_ms = len(song)
        
        # cut segment at 4th beat
        cut_location = int(0.75*total_ms)
        segment1 = song[:cut_location]
        segment2 = song[cut_location:]
        
        # pick additional segment
        crossfade = 10
        ms_to_add = int(total_ms/speed - total_ms)
        segment3 = song[cut_location - ms_to_add - crossfade : cut_location + crossfade]
        
        # glue three pieces together
        song = segment1.append(segment3, crossfade=crossfade).append(segment2, crossfade=crossfade)
        
    
    return song

def beat_matching(segment1, segment2, plot=False):
    # calculate difference of beat hits in seconds
    # difference indicates how much too early the second beat comes
    # a negative value indicates that the second beat comes earlier
    clustertime = 0.01
    
    array1 = To_numpy(segment1.high_pass_filter(500))
    array2 = To_numpy(segment2.high_pass_filter(500))
    
    PH1 = Power_history(array1, segment1.frame_rate, clustertime)
    PH2 = Power_history(array2, segment2.frame_rate, clustertime)
    
    difference = int(1000*clustertime*(np.argmax(PH2) - np.argmax(PH1)))
    
    if plot:
        plt.plot(PH1)
        plt.plot(PH2)
        
        plt.show()
    
    return difference
    