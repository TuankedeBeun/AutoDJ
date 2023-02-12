import os
from plotting import plotter
from analyse import audioreader

musicFolderPath = 'C:/Users/tuank/Music/Drum & Bass/Drum & Bass 4'
songlist = os.listdir(musicFolderPath)
song = songlist[3]

my_reader = audioreader.AudioReader(musicFolderPath, song)

time_fft, freq, fft_signal = my_reader.get_fft(freq_low=50)
time_bmt, bass, mid, treb = my_reader.get_bass_mid_treb()
time_np, signal_np = audioreader.to_nparray(my_reader.audiosegment)

my_plotter = plotter.Plotter(song)
my_plotter.add_plot(time_bmt, bass, 'bass')
my_plotter.add_plot(time_bmt, mid, 'middle')
my_plotter.add_plot(time_bmt, treb, 'treble')
#my_plotter.add_plot(time_np, np.sum(signal_np, axis=0), 'raw signal')
my_plotter.draw_plots()