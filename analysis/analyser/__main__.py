from analyser import analysis

if __name__ == '__main__':
    properties = analysis.analyse_song("C:\\Users\\tuank\\Music\\Drum & Bass\\testfolder", 5, play_drop=False, plotting=True)
    # analysis.compare_song_to_known_data(r"C:\Users\tuank\Programming\Python\AutoDJ\analysis\songtester\data\analysis_testfolder_20221123-165121.csv", 4)
    # analysis.analyse_songs_on_bpm(r"C:\Users\tuank\Programming\Python\AutoDJ\analysis\songtester\data\analysis_testfolder_20221123-165121.csv")
