import Auto_DJ_plot as DJplot
import numpy as np

musicFolderPath = 'C:/Users/tuank/Music/Drum & Bass/Drum & Bass 2/'
song = 'Maduk - Avalon (VIP)'
song_path = musicFolderPath + song + '.mp3'

segment = DJplot.read_to_audiosegment(song_path)
time, segmentNp = DJplot.audiosegment_to_nparray(segment)
time_fft, freq, fft1 = DJplot.fft_from_nparray(segmentNp, 48000)
bass, mid, treb = DJplot.bass_mid_treb_from_fft(freq, fft1)

plotter = DJplot.Plotter()
plotter.add_plot(time_fft, np.transpose([bass, mid, treb]), 'bass/mid/treb')
plotter.draw_plots((60,70))