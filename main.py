try:
    import sys
    import json
    import os
    import random
    from keywords import *
    import colored
    import spotipy

except ImportError:
    print("ImportError >> Please run 'pip install -r requirements.txt' in this project's directory.")
    exit()

#######################################################################################################################

print_success("hello <3")