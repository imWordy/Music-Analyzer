
import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QDialog, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWebEngineWidgets import QWebEngineView

from Main import main as MainApp

class Worker(QThread):
    """
    Worker thread to run background tasks without freezing the GUI.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)

class AuthDialog(QDialog):
    def __init__(self, auth_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spotify Login")
        self.setGeometry(100, 100, 600, 800)
        layout = QVBoxLayout(self)
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.web_view.setUrl(QUrl(auth_url))

class AuthWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("Music Analyzer")
        title_font = QFont("Arial", 32, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Explore and analyze your favorite music from Spotify")
        subtitle_font = QFont("Arial", 14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(40)

        auth_frame = QFrame()
        auth_frame.setFrameShape(QFrame.Shape.StyledPanel)
        auth_frame.setFrameShadow(QFrame.Shadow.Raised)
        auth_layout = QVBoxLayout(auth_frame)
        layout.addWidget(auth_frame)

        auth_title = QLabel("Choose Your Authentication Method")
        auth_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        auth_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        auth_layout.addWidget(auth_title)

        buttons_layout = QHBoxLayout()
        auth_layout.addLayout(buttons_layout)

        # Client Credentials Auth
        client_auth_layout = QVBoxLayout()
        client_auth_button = QPushButton("Public Access")
        client_auth_button.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DesktopIcon))
        client_auth_button.clicked.connect(self.main_window.authenticate_client)
        client_auth_layout.addWidget(client_auth_button)
        client_auth_desc = QLabel("Access public data like tracks, albums, and artists.")
        client_auth_desc.setWordWrap(True)
        client_auth_layout.addWidget(client_auth_desc)
        buttons_layout.addLayout(client_auth_layout)

        # User Auth
        user_auth_layout = QVBoxLayout()
        user_auth_button = QPushButton("Personalized Access")
        user_auth_button.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DirHomeIcon))
        user_auth_button.clicked.connect(self.main_window.start_user_auth)
        user_auth_layout.addWidget(user_auth_button)
        user_auth_desc = QLabel("Access your personal data like top tracks, artists, and recently played.")
        user_auth_desc.setWordWrap(True)
        user_auth_layout.addWidget(user_auth_desc)
        buttons_layout.addLayout(user_auth_layout)

        layout.addStretch()

        self.auth_status_label = QLabel("Not Authenticated")
        self.auth_status_label.setFont(QFont("Arial", 12))
        self.auth_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.auth_status_label)

class MusicAnalyzerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.main_app = MainApp()
        self.workers = []
        self.setWindowTitle("Music Analyzer")
        self.setGeometry(100, 100, 900, 700)

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Authentication Tab
        self.auth_tab = QWidget()
        self.tabs.addTab(self.auth_tab, "Authentication")
        self.init_auth_tab()

        # Search Tab
        self.search_tab = QWidget()
        self.tabs.addTab(self.search_tab, "Search")
        self.init_search_tab()

        # User Data Tab
        self.user_data_tab = QWidget()
        self.tabs.addTab(self.user_data_tab, "User Data")
        self.init_user_data_tab()
        
        # Top 100 Tab
        self.top_100_tab = QWidget()
        self.tabs.addTab(self.top_100_tab, "Global Top 100")
        self.init_top_100_tab()

        self.set_ui_enabled(False)

    def init_auth_tab(self):
        self.auth_widget = AuthWidget(self)
        layout = QVBoxLayout(self.auth_tab)
        layout.addWidget(self.auth_widget)

    def init_search_tab(self):
        layout = QVBoxLayout()

        form_layout = QHBoxLayout()
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("General Query")
        self.track_name_input = QLineEdit()
        self.track_name_input.setPlaceholderText("Track Name")
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("Artist")
        
        form_layout.addWidget(self.query_input)
        form_layout.addWidget(self.track_name_input)
        form_layout.addWidget(self.artist_input)
        layout.addLayout(form_layout)

        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_tracks)
        layout.addWidget(search_button)

        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(4)
        self.search_results_table.setHorizontalHeaderLabels(["Track", "Artist", "Album", "Release Date"])
        self.search_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.search_results_table)

        self.search_tab.setLayout(layout)

    def init_user_data_tab(self):
        layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Recently Played
        self.recently_played_table = QTableWidget()
        self.recently_played_table.setColumnCount(3)
        self.recently_played_table.setHorizontalHeaderLabels(["Track", "Artist", "Played At"])
        self.recently_played_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Top Tracks
        self.top_tracks_table = QTableWidget()
        self.top_tracks_table.setColumnCount(3)
        self.top_tracks_table.setHorizontalHeaderLabels(["Track", "Artist", "Popularity"])
        self.top_tracks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Top Artists
        self.top_artists_table = QTableWidget()
        self.top_artists_table.setColumnCount(2)
        self.top_artists_table.setHorizontalHeaderLabels(["Artist", "Genres"])
        self.top_artists_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        splitter.addWidget(self.recently_played_table)
        splitter.addWidget(self.top_tracks_table)
        splitter.addWidget(self.top_artists_table)
        layout.addWidget(splitter)

        buttons_layout = QHBoxLayout()
        self.recently_played_button = QPushButton("Update Recently Played")
        self.recently_played_button.clicked.connect(self.get_recently_played)
        buttons_layout.addWidget(self.recently_played_button)

        self.top_tracks_button = QPushButton("Update Top Tracks")
        self.top_tracks_button.clicked.connect(self.get_top_tracks)
        buttons_layout.addWidget(self.top_tracks_button)

        self.top_artists_button = QPushButton("Update Top Artists")
        self.top_artists_button.clicked.connect(self.get_top_artists)
        buttons_layout.addWidget(self.top_artists_button)
        
        layout.addLayout(buttons_layout)
        self.user_data_tab.setLayout(layout)

    def init_top_100_tab(self):
        layout = QVBoxLayout()

        self.update_top_100_button = QPushButton("Update Top 100 from Spotify")
        self.update_top_100_button.clicked.connect(self.fetch_top_100)
        layout.addWidget(self.update_top_100_button)

        self.top_100_status_label = QLabel("")
        layout.addWidget(self.top_100_status_label)

        self.top_100_table = QTableWidget()
        self.top_100_table.setColumnCount(4)
        self.top_100_table.setHorizontalHeaderLabels(["Track", "Artist", "Album", "Release Date"])
        self.top_100_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.top_100_table)
        
        self.top_100_tab.setLayout(layout)

    def start_worker(self, fn, on_finished, *args, **kwargs):
        worker = Worker(fn, *args, **kwargs)
        worker.finished.connect(on_finished)
        worker.error.connect(self.on_worker_error)
        worker.finished.connect(lambda: self.workers.remove(worker))
        worker.error.connect(lambda: self.workers.remove(worker))
        self.workers.append(worker)
        worker.start()

    def set_ui_enabled(self, enabled, is_user_auth=False):
        self.search_tab.setEnabled(enabled)
        self.top_100_tab.setEnabled(enabled)
        self.user_data_tab.setEnabled(is_user_auth)

    def authenticate_client(self):
        self.start_worker(self.main_app.authenticate_client, self.on_auth_finished)

    def start_user_auth(self):
        auth_url = self.main_app.session.get_auth_url()
        self.auth_dialog = AuthDialog(auth_url, self)
        self.auth_dialog.web_view.urlChanged.connect(self.on_url_changed)
        self.auth_dialog.exec()

    def on_url_changed(self, url):
        url_str = url.toString()
        if self.main_app.session.redirectUri in url_str:
            self.auth_dialog.web_view.stop()
            self.auth_dialog.close()
            self.start_worker(self.main_app.session.fetch_token_from_url, self.on_auth_finished, url_str)

    def on_auth_finished(self, auth_info):
        if auth_info and auth_info.get("token"):
            method = auth_info.get("method")
            is_user_auth = method == "user_login"
            
            if method == "client_credentials":
                self.auth_widget.auth_status_label.setText("Authenticated with Client Credentials")
                self.set_ui_enabled(True)
            elif is_user_auth:
                self.auth_widget.auth_status_label.setText("Authenticated as User")
                self.set_ui_enabled(True, is_user_auth=True)
                self.load_initial_user_data()

            self.load_top_100_from_db()
        else:
            self.auth_widget.auth_status_label.setText("Authentication Failed")
            self.set_ui_enabled(False)

    def search_tracks(self):
        track_name = self.track_name_input.text().strip() or None
        artist = self.artist_input.text().strip() or None
        query = self.query_input.text().strip()

        self.start_worker(self.main_app.session.searchTrack, self.on_search_finished,
                          track=track_name, artist=artist, query=query, limit=20)

    def on_search_finished(self, results):
        self.search_results_table.setRowCount(0)
        if not results:
            return
        
        self.search_results_table.setRowCount(len(results))
        for i, t in enumerate(results):
            self.search_results_table.setItem(i, 0, QTableWidgetItem(t.get('trackName', 'N/A')))
            self.search_results_table.setItem(i, 1, QTableWidgetItem(t.get('artistName', 'N/A')))
            self.search_results_table.setItem(i, 2, QTableWidgetItem(t.get('albumName', 'N/A')))
            self.search_results_table.setItem(i, 3, QTableWidgetItem(t.get('releaseDate', 'N/A')))

    def load_initial_user_data(self):
        self.get_recently_played()
        self.get_top_tracks()
        self.get_top_artists()

    def get_recently_played(self):
        self.start_worker(self.main_app.data_Retrieval.get_recently_played, self.on_recently_played_finished)

    def on_recently_played_finished(self, results):
        self.recently_played_table.setRowCount(0)
        if not results:
            return
        
        self.recently_played_table.setRowCount(len(results))
        for i, item in enumerate(results):
            track_item = item.get("track", {})
            track_name = track_item.get('name', 'N/A')
            artist_name = track_item.get('artists', [{}])[0].get('name', 'N/A')
            played_at = item.get('played_at', 'N/A')
            self.recently_played_table.setItem(i, 0, QTableWidgetItem(track_name))
            self.recently_played_table.setItem(i, 1, QTableWidgetItem(artist_name))
            self.recently_played_table.setItem(i, 2, QTableWidgetItem(played_at))

    def get_top_tracks(self):
        self.start_worker(self.main_app.data_Retrieval.get_top_tracks, self.on_top_tracks_finished)

    def on_top_tracks_finished(self, results):
        self.top_tracks_table.setRowCount(0)
        if not results:
            return
            
        self.top_tracks_table.setRowCount(len(results))
        for i, t_item in enumerate(results):
            track_name = t_item.get('name', 'N/A')
            artist_name = t_item.get('artists', [{}])[0].get('name', 'N/A')
            popularity = t_item.get('popularity', 'N/A')
            self.top_tracks_table.setItem(i, 0, QTableWidgetItem(track_name))
            self.top_tracks_table.setItem(i, 1, QTableWidgetItem(artist_name))
            self.top_tracks_table.setItem(i, 2, QTableWidgetItem(str(popularity)))

    def get_top_artists(self):
        self.start_worker(self.main_app.data_Retrieval.get_top_artists, self.on_top_artists_finished)

    def on_top_artists_finished(self, results):
        self.top_artists_table.setRowCount(0)
        if not results:
            return

        self.top_artists_table.setRowCount(len(results))
        for i, a_item in enumerate(results):
            artist_name = a_item.get('name', 'N/A')
            genres = a_item.get('genres', [])
            genres_str = ', '.join(genres) if genres else 'Unknown'
            self.top_artists_table.setItem(i, 0, QTableWidgetItem(artist_name))
            self.top_artists_table.setItem(i, 1, QTableWidgetItem(genres_str))

    def load_top_100_from_db(self):
        self.top_100_status_label.setText("Loading existing Top 100 from database...")
        self.start_worker(self.main_app.db_api.get_top_hundred_tracks_for_display, self.on_display_top_100_finished)

    def fetch_top_100(self):
        self.update_top_100_button.setEnabled(False)
        self.top_100_status_label.setText("Fetching Top 100 playlist from Spotify...")
        self.start_worker(self.main_app.data_Retrieval.get_top_100_playlist, self.on_fetch_top_100_finished)

    def on_fetch_top_100_finished(self, success):
        if success:
            self.top_100_status_label.setText("Playlist fetched. Now processing data...")
            self.start_worker(self.main_app.data_Processing.populate_derived_data_threading, self.on_processing_finished)
        else:
            self.top_100_status_label.setText("Failed to fetch Top 100 playlist.")
            self.update_top_100_button.setEnabled(True)

    def on_processing_finished(self, result):
        self.top_100_status_label.setText("Data processing complete. Fetching data for display...")
        self.load_top_100_from_db()

    def on_display_top_100_finished(self, results):
        self.top_100_table.setRowCount(0)
        if not results:
            self.top_100_status_label.setText("No Top 100 tracks found in the database.")
            self.update_top_100_button.setEnabled(True)
            return

        self.top_100_status_label.setText("Displaying Top 100 Global Playlist from Database")
        self.top_100_table.setRowCount(len(results))
        for i, row_data in enumerate(results):
            self.top_100_table.setItem(i, 0, QTableWidgetItem(row_data[0]))
            self.top_100_table.setItem(i, 1, QTableWidgetItem(row_data[1]))
            self.top_100_table.setItem(i, 2, QTableWidgetItem(row_data[2]))
            self.top_100_table.setItem(i, 3, QTableWidgetItem(str(row_data[3])))
        self.update_top_100_button.setEnabled(True)

    def on_worker_error(self, error):
        self.update_top_100_button.setEnabled(True)
        error_message = f"An error occurred: {error}"
        print(error_message)
        self.auth_widget.auth_status_label.setText(error_message)

    def closeEvent(self, event):
        for worker in self.workers[:]:
            worker.quit()
            worker.wait()
        self.main_app.close_app()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MusicAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())
