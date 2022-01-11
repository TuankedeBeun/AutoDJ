import os
import csv
import numpy as np
import audio_analyser_class as analyser
from time import strftime, localtime

def Data(folder):
    # initialize dictionary csv writer
    last_folder = os.path.split(folder)[-1]
    csv_file_name = 'analysis_' + last_folder + strftime("%d%b%YT%H:%M", localtime())
    song_properties = ['bpm', 'bpm_reliable','drop_start', 'drop_end', 'song_start', 'key', 'modus']
    file = open('data/' + csv_file_name)
    writer = csv.DictWriter(file, fieldnames=song_properties)
    writer.writeheader()
    
    # extract song properties for every song in the given folder
    songs = os.listdir(folder)
    for song in songs:
        song_analyser = analyser.AudioAnalyser(folder, song)
        properties = song_analyser.get_properties()
        writer.writerow(properties)
        
    file.close()
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