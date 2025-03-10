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
                                   QComboBox, QScrollArea, QRadioButton, QButtonGroup,
                                   QDialog, QListWidget, QSpacerItem)
    from PySide6.QtCore import Qt, QRect, QPoint, Signal
    from PySide6.QtGui import QFont, QIcon, QPainterPath, QRegion
    from PySide6 import QtCore, QtWidgets, QtGui

    # Import album databases
    from albums_database import (the_weeknd_albums, billie_eilish_albums,
                                 lana_del_rey_albums, tame_impala_albums,
                                 olivia_rodrigo_albums, kanye_west_albums,
                                 dua_lipa_albums, taylor_swift_albums,
                                 eminem_albums, xxxtentacion_albums, juice_wrld_albums)

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

#######################################################################################################################

# Artist constants
The_Weeknd = "The Weeknd"
Billie_Eilish = "Billie Eilish"
Lana_Del_Rey = "Lana Del Rey"
Tame_Impala = "Tame Impala"
Olivia_Rodrigo = "Olivia Rodrigo"
Kanye_West = "Kanye West"
Dua_Lipa = "Dua Lipa"
Taylor_Swift = "Taylor Swift"
XXXTETACION = "XXXTENTACION"
Eminem = "Eminem"
Juice_WRLD = "Juice WRLD"

#######################################################################################################################

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
    Get random meaningful lines from song lyrics.

    Args:
        title (str): Song title
        artist (str): Artist name

    Returns:
        tuple: (str, list) - A random line from the lyrics and additional lines for hints
    """
    full_lyrics = get_lyrics(title, artist)

    if not full_lyrics:
        return "Lyrics not found.", []

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

    # Return random lines if we have any valid lines
    if clean_lines:
        if len(clean_lines) <= 1:
            return "\n".join(clean_lines), []

        # Select a random starting index
        start_idx = random.randint(0, len(clean_lines) - 1)

        # Get the first line
        selected_line = clean_lines[start_idx]

        # Get additional lines for hints
        hint_lines = []
        for i in range(1, 5):  # Get up to 4 additional lines for hints
            next_idx = (start_idx + i) % len(clean_lines)
            hint_lines.append(clean_lines[next_idx])

        # Check if the first line has 7 or fewer words
        words = [word for word in selected_line.split() if word]
        if len(words) <= 6 and len(clean_lines) > 1:
            # Add the next line immediately
            next_idx = (start_idx + 1) % len(clean_lines)
            selected_line = f"{selected_line}\n{clean_lines[next_idx]}"
            # Remove this line from hint lines
            if hint_lines:
                hint_lines.pop(0)

        print_debug(f"Selected lyric: {selected_line}")
        print_debug(f"Hint lines available: {len(hint_lines)}")

        return selected_line, hint_lines
    else:
        print_warning(f"No suitable lyrics found for: {title} by {artist}")
        return "No suitable lyrics found.", []


# UI Components

class SongSuggestionDialog(QDialog):
    songSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setObjectName("suggestionDialog")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("suggestionList")
        self.list_widget.itemClicked.connect(self.on_item_selected)

        self.layout.addWidget(self.list_widget)

        # Note: Styles are now in style.qss file

    def set_suggestions(self, songs):
        """Update the list with new song suggestions"""
        self.list_widget.clear()
        for song in songs:
            self.list_widget.addItem(song)

        # Set size based on content
        item_height = 36  # Approximate height per item
        max_height = min(350, len(songs) * item_height + 10)
        width = max(300, self.parent().width() if self.parent() else 300)
        self.setFixedSize(width, max_height)

    def on_item_selected(self, item):
        """Emit signal when a song is selected"""
        self.songSelected.emit(item.text())
        self.hide()

    def keyPressEvent(self, event):
        """Handle keyboard navigation in the list"""
        key = event.key()

        if key == Qt.Key_Escape:
            self.hide()
            event.accept()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            current_item = self.list_widget.currentItem()
            if current_item:
                self.on_item_selected(current_item)
            event.accept()
        elif key == Qt.Key_Up or key == Qt.Key_Down:
            # Pass arrow keys to the list
            self.list_widget.keyPressEvent(event)
        else:
            # Pass other keys to the parent (input field)
            if self.parent():
                self.parent().keyPressEvent(event)
            super().keyPressEvent(event)


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
        self.selection_frame = selection_frame  # Store reference for later access
        selection_layout = QVBoxLayout(selection_frame)
        selection_layout.setContentsMargins(25, 20, 25, 25)  # Reduced top margin to 20px
        selection_layout.setSpacing(20)

        # Title - direct positioning
        title = QLabel("SELECT YOUR MUSIC")
        title.setObjectName("selectorTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumHeight(35)
        title.setContentsMargins(0, 0, 0, 5)  # Minimal margins

        # Create spacer for fine-tuned positioning
        spacer = QSpacerItem(20, 2, QSizePolicy.Minimum, QSizePolicy.Fixed)

        # Custom layout arrangement to position title higher
        selection_layout.addSpacerItem(spacer)  # Tiny spacer at top
        selection_layout.addWidget(title)  # Add title immediately after small spacer
        selection_layout.addSpacing(10)  # Add space after title

        # Apply specific style with negative margins to pull it up
        title.setStyleSheet("color: #e6c15a; font-size: 24px; font-weight: bold; margin-top: -5px;")

        # Artist selection
        artist_label = QLabel("CHOOSE AN ARTIST")
        artist_label.setObjectName("selectorLabel")
        self.artist_combo = QComboBox()
        self.artist_combo.setObjectName("artistCombo")
        self.artist_combo.setMinimumHeight(45)

        ###################################################################################################################

        # Add artists
        self.artists = {
            "The Weeknd": the_weeknd_albums,
            "Billie Eilish": billie_eilish_albums,
            "Lana Del Rey": lana_del_rey_albums,
            "Tame Impala": tame_impala_albums,
            "Olivia Rodrigo": olivia_rodrigo_albums,
            "Kanye West": kanye_west_albums,
            "Dua Lipa": dua_lipa_albums,
            "Taylor Swift": taylor_swift_albums,
            "Eminem": eminem_albums,
            "XXXTENTACION": xxxtentacion_albums,
            "Juice WRLD": juice_wrld_albums

        }

        ####################################################################################################################

        for artist in self.artists.keys():
            self.artist_combo.addItem(artist)

        self.artist_combo.currentTextChanged.connect(self.update_albums)

        # Album selection
        album_label = QLabel("SELECT AN ALBUM")
        album_label.setObjectName("selectorLabel")
        self.album_combo = QComboBox()
        self.album_combo.setObjectName("albumCombo")
        self.album_combo.setMinimumHeight(45)

        # Let's remove these lines since we're using a simpler approach now
        # self.album_combo.view().setItemDelegate(QtWidgets.QStyledItemDelegate())
        # self.album_combo.currentIndexChanged.connect(self.style_album_option)

        # Album info display with improved visibility
        self.album_info = QLabel()
        self.album_info.setObjectName("albumInfo")
        self.album_info.setAlignment(Qt.AlignCenter)
        self.album_info.setMinimumHeight(40)  # Taller minimum height
        self.album_info.setStyleSheet(
            "color: #11c9f5; font-size: 16px; font-weight: bold; margin: 15px 0;")  # Direct styling

        # Confirm button
        self.confirm_button = QPushButton("START PLAYING")
        self.confirm_button.setObjectName("confirmButton")
        self.confirm_button.setMinimumHeight(50)
        self.confirm_button.clicked.connect(self.confirm_selection)

        # Make sure to add the album info to the layout
        selection_layout.addWidget(artist_label)
        selection_layout.addWidget(self.artist_combo)
        selection_layout.addWidget(album_label)
        selection_layout.addWidget(self.album_combo)

        # Add a spacer between combo and info
        selection_layout.addSpacing(10)

        # Add album info in a separate frame to make it more visible
        info_frame = QFrame()
        info_frame.setMinimumHeight(50)
        info_frame.setStyleSheet("background-color: #191b22; border-radius: 8px; padding: 5px;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.addWidget(self.album_info)
        selection_layout.addWidget(info_frame)

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
            "1. Select an artist and album\n2. Read the displayed lyrics\n3. Guess which song they're from\n4. Use HINT for more lyrics (only once per song)\n5. Build your streak and score!")
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
            # Add "All Albums" option first with special prefix
            self.album_combo.addItem("⭐ All Albums ⭐")

            # Add individual albums
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

        # First make sure the label is visible
        self.album_info.setVisible(True)

        if album == "⭐ All Albums ⭐":
            # Count total songs across all albums
            total_songs = 0
            for album_data in self.artists[artist].values():
                total_songs += len(album_data["songs"])
            self.album_info.setText(f"Total: {total_songs} songs")
        elif artist in self.artists and album in self.artists[artist]:
            album_data = self.artists[artist][album]
            year = album_data["release_year"]
            song_count = len(album_data["songs"])
            self.album_info.setText(f"{year} • {song_count} songs")

        # Print for debugging
        print_debug(f"Album info updated: {self.album_info.text()}")

    def confirm_selection(self):
        """Emit signal with selected artist, album and songs"""
        artist = self.artist_combo.currentText()
        album = self.album_combo.currentText()

        if artist in self.artists:
            if album == "⭐ All Albums ⭐":
                # Collect all songs from all albums by this artist
                all_songs = []
                for album_name, album_data in self.artists[artist].items():
                    all_songs.extend(album_data["songs"])
                self.selectionMade.emit(artist, "All Albums", all_songs)
            elif album in self.artists[artist]:
                songs = self.artists[artist][album]["songs"]
                self.selectionMade.emit(artist, album, songs)


# Main Application Class
class SongGuesserApp(QMainWindow):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint)
        self.setWindowTitle("Melo-Guesser")

        # Get screen size and calculate window size
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # Set window size based on screen resolution
        if screen_width >= 2560:  # 2K or higher resolution
            # For 2K+, use the original scaling
            width = int(screen_width * 0.55)
            height = int(screen_height * 0.7)
        else:  # Full HD or lower resolution
            # Make the app significantly taller on Full HD screens - increase to 85%
            width = int(screen_width * 0.65)
            height = int(screen_height * 0.9)  # Increased from 0.85 to 0.9 (90% of screen height)

        # Enforce minimum dimensions
        min_width = 650
        min_height = 700  # Increased from 600 to 700
        width = max(width, min_width)
        height = max(height, min_height)

        # Center window
        window_x = (screen_width - width) // 2
        window_y = (screen_height - height) // 2
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
        self.hint_lines = []
        self.hint_used = False

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

        # Progress bar removed from here

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

        # Create a line edit with custom song suggestion dialog
        self.guess_input = QLineEdit()
        self.guess_input.setPlaceholderText("Start typing to see song suggestions...")
        self.guess_input.setObjectName("guessInput")
        self.guess_input.setMinimumHeight(50)
        self.guess_input.textChanged.connect(self.on_guess_text_changed)
        self.guess_input.returnPressed.connect(self.submit_guess)
        input_layout.addWidget(self.guess_input)

        # Create the suggestion dialog
        self.suggestion_dialog = SongSuggestionDialog(self.guess_input)
        self.suggestion_dialog.songSelected.connect(self.on_song_selected)

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

        # HINT button (replacing NEW SONG button)
        self.hint_button = GuessButton("HINT", icon="💡")
        self.hint_button.clicked.connect(self.show_hint)
        self.hint_button.setObjectName("newSongButton")  # Keep same styling

        self.skip_button = GuessButton("SKIP", icon="⏭️")
        self.skip_button.clicked.connect(self.skip_song)
        self.skip_button.setObjectName("skipButton")

        self.change_album_button = GuessButton("MAIN MENU", icon="💿")
        self.change_album_button.clicked.connect(self.change_album)
        self.change_album_button.setObjectName("changeAlbumButton")

        buttons_layout.addWidget(self.hint_button)
        buttons_layout.addWidget(self.skip_button)
        buttons_layout.addWidget(self.change_album_button)

        self.game_layout.addLayout(buttons_layout)

        # Add the game widget to content
        self.content_layout.addWidget(self.game_widget)

        # Add content to main layout
        main_layout.addWidget(self.content)

        # Apply stylesheet
        self.apply_stylesheet()

        # Apply resolution-specific adjustments
        self.adjust_for_resolution()

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
        self.max_streak = 0  # Reset max streak when changing albums
        self.songs_played = 0
        self.score_label.setText("0")
        self.streak_label.setText("0")

        # Show loading message
        self.lyric_label.setText("Now loading...")

        # Load first song with slight delay to allow UI to update
        QtCore.QTimer.singleShot(100, self.new_song)

    def new_song(self):
        """Load a new random song from the selected album"""
        try:
            if not self.selected_songs:
                return

            # Choose a random song from the album
            self.current_song = random.choice(self.selected_songs)

            # Show loading message and style
            self.lyric_label.setText("Now loading...")
            self.result_label.setText("")

            # Reset input field safely
            self.guess_input.clear()
            # Hide suggestion dialog if visible
            if hasattr(self, 'suggestion_dialog'):
                self.suggestion_dialog.hide()

            # Reset hint state
            self.hint_used = False
            self.hint_lines = []

            self.songs_played += 1

            # Use a QTimer to allow the UI to update before fetching lyrics (which might be slow)
            QtCore.QTimer.singleShot(100, lambda: self.fetch_and_display_lyrics())

            print_success(f"New song loaded: {self.current_song} by {self.current_artist}")
        except Exception as e:
            print_error(f"Error in new_song: {e}")

    def fetch_and_display_lyrics(self):
        """Fetch and display lyrics for the current song"""
        # Get a random lyric line and hint lines
        lyric, self.hint_lines = get_random_lyric_line(self.current_song, self.current_artist)
        self.lyric_label.setText(lyric)
        self.hint_used = False

    def show_hint(self):
        """Show additional lyrics as a hint"""
        if not self.current_song or not self.hint_lines:
            return

        # Check if hint was already used
        if self.hint_used:
            self.result_label.setText("You've already used your hint for this song!")
            return

        # Mark that a hint was used
        self.hint_used = True

        # Get the current lyrics
        current_lyrics = self.lyric_label.text()

        # Add up to 2 more lines from the hint lines
        lines_to_add = min(2, len(self.hint_lines))

        if lines_to_add <= 0:
            self.result_label.setText("No hints available for this song!")
            return

        new_lines = []
        for i in range(lines_to_add):
            if i < len(self.hint_lines):
                new_lines.append(self.hint_lines[i])

        # Update the lyrics display
        updated_lyrics = current_lyrics + "\n" + "\n".join(new_lines)
        self.lyric_label.setText(updated_lyrics)

        # Inform the user
        self.result_label.setText("Hint added! Score and streak will not increase if you guess correctly now.")

    def skip_song(self):
        """Skip the current song"""
        if self.current_song:
            # Reset score when skipping, but keep streak
            self.score = 0
            self.score_label.setText(str(self.score))

            self.result_label.setText(f"The song was: {self.current_song}")

            # Show loading for the next song
            QtCore.QTimer.singleShot(2000, lambda: self.lyric_label.setText("Now loading..."))
            # Load a new song after short delay
            QtCore.QTimer.singleShot(2100, self.new_song)

    def on_guess_text_changed(self, text):
        """Handle text changes in the guess input field"""
        try:
            if not text or len(text) < 1 or not self.selected_songs:
                self.suggestion_dialog.hide()
                return

            # Filter songs that contain the text (case insensitive)
            text_lower = text.lower()
            matching_songs = [song for song in self.selected_songs
                              if text_lower in song.lower()]

            # Update and show the suggestion dialog if we have matches
            if matching_songs:
                self.suggestion_dialog.set_suggestions(matching_songs)

                # Position the dialog below the input field
                pos = self.guess_input.mapToGlobal(
                    QPoint(0, self.guess_input.height()))
                self.suggestion_dialog.move(pos)
                self.suggestion_dialog.show()
            else:
                self.suggestion_dialog.hide()
        except Exception as e:
            print_error(f"Error in on_guess_text_changed: {e}")

    def on_song_selected(self, song):
        """Handle song selection from the suggestion dialog"""
        try:
            self.guess_input.setText(song)
            self.guess_input.setFocus()
        except Exception as e:
            print_error(f"Error in on_song_selected: {e}")

    def submit_guess(self):
        """Process the user's guess"""
        try:
            # Hide suggestion dialog
            self.suggestion_dialog.hide()

            # Get the guess text
            guess = self.guess_input.text().strip()
            if not guess:
                return

            if not self.current_song:
                self.result_label.setText("Please skip to get a new song first!")
                return

            # Improved string matching with some flexibility
            if self.is_correct_guess(guess, self.current_song):
                # Only increase score and streak if hint wasn't used
                if not self.hint_used:
                    self.score += 1
                    self.score_label.setText(str(self.score))

                    # Only increase streak if hint wasn't used
                    self.streak += 1
                    self.max_streak = max(self.max_streak, self.streak)
                    self.streak_label.setText(str(self.streak))

                    success_message = "Correct! 🎵 The song was " + self.current_song
                else:
                    success_message = "Correct with hint! 🎵 The song was " + self.current_song

                # Show success message with animations
                self.result_label.setText(success_message)

                # Highlight the score with animation
                self.score_label.setStyleSheet("color: #6eff8a; font-size: 24px; font-weight: bold;")
                QtCore.QTimer.singleShot(1000, lambda: self.score_label.setStyleSheet(""))

                # Show loading for the next song
                QtCore.QTimer.singleShot(2000, lambda: self.lyric_label.setText("Now loading..."))
                # Load a new song after displaying success
                QtCore.QTimer.singleShot(2100, self.new_song)
            else:
                # Reset score on wrong answer, but keep streak
                self.score = 0
                self.score_label.setText(str(self.score))

                self.result_label.setText("Incorrect, try again!")
        except Exception as e:
            print_error(f"Error in submit_guess: {e}")

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
        self.max_streak = 0  # Reset max streak when changing albums

        # Hide game and show selector
        self.game_widget.hide()
        self.album_selector.show()

    def apply_stylesheet(self):
        """Apply the external stylesheet from style.qss with appropriate scaling"""
        try:
            # Find the stylesheet file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            style_path = os.path.join(script_dir, "style.qss")

            if os.path.exists(style_path):
                # Open and read the stylesheet
                with open(style_path, "r") as style_file:
                    stylesheet = style_file.read()

                # Apply the stylesheet
                self.setStyleSheet(stylesheet)
                print_success(f"Applied stylesheet from style.qss")
            else:
                print_error(f"Stylesheet not found at: {style_path}")
        except Exception as e:
            print_error(f"Error applying stylesheet: {e}")

    def fix_selector_title(self):
        """Directly fix the selector title visibility and position it higher"""
        try:
            # Find the title in the selection frame
            if hasattr(self.album_selector, 'selection_frame'):
                # Try to find the label by object name
                for child in self.album_selector.selection_frame.findChildren(QLabel):
                    if child.objectName() == "selectorTitle" or child.text() == "SELECT YOUR MUSIC":
                        # Fix the label position to move it higher
                        child.setMinimumHeight(40)

                        # Modify margins to position text higher
                        child.setContentsMargins(0, 5, 0, 10)

                        # Add margin-top: -10px to move text higher in its container
                        child.setStyleSheet(
                            "font-size: 24px; font-weight: bold; color: #e6c15a; margin-top: -10px; margin-bottom: 10px;")

                        print_debug("Moved selector title higher")
                        return

            print_debug("Could not find selector title to fix - manual adjustment may be needed")
        except Exception as e:
            print_error(f"Error fixing selector title: {e}")

    def adjust_for_resolution(self):
        """Apply specific size adjustments based on the screen resolution"""
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()

        if screen_width <= 1920:  # Full HD or lower resolution
            # Minimum heights for critical components
            min_height_combo = 45
            min_height_button = 50
            min_height_input = 50

            # Adjust selection frame vertical spacing
            if hasattr(self.album_selector, 'layout'):
                self.album_selector.layout().setSpacing(20)  # Increase spacing in selector view

            # Fix combo box heights
            if hasattr(self.album_selector, 'artist_combo'):
                self.album_selector.artist_combo.setMinimumHeight(min_height_combo)
            if hasattr(self.album_selector, 'album_combo'):
                self.album_selector.album_combo.setMinimumHeight(min_height_combo)

            # Fix button heights
            if hasattr(self.album_selector, 'confirm_button'):
                self.album_selector.confirm_button.setMinimumHeight(min_height_button)

            # Fix game UI elements
            if hasattr(self, 'guess_input'):
                self.guess_input.setMinimumHeight(min_height_input)
            if hasattr(self, 'submit_button'):
                self.submit_button.setMinimumHeight(min_height_button)
            if hasattr(self, 'hint_button'):
                self.hint_button.setMinimumHeight(min_height_button)
            if hasattr(self, 'skip_button'):
                self.skip_button.setMinimumHeight(min_height_button)
            if hasattr(self, 'change_album_button'):
                self.change_album_button.setMinimumHeight(min_height_button)

            # Increase vertical space throughout the app
            self.content_layout.setContentsMargins(20, 20, 20, 20)  # Increased top/bottom margins
            self.content_layout.setSpacing(25)  # Increased spacing between main elements

            # Set specific minimum height for selection frame
            if hasattr(self.album_selector, 'selection_frame'):
                # Access the title label inside the selection frame
                for child in self.album_selector.selection_frame.children():
                    if isinstance(child, QLabel) and child.objectName() == "selectorTitle":
                        # Ensure the label has enough space
                        child.setMinimumHeight(35)  # Increase minimum height
                        # Adjust margin if needed
                        child.setContentsMargins(0, 10, 0, 10)
                        print_debug("Adjusted selector title height and margins")

                # Add more padding at the top of the selection frame layout
                if hasattr(self.album_selector.selection_frame, 'layout'):
                    selection_layout = self.album_selector.selection_frame.layout()
                    if selection_layout:
                        current_margins = selection_layout.contentsMargins()
                        selection_layout.setContentsMargins(
                            current_margins.left(),
                            30,  # Increase top margin to 30px
                            current_margins.right(),
                            current_margins.bottom()
                        )
                        print_debug("Increased selection frame top margin")

            # Increase the height of the welcome frame
            if hasattr(self.album_selector, 'welcomeFrame'):
                self.album_selector.welcomeFrame.setMinimumHeight(200)  # Set minimum height

            # Increase the height of the how-to-play frame
            if hasattr(self.album_selector, 'howToFrame'):
                self.album_selector.howToFrame.setMinimumHeight(180)  # Set minimum height

            print_debug(f"Applied Full HD resolution adjustments with increased height")

            self.fix_selector_title()


    def adjust_ui_elements(self):
        """Adjust UI element dimensions based on window size"""
        # Calculate a scale factor based on window height
        scale_factor = self.height() / 900.0  # Assuming 900px is the "standard" height

        # Apply minimum heights to various UI elements
        button_height = max(int(50 * scale_factor), 40)  # Minimum 40px

        # Update button heights
        if hasattr(self, 'submit_button'):
            self.submit_button.setMinimumHeight(button_height)
        if hasattr(self, 'hint_button'):
            self.hint_button.setMinimumHeight(button_height)
        if hasattr(self, 'skip_button'):
            self.skip_button.setMinimumHeight(button_height)
        if hasattr(self, 'change_album_button'):
            self.change_album_button.setMinimumHeight(button_height)
        if hasattr(self, 'confirm_button'):
            self.confirm_button.setMinimumHeight(button_height)
        if hasattr(self, 'guess_input'):
            self.guess_input.setMinimumHeight(button_height)

    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        # Adjust UI elements based on window size
        QtCore.QTimer.singleShot(10, self.adjust_ui_elements)
        # Apply resolution-specific adjustments
        QtCore.QTimer.singleShot(20, self.adjust_for_resolution)

# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(script_dir, "assets", "image2.png")

    if os.path.exists(icon_path):
        print_success(f"Icon found at: {icon_path}")
        app.setWindowIcon(QIcon(icon_path))
    else:
        print_error(f"Icon not found at: {icon_path}")

    window = SongGuesserApp()
    window.show()
    sys.exit(app.exec())