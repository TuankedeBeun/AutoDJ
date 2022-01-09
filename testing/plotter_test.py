import plotter
import audioreader
import numpy as np

musicFolderPath = 'C:/Users/tuank/Music/Drum & Bass/Drum & Bass 2'
song = 'Maduk - Avalon (VIP)'

my_reader = audioreader.AudioReader(musicFolderPath, song)

time_fft, freq, fft_signal = my_reader.get_fft()
time_bmt, bass, mid, treb = my_reader.get_bass_mid_treb()
time_np, signal_np = my_reader.to_nparray(my_reader.audiosegment)

my_plotter = plotter.Plotter()
my_plotter.add_plot(time_fft, np.transpose([bass, mid, treb]), 'bass/mid/treb')
my_plotter.add_plot(time_np, np.sum(signal_np, axis=0), 'raw signal')
my_plotter.draw_plots((60,70))