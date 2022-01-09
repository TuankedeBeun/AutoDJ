import os
import numpy as np
import audio_analyser_class as analyser


def Data(folder):
    #compute BPM, key and dropstart/end of each song in the folder
    os.chdir(folder)
    songs = os.listdir()
    
    #check if there already is a music data file
    if 'Music_data.npy' in songs:
        print('Folder already has a music data file')
        overwrite = input('Do you wish to delete it?\n(yes/no)\t')
        if overwrite == 'yes':
            os.remove('Music_data.npy')
            songs.remove('Music_data.npy')
        else:
            return
    
    Nsongs = len(songs)
    data = np.zeros((Nsongs, 7)) #[framerate, BPM, dropstart, dropend, key]
    #loop for every song
    for i, song in enumerate(songs):
        song_analyser = analyser.AudioAnalyser(folder, song)
        properties = song_analyser.get_properties()
        
        #fill data array
        print(properties)
        ### TODO: something with csv saving
    
    np.save('Music_data.npy', data)
    return


def check(folder, song_nr, plot=True):
    os.chdir(folder)
    songs = os.listdir()
    if 'Music_data.npy' in songs:
        songs.remove('Music_data.npy')
    song = songs[song_nr]
    
    #read song
    song, signal, signal_AS, audiorate = Read(song)
    print('\nMusic data: of %s\n' %song[:-4] + '-'*60)
    print('framerate =\t', audiorate)
    
    # find bpm
    props = Find_BPM(signal_AS, signal, audiorate, song, plot=plot)
    BPM, drop_start0, drop_end0, drop_beat, BPM_reliable, beat_reliable = props
    print('BPM =\t\t', BPM)
    print('drop start  ~\t', drop_start0)
    print('drop end  ~\t', drop_end0)
    
    # find exact timestamps of start and end of drop
    drop_start, drop_reliable = Droptime_exact(signal_AS, drop_beat, BPM, plot=plot)
    print('drop start =\t', drop_start)
    
    # find songstart and dropend
    drop_end, song_start = dropend_and_songstart(drop_start, drop_end0, BPM, plot=plot)
    print('drop end =\t', drop_end)
    print('song start =\t', song_start)
    
    # find key
    key, major, scale = Key(signal, audiorate, drop_start, BPM, bars=2, plot=plot)
    print('key =\t\t', key)
    
    # reliability
    reliable = BPM_reliable and beat_reliable and drop_reliable
    if not reliable:
        print('\nUNRELIABLE')
    
    return audiorate, BPM, song_start, drop_start, drop_end, key