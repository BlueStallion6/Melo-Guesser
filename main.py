try:
    import sys
    import json
    import os
    import random
    from keywords import *
    import colored
    import spotipy
    import requests
    from dotenv import load_dotenv
    import lyricsgenius


except ImportError:
    print("ImportError >> Please run 'pip install -r requirements.txt' in this project's directory.")
    exit()

#######################################################################################################################

load_dotenv()
GENIUS_ACCESS_TOKEN = os.getenv('GENIUS_ACCESS_TOKEN')
if not GENIUS_ACCESS_TOKEN:
    raise ValueError("Genius API token not found.")

The_Weeknd = "The Weeknd"
Billie_Eilish = "Billie Eilish"
Lana_Del_Rey = "Lana Del Rey"
Tame_Impala = "Tame Impala"
Olivia_Rodrigo = "Olivia Rodrigo"

#######################################################################################################################

genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, timeout = 12)

def get_lyrics(title, artist):
    song = genius.search_song(title, artist)
    if song:
        return song.lyrics
    else:
        return None

lyrics = get_lyrics("CHIHIRO", Billie_Eilish)
if lyrics:
    print(lyrics)
else:
    print("Lyrics not found.")













