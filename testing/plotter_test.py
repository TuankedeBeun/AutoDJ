import plotter
import numpy as np

musicFolderPath = 'C:/Users/tuank/Music/Drum & Bass/Drum & Bass 2/'
song = 'Maduk - Avalon (VIP)'

my_reader = plotter.AudioReader(musicFolderPath, song)

time_fft, freq, fft_signal = my_reader.get_fft()
time_bmt, bass, mid, treb = my_reader.get_bass_mid_treb()

my_plotter = plotter.Plotter()
my_plotter.add_plot(time_fft, np.transpose([bass, mid, treb]), 'bass/mid/treb')
my_plotter.draw_plots((60,70))