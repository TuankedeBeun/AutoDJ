import os
import csv
from audio_analyser import AudioAnalyser
from time import strftime, localtime
from songplayer import play_song

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
        song_analyser = AudioAnalyser(folder, song)
        properties = song_analyser.get_properties()
        writer.writerow(properties)
        
    file.close()
    return

def analyse_song(folder, song, plot=True, play_drop=False):
    if type(song) == int:
        songlist = os.listdir(folder)
        song_file = songlist[song]
    else:
        song_file = song + '.mp3'
    
    song_analyser = AudioAnalyser(folder, song_file)
    properties = song_analyser.get_properties()
    
    for prop in properties.keys():
        value = properties[prop]
        print('%15s: %s' % (prop, value))
        
    if plot: song_analyser.plotter.draw_axes()
    
    if play_drop: 
        start = properties['drop_start']['value'] - 4*60/(properties['bpm']['value'])
        end = start + 8*60/(properties['bpm']['value'])
        play_song(folder, song_analyser.reader.audiosegment, start=start, end=end)
    
    return properties