from Auto_DJ_BPM_V3 import Data, check
from Auto_DJ_play_V2 import Player, Play

testfolder = 'C:/Users/tuank/Music/Drum & Bass/testfolder'
DnB_folder = 'C:/Users/tuank/Music/Drum & Bass/Drum & Bass '
#testsong = AudioSegment.from_mp3(testfolder + '/Bensley - Outsider.mp3')
#testsegment = testsong[60000:65000]

folder = DnB_folder+'5'


if True:
    try:
        player.root.destroy()
        del player
    except:
        pass
    player = Player(folder, method=8)
    songlist = player.songlist
    music_data = player.properties
elif True:
    #### criterium for good algorithm: it should yield good results for the first 20 songs ####
    # folder 5: 18, 19, 25, 39, 43, 45
    # folder 6:1,4,6,11,12,14,15,20,35,37,38,39,44,48,68,74,79,82,
    #          85,89,95,96,97,99,100,101,12,104,107,108,109,119

    song = 9
    audiorate, BPM, song_start, drop_start, drop_end, key = check(folder, song, plot=True)
    start = drop_start
    Play(folder, song, start=start, end=start + 4*60/BPM, speed=1)
else:
    Data(testfolder)