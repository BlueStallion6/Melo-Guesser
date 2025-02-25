#!/usr/bin/env python3

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
    import PySide6
    from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                                   QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
                                   QFrame, QGridLayout, QSizePolicy, QProgressBar,
                                   QComboBox, QScrollArea, QRadioButton, QButtonGroup)
    from PySide6.QtCore import Qt, QRect, QPoint, Signal
    from PySide6.QtGui import QFont, QIcon, QPainterPath, QRegion
    from PySide6 import QtCore, QtWidgets, QtGui

    # Import album databases
    from albums_database import (the_weeknd_albums, billie_eilish_albums,
                                 lana_del_rey_albums, tame_impala_albums,
                                 olivia_rodrigo_albums)

except ImportError as e:
    print(f"ImportError >> {e}")
    print("Please run 'pip install -r requirements.txt' in this project's directory.")
    exit()

# Load environment variables
load_dotenv()
GENIUS_ACCESS_TOKEN = os.getenv('GENIUS_ACCESS_TOKEN')
if not GENIUS_ACCESS_TOKEN:
    try:
        # Try to import from config.py as a fallback
        from config import GENIUS_API_KEY

        GENIUS_ACCESS_TOKEN = GENIUS_API_KEY
    except (ImportError, AttributeError):
        print_error("Genius API token not found. Please set GENIUS_ACCESS_TOKEN in .env or config.py")
        exit(1)

# Artist constants
The_Weeknd = "The Weeknd"
Billie_Eilish = "Billie Eilish"
Lana_Del_Rey = "Lana Del Rey"
Tame_Impala = "Tame Impala"
Olivia_Rodrigo = "Olivia Rodrigo"

# Initialize Genius API client
genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, timeout=12)


def get_lyrics(title, artist):
    """
    Get full lyrics for a song using the Genius API.

    Args:
        title (str): Song title
        artist (str): Artist name

    Returns:
        str or None: Song lyrics or None if not found
    """
    try:
        print_debug(f"Searching for lyrics: {title} by {artist}")
        song = genius.search_song(title, artist)
        if song:
            return song.lyrics
        else:
            print_warning(f"Lyrics not found for: {title} by {artist}")
            return None
    except Exception as e:
        print_error(f"Error getting lyrics: {e}")
        return None


def get_random_lyric_line(title, artist):
    """
    Get a random meaningful line from song lyrics.

    Args:
        title (str): Song title
        artist (str): Artist name

    Returns:
        str: A random line from the lyrics or error message
    """
    full_lyrics = get_lyrics(title, artist)

    if not full_lyrics:
        return "Lyrics not found."

    # Split into lines
    lines = full_lyrics.split('\n')

    # Filter out empty lines and headers/footers
    clean_lines = []
    for line in lines:
        line = line.strip()
        words = [word for word in line.split() if word]
        word_count = len(words)

        if (line.strip() and
                not line.startswith('[') and
                not line.endswith(']') and
                not line.startswith('(') and
                not line.endswith(')') and
                word_count > 4 and
                not 'Lyrics' in line and
                not 'Contributor' in line and
                not 'Embed' in line):
            clean_lines.append(line.strip())

    # Return a random line if we have any valid lines
    if clean_lines:
        selected_line = random.choice(clean_lines)
        print_debug(f"Selected lyric: {selected_line}")
        return selected_line
    else:
        print_warning(f"No suitable lyrics found for: {title} by {artist}")
        return "No suitable lyrics found."


# UI Components

class RoundedProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("roundedProgressBar")
        self.setTextVisible(False)
        self.setFixedHeight(4)
        # Set a loading style animation
        self.loading_style = """
        #roundedProgressBar::chunk {
            background-color: #e6c15a;
            border-radius: 2px;
            width: 10px;
        }
        """
        self.normal_style = """
        #roundedProgressBar::chunk {
            background-color: #e6c15a;
            border-radius: 2px;
        }
        """
        self.setStyleSheet(self.normal_style)

    def set_loading_mode(self, is_loading):
        """Toggle loading animation mode"""
        if is_loading:
            self.setStyleSheet(self.loading_style)
        else:
            self.setStyleSheet(self.normal_style)


class RoundedFrame(QFrame):
    def __init__(self, parent=None, radius=10):
        super().__init__(parent)
        self.border_radius = radius

    def paintEvent(self, event):
        # Let the original paintEvent handle the painting
        super().paintEvent(event)

    def resizeEvent(self, event):
        # Create a rounded mask for the frame
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), self.border_radius, self.border_radius)
        mask = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)
        super().resizeEvent(event)


class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(50)
        self.setObjectName("titleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)

        # Title with logo
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)

        # Music icon (you can replace with an actual icon)
        logo_label = QLabel("🎵")
        logo_label.setObjectName("logoLabel")

        title = QLabel("MELO-GUESSER")
        title.setObjectName("titleLabel")

        title_layout.addWidget(logo_label)
        title_layout.addWidget(title)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        minimize_button = QPushButton("−")
        minimize_button.setObjectName("minimizeButton")
        minimize_button.setFixedSize(30, 30)
        minimize_button.clicked.connect(self.parent.showMinimized)

        close_button = QPushButton("✕")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.parent.close)

        button_layout.addWidget(minimize_button)
        button_layout.addWidget(close_button)

        layout.addLayout(title_layout)
        layout.addStretch()
        layout.addLayout(button_layout)

        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.start_pos:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent.move(self.parent.x() + delta.x(), self.parent.y() + delta.y())
            self.start_pos = event.globalPosition().toPoint()
            event.accept()


class GuessButton(QPushButton):
    def __init__(self, text, parent=None, icon=None):
        super().__init__(text, parent)
        self.setObjectName("guessButton")
        self.setMinimumHeight(50)
        if icon:
            self.setText(f"{icon} {text}")


class ArtistAlbumSelector(QWidget):
    selectionMade = Signal(str, str, list)  # artist, album, songs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("artistAlbumSelector")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(30)

        # Welcome message section
        welcome_frame = RoundedFrame(radius=10)
        welcome_frame.setObjectName("welcomeFrame")
        welcome_layout = QVBoxLayout(welcome_frame)
        welcome_layout.setContentsMargins(25, 25, 25, 25)

        welcome_logo = QLabel("🎵✨")
        welcome_logo.setObjectName("welcomeLogo")
        welcome_logo.setAlignment(Qt.AlignCenter)

        welcome_title = QLabel("WELCOME TO MELO-GUESSER")
        welcome_title.setObjectName("welcomeTitle")
        welcome_title.setAlignment(Qt.AlignCenter)

        welcome_text = QLabel(
            "Test your music knowledge by guessing songs from lyrics! Select an artist and album below to start playing.")
        welcome_text.setObjectName("welcomeText")
        welcome_text.setWordWrap(True)
        welcome_text.setAlignment(Qt.AlignCenter)

        welcome_layout.addWidget(welcome_logo)
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_text)

        main_layout.addWidget(welcome_frame)

        # Selection section frame
        selection_frame = RoundedFrame(radius=10)
        selection_frame.setObjectName("selectionFrame")
        selection_layout = QVBoxLayout(selection_frame)
        selection_layout.setContentsMargins(25, 25, 25, 25)
        selection_layout.setSpacing(20)

        # Title
        title = QLabel("SELECT YOUR MUSIC")
        title.setObjectName("selectorTitle")
        title.setAlignment(Qt.AlignCenter)
        selection_layout.addWidget(title)

        # Artist selection
        artist_label = QLabel("CHOOSE AN ARTIST")
        artist_label.setObjectName("selectorLabel")
        self.artist_combo = QComboBox()
        self.artist_combo.setObjectName("artistCombo")
        self.artist_combo.setMinimumHeight(45)

        # Add artists
        self.artists = {
            "The Weeknd": the_weeknd_albums,
            "Billie Eilish": billie_eilish_albums,
            "Lana Del Rey": lana_del_rey_albums,
            "Tame Impala": tame_impala_albums,
            "Olivia Rodrigo": olivia_rodrigo_albums
        }

        for artist in self.artists.keys():
            self.artist_combo.addItem(artist)

        self.artist_combo.currentTextChanged.connect(self.update_albums)

        # Album selection
        album_label = QLabel("SELECT AN ALBUM")
        album_label.setObjectName("selectorLabel")
        self.album_combo = QComboBox()
        self.album_combo.setObjectName("albumCombo")
        self.album_combo.setMinimumHeight(45)

        # Album info display
        self.album_info = QLabel()
        self.album_info.setObjectName("albumInfo")
        self.album_info.setAlignment(Qt.AlignCenter)

        # Confirm button
        self.confirm_button = QPushButton("START PLAYING")
        self.confirm_button.setObjectName("confirmButton")
        self.confirm_button.setMinimumHeight(50)
        self.confirm_button.clicked.connect(self.confirm_selection)

        # Add to layout
        selection_layout.addWidget(artist_label)
        selection_layout.addWidget(self.artist_combo)
        selection_layout.addWidget(album_label)
        selection_layout.addWidget(self.album_combo)
        selection_layout.addWidget(self.album_info)
        selection_layout.addWidget(self.confirm_button)

        main_layout.addWidget(selection_frame)

        # How to play section
        how_to_frame = RoundedFrame(radius=10)
        how_to_frame.setObjectName("howToFrame")
        how_to_layout = QVBoxLayout(how_to_frame)
        how_to_layout.setContentsMargins(25, 25, 25, 25)

        how_to_title = QLabel("HOW TO PLAY")
        how_to_title.setObjectName("howToTitle")
        how_to_title.setAlignment(Qt.AlignCenter)

        how_to_text = QLabel(
            "1. Select an artist and album\n2. Read the displayed lyrics\n3. Guess which song they're from\n4. Build your streak and score!")
        how_to_text.setObjectName("howToText")
        how_to_text.setAlignment(Qt.AlignCenter)

        how_to_layout.addWidget(how_to_title)
        how_to_layout.addWidget(how_to_text)

        main_layout.addWidget(how_to_frame)

        # Fill albums for initial artist
        self.update_albums(self.artist_combo.currentText())

    def update_albums(self, artist_name):
        """Update album list when artist changes"""
        self.album_combo.clear()

        if artist_name in self.artists:
            albums = self.artists[artist_name]
            for album_name in albums.keys():
                self.album_combo.addItem(album_name)

            # Update album info for first album
            self.update_album_info()

            # Connect album change signal
            self.album_combo.currentTextChanged.connect(self.update_album_info)

    def update_album_info(self):
        """Update album information display"""
        artist = self.artist_combo.currentText()
        album = self.album_combo.currentText()

        if artist in self.artists and album in self.artists[artist]:
            album_data = self.artists[artist][album]
            year = album_data["release_year"]
            song_count = len(album_data["songs"])

            #info_text = f"Released: {year} • {song_count} songs"
            #self.album_info.setText(info_text)

    def confirm_selection(self):
        """Emit signal with selected artist, album and songs"""
        artist = self.artist_combo.currentText()
        album = self.album_combo.currentText()

        if artist in self.artists and album in self.artists[artist]:
            songs = self.artists[artist][album]["songs"]
            self.selectionMade.emit(artist, album, songs)


# Main Application Class
class SongGuesserApp(QMainWindow):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint)
        self.setWindowTitle("Melo-Guesser")

        # Get screen size and calculate window size
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.55)
        height = int(screen.height() * 0.7)
        min_width = 650
        min_height = 600
        width = max(width, min_width)
        height = max(height, min_height)

        # Center window
        window_x = (screen.width() - width) // 2
        window_y = (screen.height() - height) // 2
        self.setGeometry(QRect(window_x, window_y, width, height))
        self.setFixedSize(width, height)

        # Create rounded window mask
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create main container
        self.main_container = RoundedFrame(self, radius=15)
        self.main_container.setObjectName("mainContainer")
        self.setCentralWidget(self.main_container)

        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add custom title bar
        title_bar = CustomTitleBar(self)
        main_layout.addWidget(title_bar)

        # Create content widget and stacked layout for game modes
        self.content = QWidget()
        self.content.setObjectName("mainContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(30, 25, 30, 25)
        self.content_layout.setSpacing(25)

        # Initialize game state variables
        self.current_song = ""
        self.current_artist = ""
        self.selected_album = ""
        self.selected_songs = []
        self.score = 0
        self.streak = 0
        self.max_streak = 0
        self.songs_played = 0
        self.total_songs = 5

        # Create the album selector widget
        self.album_selector = ArtistAlbumSelector()
        self.album_selector.selectionMade.connect(self.on_album_selected)
        self.content_layout.addWidget(self.album_selector)

        # Create the game UI (initially hidden)
        self.game_widget = QWidget()
        self.game_layout = QVBoxLayout(self.game_widget)
        self.game_layout.setContentsMargins(0, 0, 0, 0)
        self.game_layout.setSpacing(25)
        self.game_widget.hide()

        # Game header with progress bar
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 10)
        header_layout.setSpacing(15)

        self.header = QLabel("GUESS THE SONG FROM LYRICS")
        self.header.setObjectName("gameHeader")
        self.header.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.header)

        # Progress bar to indicate current song
        self.progress_bar = RoundedProgressBar()
        header_layout.addWidget(self.progress_bar)

        self.game_layout.addWidget(header_frame)

        # Score and streak area
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        # Score display
        score_frame = RoundedFrame(radius=8)
        score_frame.setObjectName("scoreFrame")
        score_layout = QVBoxLayout(score_frame)
        score_title = QLabel("SCORE")
        score_title.setObjectName("statLabel")
        score_title.setAlignment(Qt.AlignCenter)
        self.score_label = QLabel("0")
        self.score_label.setObjectName("scoreValue")
        self.score_label.setAlignment(Qt.AlignCenter)
        score_layout.addWidget(score_title)
        score_layout.addWidget(self.score_label)
        stats_layout.addWidget(score_frame)

        # Streak display
        streak_frame = RoundedFrame(radius=8)
        streak_frame.setObjectName("streakFrame")
        streak_layout = QVBoxLayout(streak_frame)
        streak_title = QLabel("STREAK")
        streak_title.setObjectName("statLabel")
        streak_title.setAlignment(Qt.AlignCenter)
        self.streak_label = QLabel("0")
        self.streak_label.setObjectName("streakValue")
        self.streak_label.setAlignment(Qt.AlignCenter)
        streak_layout.addWidget(streak_title)
        streak_layout.addWidget(self.streak_label)
        stats_layout.addWidget(streak_frame)

        # Album info display
        album_display = RoundedFrame(radius=8)
        album_display.setObjectName("albumDisplayFrame")
        album_display_layout = QVBoxLayout(album_display)
        album_title = QLabel("ALBUM")
        album_title.setObjectName("statLabel")
        album_title.setAlignment(Qt.AlignCenter)
        self.album_label = QLabel("")
        self.album_label.setObjectName("albumValue")
        self.album_label.setAlignment(Qt.AlignCenter)
        album_display_layout.addWidget(album_title)
        album_display_layout.addWidget(self.album_label)
        stats_layout.addWidget(album_display)

        self.game_layout.addLayout(stats_layout)

        # Lyric display with decorative elements
        lyric_frame = RoundedFrame(radius=8)
        lyric_frame.setObjectName("lyricFrame")
        lyric_layout = QVBoxLayout(lyric_frame)
        lyric_layout.setContentsMargins(20, 20, 20, 20)

        # Add quote marks
        quote_open = QLabel('"')
        quote_open.setObjectName("quoteOpen")
        quote_open.setAlignment(Qt.AlignLeft)
        lyric_layout.addWidget(quote_open)

        # Lyric text
        self.lyric_label = QLabel("Select an artist and album to start guessing...")
        self.lyric_label.setObjectName("lyricDisplay")
        self.lyric_label.setWordWrap(True)
        self.lyric_label.setAlignment(Qt.AlignCenter)
        lyric_layout.addWidget(self.lyric_label, 1)

        # Closing quote
        quote_close = QLabel('"')
        quote_close.setObjectName("quoteClose")
        quote_close.setAlignment(Qt.AlignRight)
        lyric_layout.addWidget(quote_close)

        self.game_layout.addWidget(lyric_frame, 1)

        # Guess input area
        input_frame = QFrame()
        input_frame.setObjectName("inputFrame")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(15)

        input_label = QLabel("YOUR GUESS")
        input_label.setObjectName("inputLabel")
        input_layout.addWidget(input_label)

        self.guess_input = QLineEdit()
        self.guess_input.setPlaceholderText("Enter song name...")
        self.guess_input.setObjectName("guessInput")
        self.guess_input.setMinimumHeight(50)
        self.guess_input.returnPressed.connect(self.submit_guess)
        input_layout.addWidget(self.guess_input)

        self.submit_button = GuessButton("SUBMIT GUESS", icon="🎯")
        self.submit_button.clicked.connect(self.submit_guess)
        input_layout.addWidget(self.submit_button)

        self.game_layout.addWidget(input_frame)

        # Results area with animated feedback
        self.result_label = QLabel("")
        self.result_label.setObjectName("resultLabel")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.game_layout.addWidget(self.result_label)

        # Game control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.new_song_button = GuessButton("NEW SONG", icon="🎵")
        self.new_song_button.clicked.connect(self.new_song)
        self.new_song_button.setObjectName("newSongButton")

        self.skip_button = GuessButton("SKIP", icon="⏭️")
        self.skip_button.clicked.connect(self.skip_song)
        self.skip_button.setObjectName("skipButton")

        self.change_album_button = GuessButton("CHANGE ALBUM", icon="💿")
        self.change_album_button.clicked.connect(self.change_album)
        self.change_album_button.setObjectName("changeAlbumButton")

        buttons_layout.addWidget(self.new_song_button)
        buttons_layout.addWidget(self.skip_button)
        buttons_layout.addWidget(self.change_album_button)

        self.game_layout.addLayout(buttons_layout)

        # Add the game widget to content
        self.content_layout.addWidget(self.game_widget)

        # Add content to main layout
        main_layout.addWidget(self.content)

        # Apply stylesheet
        self.apply_stylesheet()

    def on_album_selected(self, artist, album, songs):
        """Handle album selection"""
        self.current_artist = artist
        self.selected_album = album
        self.selected_songs = songs
        self.total_songs = len(songs)

        # Update album display
        self.album_label.setText(f"{album}")
        self.header.setText(f"GUESS {artist.upper()} SONGS FROM LYRICS")

        # Hide selector and show game
        self.album_selector.hide()
        self.game_widget.show()

        # Reset game stats
        self.score = 0
        self.streak = 0
        self.songs_played = 0
        self.score_label.setText("0")
        self.streak_label.setText("0")
        self.progress_bar.setValue(0)

        # Show loading message
        self.lyric_label.setText("Now loading...")

        # Load first song with slight delay to allow UI to update
        QtCore.QTimer.singleShot(100, self.new_song)

    def new_song(self):
        """Load a new random song from the selected album"""
        if not self.selected_songs:
            return

        # Choose a random song from the album
        self.current_song = random.choice(self.selected_songs)

        # Show loading message and style
        self.lyric_label.setText("Now loading...")
        self.result_label.setText("")
        self.progress_bar.set_loading_mode(True)

        # Reset input field
        self.guess_input.setText("")
        self.songs_played += 1

        # Update progress bar
        progress_value = min(100, int((self.songs_played / self.total_songs) * 100))
        self.progress_bar.setValue(progress_value)

        # Use a QTimer to allow the UI to update before fetching lyrics (which might be slow)
        QtCore.QTimer.singleShot(100, lambda: self.fetch_and_display_lyrics())

        print_success(f"New song loaded: {self.current_song} by {self.current_artist}")

    def fetch_and_display_lyrics(self):
        """Fetch and display lyrics for the current song"""
        # Get and display a random lyric line
        lyric = get_random_lyric_line(self.current_song, self.current_artist)
        self.lyric_label.setText(lyric)
        self.progress_bar.set_loading_mode(False)

    def skip_song(self):
        """Skip the current song"""
        if self.current_song:
            # Reset streak when skipping
            self.streak = 0
            self.streak_label.setText(str(self.streak))

            self.result_label.setText(f"The song was: {self.current_song}")

            # Show loading for the next song
            QtCore.QTimer.singleShot(2000, lambda: self.lyric_label.setText("Now loading..."))
            # Load a new song after short delay
            QtCore.QTimer.singleShot(2100, self.new_song)

    def submit_guess(self):
        """Process the user's guess"""
        guess = self.guess_input.text().strip()
        if not guess:
            return

        if not self.current_song:
            self.result_label.setText("Please click 'New Song' first!")
            return

        # Improved string matching with some flexibility
        if self.is_correct_guess(guess, self.current_song):
            self.score += 1
            self.streak += 1
            self.max_streak = max(self.max_streak, self.streak)

            self.score_label.setText(str(self.score))
            self.streak_label.setText(str(self.streak))

            # Show success message with animations
            self.result_label.setText(f"Correct! 🎵 The song was {self.current_song}")

            # Highlight the score with animation
            self.score_label.setStyleSheet("color: #6eff8a; font-size: 24px; font-weight: bold;")
            QtCore.QTimer.singleShot(1000, lambda: self.score_label.setStyleSheet(""))

            # Show loading for the next song
            QtCore.QTimer.singleShot(2000, lambda: self.lyric_label.setText("Now loading..."))
            # Load a new song after displaying success
            QtCore.QTimer.singleShot(2100, self.new_song)
        else:
            # Reset streak on wrong answer
            self.streak = 0
            self.streak_label.setText(str(self.streak))

            self.result_label.setText("Incorrect, try again!")

    def is_correct_guess(self, guess, actual):
        """Improved matching for song guesses"""
        guess = guess.lower().strip()
        actual = actual.lower().strip()

        # Direct match
        if guess == actual:
            return True

        # Remove special characters and check
        import re
        guess_clean = re.sub(r'[^\w\s]', '', guess).strip()
        actual_clean = re.sub(r'[^\w\s]', '', actual).strip()

        if guess_clean == actual_clean:
            return True

        # Check if guess is contained in actual or vice versa (for partial matches)
        if (len(guess_clean) > 5 and (guess_clean in actual_clean or actual_clean in guess_clean)):
            return True

        return False

    def change_album(self):
        """Return to album selection"""
        # Reset game
        self.current_song = ""
        self.current_artist = ""
        self.selected_album = ""
        self.selected_songs = []

        # Hide game and show selector
        self.game_widget.hide()
        self.album_selector.show()

    def apply_stylesheet(self):
        # Original stylesheet plus additions for album selector

        # Base stylesheet (from original implementation)
        base_stylesheet = """
        /* Main Window Styles */
        QMainWindow {
            background-color: transparent;
        }

        #mainContainer {
            background-color: #0e1016;
            border-radius: 15px;
        }

        #mainContent {
            background-color: #0e1016;
            color: white;
            border: none;
        }

        /* Title Bar */
        #titleBar {
            background-color: #080a10;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            border-bottom: 1px solid #1e2028;
        }

        #titleLabel {
            color: #e6c15a;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 1px;
        }

        #logoLabel {
            color: #e6c15a;
            font-size: 22px;
        }

        #closeButton, #minimizeButton {
            background-color: transparent;
            color: #aaaaaa;
            font-size: 16px;
            border: none;
            border-radius: 15px;
        }

        #closeButton:hover {
            background-color: #e81123;
            color: white;
        }

        #minimizeButton:hover {
            background-color: #333333;
            color: white;
        }

        /* Header Frame */
        #headerFrame {
            border-bottom: 1px solid #1e2028;
            padding-bottom: 5px;
        }

        /* Game Header */
        #gameHeader {
            color: #e6c15a;
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 1px;
        }

        /* Progress Bar */
        #roundedProgressBar {
            background-color: #1e2028;
            border-radius: 2px;
            border: none;
        }

        #roundedProgressBar::chunk {
            background-color: #e6c15a;
            border-radius: 2px;
        }

        /* Stats Frames */
        #scoreFrame, #streakFrame {
            background-color: #14161d;
            border: 1px solid #1e2028;
            border-radius: 8px;
            padding: 10px;
        }

        #statLabel {
            color: #aaaaaa;
            font-size: 13px;
            font-weight: bold;
        }

        #scoreValue, #streakValue {
            color: #11c9f5;
            font-size: 22px;
            font-weight: bold;
        }

        /* Lyric Frame */
        #lyricFrame {
            background-color: #14161d;
            border: 1px solid #1e2028;
            border-radius: 8px;
        }

        /* Quote Marks */
        #quoteOpen, #quoteClose {
            color: #6b6d74;
            font-size: 42px;
            font-family: Georgia, serif;
            font-weight: bold;
        }

        /* Lyric Display */
        #lyricDisplay {
            background-color: transparent;
            border: none;
            padding: 10px;
            color: white;
            font-size: 20px;
            line-height: 1.5;
            font-style: italic;
        }

        /* Input Frame */
        #inputFrame {
            background-color: transparent;
        }

        #inputLabel {
            color: #aaaaaa;
            font-size: 14px;
            font-weight: bold;
        }

        #guessInput {
            background-color: #14161d;
            border: 1px solid #1e2028;
            border-radius: 8px;
            padding: 10px 15px;
            color: white;
            font-size: 16px;
        }

        #guessInput:focus {
            border: 1px solid #e6c15a;
            background-color: #191b22;
        }

        /* Buttons */
        #guessButton {
            background-color: #14161d;
            color: #e6c15a;
            border: 1px solid #e6c15a;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 1px;
        }

        #guessButton:hover {
            background-color: #1a1d25;
            border: 1px solid #f0cc62;
        }

        #guessButton:pressed {
            background-color: #e6c15a;
            color: #0e1016;
        }

        #newSongButton {
            background-color: #14161d;
            color: #11c9f5;
            border: 1px solid #11c9f5;
        }

        #newSongButton:hover {
            background-color: #1a1d25;
            border: 1px solid #39d8ff;
        }

        #newSongButton:pressed {
            background-color: #11c9f5;
            color: #0e1016;
        }

        #skipButton {
            background-color: #14161d;
            color: #ff6b6b;
            border: 1px solid #ff6b6b;
        }

        #skipButton:hover {
            background-color: #1a1d25;
            border: 1px solid #ff8c8c;
        }

        #skipButton:pressed {
            background-color: #ff6b6b;
            color: #0e1016;
        }

        /* Result Label */
        #resultLabel {
            color: white;
            font-size: 16px;
            min-height: 30px;
            font-weight: bold;
        }
        """

        # Additional styles for the album selector
        additional_styles = """
        /* Album Selector Styles */
        #artistAlbumSelector {
            background-color: transparent;
        }

        /* Welcome Frame */
        #welcomeFrame {
            background-color: #191b22;
            border: 1px solid #2a2d35;
            border-radius: 10px;
        }

        #welcomeLogo {
            color: #e6c15a;
            font-size: 42px;
            margin-bottom: 10px;
        }

        #welcomeTitle {
            color: #e6c15a;
            font-size: 28px;
            font-weight: bold;
            letter-spacing: 1px;
            margin-bottom: 15px;
        }

        #welcomeText {
            color: #d0d0d0;
            font-size: 16px;
            line-height: 1.5;
        }

        /* How to Play Frame */
        #howToFrame {
            background-color: #191b22;
            border: 1px solid #2a2d35;
            border-radius: 10px;
        }

        #howToTitle {
            color: #11c9f5;
            font-size: 20px;
            font-weight: bold;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        #howToText {
            color: #d0d0d0;
            font-size: 16px;
            line-height: 1.8;
        }

        /* Selection Frame */
        #selectionFrame {
            background-color: #191b22;
            border: 1px solid #2a2d35;
            border-radius: 10px;
        }

        #selectorTitle {
            color: #e6c15a;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        #selectorLabel {
            color: #aaaaaa;
            font-size: 14px;
            font-weight: bold;
            margin-top: 5px;
            margin-bottom: 5px;
        }

        #artistCombo, #albumCombo {
            background-color: #14161d;
            border: 1px solid #1e2028;
            border-radius: 8px;
            padding: 5px 15px;
            color: white;
            font-size: 16px;
        }

        #artistCombo::drop-down, #albumCombo::drop-down {
            border: none;
            width: 30px;
        }

        #artistCombo::down-arrow, #albumCombo::down-arrow {
            width: 14px;
            height: 14px;
            image: none;
            border-left: 2px solid #e6c15a;
            border-bottom: 2px solid #e6c15a;
            margin-right: 10px;
            transform: rotate(-45deg);
        }

        #artistCombo QAbstractItemView, #albumCombo QAbstractItemView {
            border: 1px solid #1e2028;
            border-radius: 5px;
            background-color: #1a1d25;
            color: white;
            selection-background-color: #2a2d35;  /* Darker selection background */
            selection-color: #e6c15a;  /* Gold text for selected item */
            outline: 0;
        }

        #artistCombo:focus, #albumCombo:focus {
            border: 1px solid #e6c15a;
        }

        #albumInfo {
            color: #11c9f5;
            font-size: 16px;
            margin: 15px 0;
            font-weight: bold;
        }

        #confirmButton {
            background-color: #14161d;
            color: #e6c15a;
            border: 2px solid #e6c15a;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 1px;
            margin-top: 15px;
        }

        #confirmButton:hover {
            background-color: #1a1d25;
            border: 2px solid #f0cc62;
        }

        #confirmButton:pressed {
            background-color: #e6c15a;
            color: #0e1016;
        }

        #albumDisplayFrame {
            background-color: #14161d;
            border: 1px solid #1e2028;
            border-radius: 8px;
            padding: 10px;
        }

        #albumValue {
            color: #e6c15a;
            font-size: 18px;
            font-weight: bold;
        }

        #changeAlbumButton {
            background-color: #14161d;
            color: #e6c15a;
            border: 1px solid #e6c15a;
        }

        #changeAlbumButton:hover {
            background-color: #1a1d25;
            border: 1px solid #f0cc62;
        }

        #changeAlbumButton:pressed {
            background-color: #e6c15a;
            color: #0e1016;
        }
        """

        # Combine the styles and apply them
        self.setStyleSheet(base_stylesheet + additional_styles)


# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SongGuesserApp()
    window.show()
    sys.exit(app.exec())