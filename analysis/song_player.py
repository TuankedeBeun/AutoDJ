import os
import numpy as np
import pyaudio
from pydub import AudioSegment

def play_song(folder, song, start=0, end=-1, speed=1, dt=100):
    # play song via pyaudio
    
    if type(song) is int:
        # find song title
        songs = os.listdir(folder)
        if 'Music_data.npy' in songs:
            songs.remove('Music_data.npy')
        title = songs[song]
        
        # open mp3 with pydub
        mp3 = AudioSegment.from_mp3(os.path.join(folder, title))
        mp3 = mp3[1000*start: 1000*end]
        
    elif type(song) is str:
        mp3 = AudioSegment.from_mp3(os.path.join(folder, title))
        mp3 = mp3[1000*start: 1000*end]
        
    elif type(song) is AudioSegment:
        mp3 = song[1000*start: 1000*end]
        
    else:
        raise TypeError
    
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

