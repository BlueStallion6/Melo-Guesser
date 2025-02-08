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
    raise ValueError("Genius API token not found. Please check your .env file.")

#######################################################################################################################