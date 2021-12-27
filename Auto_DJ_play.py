import os
import tkinter as tk
import numpy as np
import pyaudio
from pydub import AudioSegment
from time import sleep

# TO DO
# - make tkinter DJ booth (with info spinning discs?)
# - create ~10 mixing methods
# - redo slowing down with pydub only


class Player():
    # This is the main DJ player class, which plays songs and mixes them.
    # It also comes with a GUI, in which you can set the directory to the music
    # files. There should already be a file containing all the drop/key data in
    # that folder.
    
    def __init__(self, folder, starting_song=0):           
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
                               'double drop']
        # list of keys
        self.key_names = ['A','Bb','B','C','Db','D','Eb','E','F','F#','G','Ab']
        
        # time tick size
        self.tick = 1/4                
        
        # placeholders
        self.song_nr1 = 0
        self.song_nr2 = 0
        self.song1 = None
        self.song2 = None
        self.t1 = 0
        self.t2 = 0
        #load fps, bpm, start, end, key, dt, t2 = t1
        self.load_music_data(show=False)
        
        # load in two new songs
        self.next_song() #song1 = song2, pick new song2
        self.load_music_data()
        self.next_song()
        self.load_music_data()
        
        # get transitioning time ticks
        self.mix.set(self.mixing_methods[1])
        self.set_shift_times()
        self.ms_time()
        
        # toggle for switching songs
        self.loading = False
        # toggle for pausing
        self.paused = False
        # toggle for streaming
        self.streaming = False
        # track playing
        self.main_track = 1
        
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
        pick_button = tk.Button(self.canvas, text='Pick', command=self.switch,
                            font=('Calisto', 18, 'italic'), width=5, bg=blue,
                            fg=white)
        pick_button.place(x=width/2, y=460, anchor=tk.CENTER)
                    
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
        
        # transition slider
        self.canvas.create_line(xcenter1+30, ybottom-25, xcenter1+30, ybottom+25, fill=orange, width=4)
        self.canvas.create_line(xcenter2-30, ybottom-25, xcenter2-30, ybottom+25, fill=orange, width=4)
        for i in range(11):
            x = xcenter1 + 30 + i/11*(xcenter2 - xcenter1 - 60)
            self.canvas.create_line(x, ybottom-25, x, ybottom+25, fill=orange, width=2)
        
        self.slider = self.canvas.create_rectangle(xcenter1+24, ybottom+20, 
                        xcenter1+36, ybottom-20, fill=wheel, outline=slider, width=2)
        
        # tkinter variables
        self.song_title1 = tk.StringVar(self.canvas)
        self.song_title2 = tk.StringVar(self.canvas)
        self.BPM1 = tk.DoubleVar(self.canvas)
        self.BPM2 = tk.DoubleVar(self.canvas)
        self.key_name1 = tk.StringVar(self.canvas)
        self.key_name2 = tk.StringVar(self.canvas)
        self.mix = tk.StringVar(self.canvas)
        self.Nsongsplayed = tk.IntVar(self.canvas, value=-2)
        self.streamtime = tk.StringVar(self.canvas, value='streamtime 00:00')
        
        # info text
        tk.Label(self.canvas, textvariable=self.song_title1, font=('Calisto', 15), 
                 wraplength=260, justify='left',
                 bg=wheel, fg=white).place(x=50, y=ybottom, anchor=tk.W)
        tk.Label(self.canvas, textvariable=self.song_title2, font=('Calisto', 15), 
                 wraplength=260, justify='left',
                 bg=wheel, fg=white).place(x=xcenter2+50, y=ybottom, anchor=tk.W)
        tk.Label(self.canvas, textvariable=self.BPM1, font=('Calisto', 20), 
                 bg=wheel, fg=white).place(x=xcenter1-130, y=ybottom-50, anchor=tk.W)
        tk.Label(self.canvas, textvariable=self.BPM2, font=('Calisto', 20),
                 bg=wheel, fg=white).place(x=width-130, y=ybottom-50, anchor=tk.W)
        tk.Label(self.canvas, textvariable=self.key_name1, font=('Calisto', 20),
                 bg=wheel, fg=white).place(x=xcenter1-130, y=ybottom+20, anchor=tk.W)
        tk.Label(self.canvas, textvariable=self.key_name2, font=('Calisto', 20),
                 bg=wheel, fg=white).place(x=width-130, y=ybottom+20, anchor=tk.W)
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
        self.spinny1 = self.canvas.create_line(xmid1+30, ymid, xmid1+40, ymid, width=6,
                                fill=white, tags='spinny 1')
        self.spinny2 = self.canvas.create_line(xmid2+30, ymid, xmid2+40, ymid, width=6,
                                fill=white, tags='spinny 2')
        
        # load canvas
        self.canvas.pack()
        
        return
        
    
    def get_properties(self):
        # choose music folder
        # also check for data file
        songlist = os.listdir()
        
        # check if music data file available
        if 'Music_data.npy' not in songlist:
            print('No music data file in given folder')
            return
        else:
            properties = np.load('Music_data.npy')
            songlist.remove('Music_data.npy')
        
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
                format = self.p.get_format_from_width(self.song1.sample_width),
                channels = self.song1.channels,
                rate = int(self.framerate),
                frames_per_buffer = 80000,
                output = True)
    
    def ms_time(self):
        self.ms1 = int(1000*self.songstart + self.t1*self.dt1)
        self.ms2 = int(1000*self.songstart2 + self.t2*self.dt2)
    
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
        self.data = self.song1[:self.ms1]._data
        self.stream.write(self.data)
        while len(self.data) > 0:
            while self.paused:
                self.canvas.update()
                self.canvas.update_idletasks()
                sleep(0.1)
            
            # print status
            seconds = self.stream.get_time() - self.streamtime0
            minutes = int(seconds/60)
            seconds = seconds % 60
            self.streamtime.set('streamtime %.2d:%.2d' % (minutes, seconds))
            
            # write data
            data = self.get_data()
            self.stream.write(data)
            self.t1 += self.tick #!!!
            self.ms_time()
            self.animate()
        
        # stop stream    
        self.stream.stop_stream()
        
        # terminate pyaudio
        self.p.terminate()
        print('stream stopped')
    
    def get_data(self):
        # set new data for stream
        #!!!
        if self.t1 < self.trans_in:
            data = self.song1[self.ms1: self.ms1 + self.tick*self.dt1]._data
            
        elif self.t1 >= self.trans_in and self.t1 < self.trans_out:
            
            # use mixing algorithm
            mixer = Mixing_methods(self)
            data = mixer.get_data(self.mix.get())
            
            self.t2 += self.tick
            
        elif self.t1 >= self.trans_out and not self.loading:
            print('loading')
            self.tick = 1
            data = self.song2[self.ms2: self.ms2 + self.tick*self.dt2]._data
            self.t2 += self.tick
            self.loading = True
            print('loaded')
            
        elif self.loading:
            print('switching')
            self.next_song()
            self.load_music_data()
            self.set_shift_times()
            self.ms_time()
            self.tick = 1/4
            data = self.song1[self.ms1: self.ms1 + self.tick*self.dt1]._data
            self.loading = False
            print('switched')
            
        else:
            print('data not loaded')
        
        return data
    
    def next_song(self, next_song_nr = False):
        # choose new song and mixing method
        if next_song_nr is False:
            next_song_nr, mix = self.pick_song()
            self.mix.set(mix)
        else:
            self.mix.set('crossfade')
        
        #!!!
        # shift song properties from song 2 to song 1
        self.song_nr1 = self.song_nr2
        self.song_nr2 = next_song_nr
        self.song_title1.set(self.song_title2.get())
        self.song_title2.set(self.songlist[self.song_nr2])
        self.song1 = self.song2
        self.song2 = AudioSegment.from_mp3(self.songlist[next_song_nr] + '.mp3')
        
        # update info
        self.Nsongsplayed.set(self.Nsongsplayed.get() + 1)
        
        # register played songs
        self.unplayed = np.delete(self.unplayed,
                                  np.where(self.unplayed == self.song_nr2))
        
        # reset slider position
        self.canvas.coords(self.slider, 524, 545, 536, 505)
        
        # printing update
        print('\n' + '-'*60)
        print('Coming up:', self.song_title2.get())
        
        return
    
    def pick_song(self):
        #pick a mixing method
        
        #!!!
        #key must be neighbours
        keys = [(self.key2-5)%12, self.key2, (self.key2+5)%12]
        unplayed_keys = self.properties[self.unplayed, 5]
        choices = self.unplayed[np.isin(unplayed_keys, keys)]
            
        #if no songs with appropriate keys left, pick a random one
        if len(choices) == 0:
            choices = self.unplayed
            methods = ['crossfade']
        # double drop --> crossfade
        elif self.mix.get() == 'double drop':
            methods = ['crossfade']
        # drop-to-drop -/-> double drop
        elif self.mix.get() == 'drop-to-drop':
            methods = self.mixing_methods.copy()
            methods.remove('double drop')
        else:
            methods = self.mixing_methods
        
        next_song_nr = np.random.choice(choices)
        mix = np.random.choice(methods)
            
        return next_song_nr, mix 
    
    def switch(self):
        pass
    
    def load_music_data(self, show=True):
        # data row = [framerate, BPM, songstart, dropstart, dropend, key]
        (self.framerate, BPM1, self.songstart, self.dropstart, 
             self.dropend, self.key1) = self.properties[self.song_nr1]
        (self.framerate2, BPM2, self.songstart2, self.dropstart2, 
             self.dropend2, self.key2) = self.properties[self.song_nr2]
        self.BPM1.set(BPM1)
        self.BPM2.set(BPM2)
        self.key_name1.set(self.key_names[int(self.key1)])
        self.key_name2.set(self.key_names[int(self.key2)])
        self.dt1 = int(1000*4*60/BPM1)
        self.dt2 = int(1000*4*60/BPM2)
        self.t1 = self.t2
        
        if show:
            #print properties
            print('BPM =\t\t', BPM2)
            print('key =\t\t', self.key_names[int(self.key2)])
    
    def set_shift_times(self):
        #determine the transition period
        mix = self.mix.get()
        
        #!!!
        if mix == 'test': #regular crossfade #testmode
            print('method', self.mix.get())
            self.trans_in = 8
            self.trans_out = 16
            self.t2 = round(1000*(self.dropstart2 - self.songstart2)/self.dt2) - 8
        
        elif mix == 'crossfade': #regular crossfade
            print('Next transition: crossfading after drop')
            self.trans_in = round(1000*(self.dropend - self.songstart)/self.dt1)
            self.trans_out = round(1000*(self.dropend - self.songstart)/self.dt1) + 16
            self.t2 = 0
        
        elif mix == 'drop end switch': #after drop switch
            print('Next transition: switching at end of drop')
            self.trans_in = round(1000*(self.dropend - self.songstart)/self.dt1) - 1
            self.trans_out = round(1000*(self.dropend - self.songstart)/self.dt1)
            self.t2 = -1
        
        elif mix == 'drop-to-drop': #drop-to-drop switch
            print('Next transition: switching drop-to-drop')
            self.trans_in = round(1000*(self.dropend - self.songstart)/self.dt1) - 8
            self.trans_out = round(1000*(self.dropend - self.songstart)/self.dt1)
            self.t2 = round(1000*(self.dropstart2 - self.songstart2)/self.dt2) - 8
            
        elif mix == 'double drop': #drop-to-drop switch
            print('Next transition: switching double drop')
            self.trans_in = round(1000*(self.dropstart - self.songstart)/self.dt1) - 8
            self.trans_out = round(1000*(self.dropstart - self.songstart)/self.dt1) + 16
            self.t2 = round(1000*(self.dropstart2 - self.songstart2)/self.dt2) - 8
        
        
        return
    
    def animate(self):
        # animate stuff on GUI
        # some coordinates
        width = 1200
        height = 600
        xcenter1 = 500
        xcenter2 = 700
        xmid1 = 250
        xmid2 = 950
        ymid = 250
        ybottom = 525
        
        # spinny things
        #!!!
        angle = np.pi*self.t1/2
        self.canvas.coords(self.spinny1,
                           [xmid1 + 30*np.cos(angle), ymid + 30*np.sin(angle),
                           xmid1 + 40*np.cos(angle), ymid + 40*np.sin(angle)])
        self.canvas.coords(self.spinny2,
                           [xmid2 + 30*np.cos(angle), ymid + 30*np.sin(angle),
                           xmid2 + 40*np.cos(angle), ymid + 40*np.sin(angle)])
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
        self.root.destroy()
        
        return
        

    ### MIXING METHODS ###
class Mixing_methods():
    def __init__(self, P):
        # song segment
        self.player = P
        self.d1 = P.song1[P.ms1: P.ms1 + P.tick*P.dt1]
        d2 = P.song2[P.ms2: P.ms2 + P.tick*P.dt2]
        self.d2 = speed_correction(d2, P.BPM1.get()/P.BPM2.get())
        
        # handy variable
        self.step = int(self.player.tick*self.player.dt1)
        
        #!!!
        # transition progress
        self.frac = ((P.t1 - P.trans_in) / (P.trans_out - P.trans_in))
        self.frac_next = ((P.t1 - P.trans_in + 1) / (P.trans_out - P.trans_in))
        print('\rtransition %d%%' % (self.frac*100))   
        
        #update slider
        xcenter1 = 500
        xcenter2 = 700
        ybottom = 525
        x = xcenter1 + 30 + self.frac*(xcenter2 - xcenter1 - 60)
        P.canvas.coords(P.slider, [x-6, ybottom-20, x+6, ybottom+20])
    
    def get_data(self, method_nr):
        # methods of altering d1 and d2
        if method_nr == 'test': self.testmix()
        elif method_nr == 'crossfade': self.crossfade()
        elif method_nr == 'drop end switch': self.dropend_switch()
        elif method_nr == 'drop-to-drop': self.drop_to_drop()
        elif method_nr == 'double drop': self.double_drop()
        
        #combine
        data = self.d1.overlay(self.d2)._data
        
        return data
        
        
    def testmix(self):
        #testmethod for playing both songs simultaneously
        
        #make first song less loud
        self.d1 -= 5
        
        return
    
    def crossfade(self):
        #mixing method 0: fade in - fade out after drop in 8 bars
        
        #fade in second track
        dB_range = 20
        if self.frac < 0.5:
            self.d2 = self.d2.fade(to_gain = -dB_range*(1 - 2*self.frac_next), 
                                   from_gain = -dB_range*(1 - 2*self.frac),
                                   start = 0,
                                   end = self.step)
        #fade out first track
        else:
            self.d1 = self.d1.fade(to_gain = -dB_range*(2*self.frac_next - 1), 
                                   from_gain = -dB_range*(2*self.frac - 1),
                                   start = 0,
                                   end = self.step)
        
        return
    
    def dropend_switch(self):
        #mixing method 1: start 8 bars before end of drop, fade out at drop
        
        #fade in - fade out
        self.d2 = self.d2.fade_in(int(self.step/2))
        self.d1 = self.d1.fade_out(int(self.step/4))
                
        return
    
    def drop_to_drop(self):
        # mixing method 2: fade in second track to drop when first track
        # drop ends
        
        dB_range = 30        
        # slowly fade in second track
        self.d2 = self.d2.fade(to_gain = -dB_range*(1 - self.frac_next), 
                               from_gain = -dB_range*(1 - self.frac),
                               start = 0,
                               end = self.step)
        
        # last minute fade out
        if self.player.t1 == self.player.trans_out - self.player.tick:
            self.d1 = self.d1.fade_out(int(self.step))
        
        return
    
    def double_drop(self):
        # mixing method 3: double drop
        
        dB_range = 30
        
        # fade in second track before drop
        buildup = (self.player.t1 - self.player.trans_in)/8
        buildup_next = (self.player.t1 - self.player.trans_in + self.player.tick)/8
        
        # dim both tracks to keep headspace
        dim = 8
        
        if buildup < 1:
            self.d1 = self.d1.fade(to_gain = -dim*buildup_next, 
                                   from_gain = -dim*buildup,
                                   start = 0,
                                   end = self.step)
            self.d2 = self.d2.fade(to_gain = -dB_range*(1 - buildup_next), 
                                   from_gain = -dB_range*(1 - buildup),
                                   start = 0,
                                   end = self.step) - dim
                                   
        elif self.player.t1 == self.player.trans_out - self.player.tick:
            self.d1 = self.d1.fade_out(int(self.player.dt1/4))
            self.d2 = self.d2.fade(to_gain = 0, 
                                   from_gain = -dim,
                                   start = 0,
                                   end = self.step)
        else:
            self.d1 = self.d1 - dim
            self.d2 = self.d2 - dim
        
        return
        
def speed_correction(song, speed):
    #slowdown data fragment manually with numpy
    #!!! needs to be polished by only using pydub
    
    #do not change speed. Minimal speed change is 1.007 for pydub
    if speed >= 1 and speed < 1.01:
        return song
    
    elif speed > 1.01:
        song = song.speedup(playback_speed=speed, crossfade=25)
        return song
    
    song_arr = np.array(song.get_array_of_samples()) #convert audio to numpy array
    if song.channels == 2:
        song_arr = song_arr.reshape((-1, 2)).transpose() #split stereo channels
        song_left = song_arr[0] # take left
        song_right = song_arr[1] # take right
        
    duration = len(song)/1000
    insert_freq = 2.9*2
    interval = int(1/(1-speed))
    #first remove every nth element: if framerate is altered
    '''
    cuts = np.arange(0, mp3_left.size, interval)
    mp3_left = np.delete(mp3_left, cuts)
    mp3_right = np.delete(mp3_right, cuts)
    '''
    
    #add missing pieces by duplicating and inserting data evenly spread out
    Nmissing = int(song_left.size/interval)
    Nchunks = int(insert_freq*duration)
    chunksize = int(Nmissing/Nchunks)
    #determine insert locations
    cuts2 = np.linspace(song_left.size, chunksize, Nchunks+1, dtype=np.int)
    for cut in cuts2:
        #actual inserting
        song_left = np.hstack((song_left[:cut], 
                              song_left[cut:cut+chunksize],
                              song_left[cut:]))
        song_right = np.hstack((song_right[:cut], 
                              song_right[cut:cut+chunksize],
                              song_right[cut:]))
    
    song_arr = np.vstack((song_left, song_right)).transpose()        
    
    song._data = song_arr.tobytes()
    
    return song
        

def Play(folder, song_nr, start=0, end=-1, speed=1, dt=100):
    #play song via pyaudio
    
    #first open mp3 with pydub
    os.chdir(folder)
    songs = os.listdir()
    song = songs[song_nr]
    
    #open mp3
    mp3 = AudioSegment.from_mp3(song)
    mp3 = mp3[1000*start: 1000*end]
    
    #if it needs to be played slower
    if speed < 1:
        #make numpy array
        mp3_arr = np.array(mp3.get_array_of_samples()) #convert audio to numpy array
        if mp3.channels == 2:
            mp3_arr = mp3_arr.reshape((-1, 2)).transpose() #split stereo channels
            mp3_left = mp3_arr[0] # take left
            mp3_right = mp3_arr[1] # take right
    
        insert_freq = 2.9*2
        interval = int(1/(1-speed))
        #first remove every nth element: if framerate is altered
        '''
        cuts = np.arange(0, mp3_left.size, interval)
        mp3_left = np.delete(mp3_left, cuts)
        mp3_right = np.delete(mp3_right, cuts)
        '''
        
        #add missing pieces by duplicating and inserting data evenly spread out
        Nmissing = int(mp3_left.size/interval)
        Nchunks = int(insert_freq*(end-start))
        chunksize = int(Nmissing/Nchunks)
        print('chunklength:', chunksize/48)
        #determine insert locations
        cuts2 = np.linspace(mp3_left.size, chunksize, Nchunks+1, dtype=np.int)
        for cut in cuts2:
            #actual inserting
            mp3_left = np.hstack((mp3_left[:cut], 
                                  mp3_left[cut:cut+chunksize],
                                  mp3_left[cut:]))
            mp3_right = np.hstack((mp3_right[:cut], 
                                  mp3_right[cut:cut+chunksize],
                                  mp3_right[cut:]))
        
        mp3_arr = np.vstack((mp3_left, mp3_right)).transpose()        
        
        mp3._data = mp3_arr.tobytes()
    
        #player faster/slower: if framerate is altered
        '''
        sample_rate = int(mp3.frame_rate * 1)
        mp3 = mp3._spawn(mp3.raw_data, overrides={'frame_rate': sample_rate})
        '''
    
    #if it needs to be played more quickly
    if speed > 1:
        mp3 = mp3.speedup(playback_speed=speed, crossfade=0)
    
    #set up stream
    p = pyaudio.PyAudio()
    stream = p.open(format = p.get_format_from_width(mp3.sample_width),
                    channels = mp3.channels,
                    rate = mp3.frame_rate,
                    output = True)
    
    
    #read first data
    t = 0
    data = mp3[t:t+dt]._data
    
    #play stream
    print('\nplaying')
    while len(data) > 0:
        stream.write(data)
        t += dt
        data = mp3[t:t+dt]._data
    
    #stop stream    
    stream.stop_stream()
    stream.close()
    
    #terminate pyaudio
    p.terminate()
    print('stream stopped')
    
    return

def Double(song_nr1, song_nr2, dt=100):
    #play two songs simultaneously via pyaudio
    
    #first open mp3 with pydub
    os.chdir('C:/Users/tuank/Music/Drum & Bass/Drum & Bass 4')
    songs = os.listdir()
    song1 = songs[song_nr1]
    song2 = songs[song_nr2]
    
    #open mp3's
    mp3_1 = AudioSegment.from_mp3(song1)
    mp3_2 = AudioSegment.from_mp3(song2)
    
    if (mp3_1.channels != mp3_2.channels or
        mp3_1.frame_rate != mp3_2.frame_rate or
        mp3_1.sample_width != mp3_2.sample_width):
        print('format, channels or framerate do not correspond')
        return
    
    #set up stream
    p = pyaudio.PyAudio()
    stream = p.open(format = p.get_format_from_width(mp3_1.sample_width),
                    channels = mp3_1.channels,
                    rate = mp3_1.frame_rate,
                    output = True)
    
    #combine two audiofiles
    combined = mp3_1.overlay(mp3_2)
    
    #read first data
    t = 0
    data = combined[t:t+dt]._data
    
    #play stream
    print('playing')
    while len(data) > 0:
        stream.write(data)
        t += dt
        data = combined[t:t+dt]._data
    
    #stop stream    
    stream.stop_stream()
    stream.close()
    
    #terminate pyaudio
    p.terminate()
    print('stream stopped')
    
    return
