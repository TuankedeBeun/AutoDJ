import os
import csv
from time import strftime, localtime
from tabulate import tabulate
from analyser.analyse.audio_analyser import AudioAnalyser
from analyser.player.songplayer import play_song
from analyser.common.load_data import load_data_from_csv
from analyser.common.bpm import calculate_bpm_from_drop
from analyser.common.key_conversion import from_keynumber_to_key

def analyse_folder(folder):
    # initialize dictionary csv writer
    last_folder = os.path.split(folder)[-1]
    csv_file_name = 'analysis_' + last_folder + strftime("%d%b%YT%H%M", localtime()) + '.csv'
    song_properties = ['bpm','drop_start', 'drop_end', 'song_start', 'key', 'key_number', 'is_major']
    file = open(os.path.join(os.getcwd(), 'analyser\\data', csv_file_name), newline='', mode='w')
    writer = csv.DictWriter(file, fieldnames=song_properties)
    writer.writeheader()
    
    # extract song properties for every song in the given folder
    songs = os.listdir(folder)
    for nr, song in enumerate(songs):
        print('analysing song number {nr} of {total}: {name}'.format(nr=nr, total=len(songs), name=song[:-4]))
        song_analyser = AudioAnalyser(folder, song, printing=False, plotting=False)
        properties = song_analyser.get_properties()
        key = properties['key']['note'] + (not properties['key']['is_major'])*'m'
        filtered_properties = {
            'bpm': properties['bpm']['value'],
            'drop_start': properties['drop_start']['value'],
            'drop_end': properties['drop_end']['value'],
            'song_start': properties['song_start']['value'],
            'key': key,
            'key_number': properties['key']['key_number'],
            'is_major': properties['key']['is_major']
        }
        writer.writerow(filtered_properties)
        
    file.close()
    return

def analyse_song(folder, song, plotting=False, play_drop=False, printing=True):
    if type(song) == int:
        songlist = os.listdir(folder)
        song_file = songlist[song]
    elif song[-4:] != '.mp3':
        song_file = song + '.mp3'
    else:
        song_file = song
    
    song_analyser = AudioAnalyser(folder, song_file, printing=printing)
    properties = song_analyser.get_properties()
        
    if plotting:
        song_analyser.plotter.draw_axes()
    
    if play_drop: 
        start = properties['drop_start']['value'] - 4*60/(properties['bpm']['value'])
        end = start + 8*60/(properties['bpm']['value'])
        play_song(folder, song_analyser.reader.audiosegment, start=start, end=end)
    
    return properties

def compare_song_to_known_data(csv_path, song_nr, base_path="C:\\Users\\tuank\\Music\\Drum & Bass"):
    ### analyse song
    # get path to corresponding music folder
    file_name = os.path.basename(csv_path)
    folder_name = file_name.split('_')[1]
    folder_path = os.path.join(base_path, folder_name)
    song_name = os.listdir(folder_path)[song_nr].strip('.mp3')
    print(song_name)

    # analyse same song
    song_analysed = analyse_song(folder_path, song_nr, printing=False, plotting=False, play_drop=False)

    ### compare to known data
    # load known data
    folder_known = load_data_from_csv(csv_path)
    song_known = folder_known[song_nr]

    # guess bpm from drop start/end
    bpm_guess = calculate_bpm_from_drop(song_known['drop_start'], song_known['drop_end'])
    bpm_guess = round(bpm_guess, 1)

    # calculate key_number
    key_analysed = from_keynumber_to_key(song_analysed['key']['key_number'], song_analysed['key']['is_major'])

    # print results
    table = [
        ['property', 'known', 'analysis'], 
        ['drop_start', song_known['drop_start'], song_analysed['drop_start']['value']],
        ['drop_end', song_known['drop_end'], song_analysed['drop_end']['value']],
        ['bpm', bpm_guess, song_analysed['bpm']['value']],
        ['key', song_known['key'], key_analysed]
    ]

    print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))

    return table

def analyse_songs_on_bpm(csv_path, base_path="C:\\Users\\tuank\\Music\\Drum & Bass"):
    ### analyse folder on bpm
    # get path to corresponding music folder
    file_name = os.path.basename(csv_path)
    folder_name = file_name.split('_')[1]
    folder_path = os.path.join(base_path, folder_name)
    song_files = os.listdir(folder_path)

    # analyse every song in the folder on bpm
    bpm_analysed = []
    for nr, song_file in enumerate(song_files):
        song_name = song_file.strip('.mp3')
        print('analysing song number {nr} of {total}: {name}'.format(nr=nr, total=len(song_files), name=song_name))
        song_analysed = analyse_song(folder_path, song_file, printing=False, plotting=False, play_drop=False) #TODO: need separate function to only get the BPM
        bpm_analysed.append({song_file.strip('.mp3'): song_analysed['bpm']})

    ### compare with bpm of known data
    print('loading known data')
    # load known data
    folder_known = load_data_from_csv(csv_path)

    # guess bpm from drop start/end
    bpm_known = []
    for song_known in folder_known:
        bpm_guess = calculate_bpm_from_drop(song_known['drop_start'], song_known['drop_end'])
        bpm_guess = round(bpm_guess, 1)
        bpm_known.append({song_known['file'].strip('.mp3'): bpm_guess})

    # add results to table
    print('composing table')
    table = [['song', 'known', 'analysis']]
    for song_file in song_files:
        song_name = song_file.strip('.mp3')
        table_entry = [song_name, bpm_known[song_name], bpm_analysed[song_name]]
        table.append(table_entry)

    # print results
    print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))

    return table