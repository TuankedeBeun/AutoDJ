import os
import csv
import audio_analyser_class as analyser
from time import strftime, localtime

def analyse_folder(folder):
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

def analyse_song(folder, song, plot=True):
    if type(song) == int:
        songlist = os.listdir(folder)
        song_file = songlist[song]
    else:
        song_file = song + '.mp3'
    
    song_analyser = analyser.AudioAnalyser(folder, song_file)
    properties = song_analyser.get_properties()
    
    tones = ['A','Bb','B','C','C#','D','Eb','E','F','F#','G','G#']

    for prop in properties.keys():
        value = properties[prop]
        if prop == 'key':
            value = tones[value]
        print('%15s: %s' % (prop, value))
        
#    song_analyser.plotter.draw_plots()
    
    return properties