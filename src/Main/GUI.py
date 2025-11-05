import os
import sys
import pandas as pd
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QDialog, 
                             QFrame, QListWidget, QListWidgetItem, QMessageBox, QGridLayout, 
                             QRadioButton, QButtonGroup)
from PySide6.QtCore import QThread, Signal, Qt, QUrl
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWebEngineWidgets import QWebEngineView
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from Main import main as MainApp
from Analysis import plot_single_feature
from Model import AnomalyDetector

class Worker(QThread):
    finished = Signal(object)
    error = Signal(Exception)

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
        title_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Explore and analyze your favorite music from Spotify")
        subtitle_label.setFont(QFont("Arial", 14))
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

        client_auth_layout = QVBoxLayout()
        client_auth_button = QPushButton("Public Access")
        client_auth_button.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DesktopIcon))
        client_auth_button.clicked.connect(self.main_window.authenticate_client)
        client_auth_layout.addWidget(client_auth_button)
        client_auth_desc = QLabel("Access public data and local analysis features.")
        client_auth_desc.setWordWrap(True)
        client_auth_layout.addWidget(client_auth_desc)
        buttons_layout.addLayout(client_auth_layout)

        user_auth_layout = QVBoxLayout()
        user_auth_button = QPushButton("Personalized Access")
        user_auth_button.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DirHomeIcon))
        user_auth_button.clicked.connect(self.main_window.start_user_auth)
        user_auth_layout.addWidget(user_auth_button)
        user_auth_desc = QLabel("Access your personal data like top tracks and recently played.")
        user_auth_desc.setWordWrap(True)
        user_auth_layout.addWidget(user_auth_desc)
        buttons_layout.addLayout(user_auth_layout)

        layout.addStretch()

        self.auth_status_label = QLabel("Not Authenticated")
        self.auth_status_label.setFont(QFont("Arial", 12))
        self.auth_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.auth_status_label)

class ComparisonDialog(QDialog):
    def __init__(self, df, track_ids, parent=None):
        super().__init__(parent)
        self.df = df
        self.track_ids = track_ids
        self.setWindowTitle("Compare Audio Features")
        self.setGeometry(200, 200, 700, 500)

        main_layout = QHBoxLayout(self)
        
        button_layout = QVBoxLayout()
        self.features = ['danceability', 'energy', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
        for feature in self.features:
            btn = QPushButton(feature.capitalize())
            btn.clicked.connect(lambda checked, f=feature: self.plot_feature(f))
            button_layout.addWidget(btn)
        
        main_layout.addLayout(button_layout)

        self.plot_widget = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_widget)
        main_layout.addWidget(self.plot_widget)

        self.plot_feature(self.features[0])

    def plot_feature(self, feature):
        for i in reversed(range(self.plot_layout.count())):
            widget = self.plot_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        fig = plot_single_feature(self.df, self.track_ids, feature)
        canvas = FigureCanvas(fig)
        self.plot_layout.addWidget(canvas)

class MusicAnalyzerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.main_app = MainApp()
        self.workers = []
        self.setWindowTitle("Music Analyzer")
        self.setGeometry(100, 100, 1000, 800)

        csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'DataBase', 'SpotifyAudioFeaturesApril2019.csv')
        try:
            self.data_df = pd.read_csv(csv_file_path)
            self.data_df['track_id'] = self.data_df['track_id'].astype(str)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", f"CSV file not found at {csv_file_path}")
            self.data_df = pd.DataFrame()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading CSV: {e}")
            self.data_df = pd.DataFrame()

        self.anomaly_detector = AnomalyDetector()

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.init_tabs()

        self.set_spotify_ui_enabled(False)
        if not self.data_df.empty:
            self.tabs.findChild(QWidget, "Analysis").setEnabled(True)
            self.tabs.findChild(QWidget, "Unique Tracks").setEnabled(True)
            self.load_all_tracks_for_analysis()

    def init_tabs(self):
        # Authentication Tab
        self.auth_tab = QWidget()
        self.auth_tab.setObjectName("Authentication")
        self.tabs.addTab(self.auth_tab, "Authentication")
        auth_layout = QVBoxLayout(self.auth_tab)
        self.auth_widget = AuthWidget(self)
        auth_layout.addWidget(self.auth_widget)

        # Local Analysis Tabs
        analysis_tab = QWidget()
        analysis_tab.setObjectName("Analysis")
        self.tabs.addTab(analysis_tab, "Analysis")
        self.init_analysis_tab(analysis_tab)

        unique_tracks_tab = QWidget()
        unique_tracks_tab.setObjectName("Unique Tracks")
        self.tabs.addTab(unique_tracks_tab, "Unique Tracks")
        self.init_unique_tracks_tab(unique_tracks_tab)

        # Spotify-dependent tabs
        self.search_tab = QWidget()
        self.search_tab.setObjectName("Search")
        self.tabs.addTab(self.search_tab, "Search")
        self.init_search_tab()

        self.user_data_tab = QWidget()
        self.user_data_tab.setObjectName("User Data")
        self.tabs.addTab(self.user_data_tab, "User Data")
        self.init_user_data_tab()
        
        self.top_100_tab = QWidget()
        self.top_100_tab.setObjectName("Top 100")
        self.tabs.addTab(self.top_100_tab, "Global Top 100")
        self.init_top_100_tab()

    def init_analysis_tab(self, tab):
        layout = QVBoxLayout(tab)
        self.tracks_table = QTableWidget()
        self.tracks_table.setColumnCount(2)
        self.tracks_table.setHorizontalHeaderLabels(["Track", "Artist"])
        self.tracks_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.tracks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tracks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tracks_table)

        compare_button = QPushButton("Compare Selected Tracks")
        compare_button.clicked.connect(self.open_comparison_dialog)
        layout.addWidget(compare_button)

    def init_unique_tracks_tab(self, tab):
        layout = QVBoxLayout(tab)
        find_button = QPushButton("Find Top 10 Most Unique Tracks")
        find_button.clicked.connect(self.find_unique_tracks)
        layout.addWidget(find_button)

        self.unique_tracks_table = QTableWidget()
        self.unique_tracks_table.setColumnCount(3)
        self.unique_tracks_table.setHorizontalHeaderLabels(["Track", "Artist", "Anomaly Score"])
        self.unique_tracks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.unique_tracks_table)

    def init_search_tab(self):
        layout = QVBoxLayout(self.search_tab)
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

    def init_user_data_tab(self):
        layout = QVBoxLayout(self.user_data_tab)
        layout.setSpacing(20)

        # --- Recently Played Section ---
        rp_frame = QFrame()
        rp_frame.setFrameShape(QFrame.Shape.StyledPanel)
        rp_layout = QVBoxLayout(rp_frame)
        
        rp_label = QLabel("Recently Played Tracks")
        rp_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        rp_layout.addWidget(rp_label)

        self.recently_played_table = QTableWidget()
        self.recently_played_table.setColumnCount(3)
        self.recently_played_table.setHorizontalHeaderLabels(["Track", "Artist", "Played At"])
        self.recently_played_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        rp_layout.addWidget(self.recently_played_table)

        self.recently_played_button = QPushButton("Update Recently Played")
        self.recently_played_button.clicked.connect(self.get_recently_played)
        rp_layout.addWidget(self.recently_played_button)
        
        layout.addWidget(rp_frame)

        # --- Top Tracks Section ---
        tt_frame = QFrame()
        tt_frame.setFrameShape(QFrame.Shape.StyledPanel)
        tt_layout = QVBoxLayout(tt_frame)

        tt_label = QLabel("Your Top Tracks")
        tt_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        tt_layout.addWidget(tt_label)

        tt_options_layout = QHBoxLayout()
        tt_options_layout.addWidget(QLabel("Time Range:"))
        self.tt_time_range_group = QButtonGroup(self)
        
        tt_short = QRadioButton("Short (4 wks)")
        tt_short.time_range = "short_term"
        tt_medium = QRadioButton("Medium (6 mos)")
        tt_medium.time_range = "medium_term"
        tt_medium.setChecked(True)
        tt_long = QRadioButton("Long (All time)")
        tt_long.time_range = "long_term"
        
        self.tt_time_range_group.addButton(tt_short)
        self.tt_time_range_group.addButton(tt_medium)
        self.tt_time_range_group.addButton(tt_long)
        
        tt_options_layout.addWidget(tt_short)
        tt_options_layout.addWidget(tt_medium)
        tt_options_layout.addWidget(tt_long)
        tt_options_layout.addStretch()
        tt_layout.addLayout(tt_options_layout)

        self.top_tracks_table = QTableWidget()
        self.top_tracks_table.setColumnCount(3)
        self.top_tracks_table.setHorizontalHeaderLabels(["Track", "Artist", "Popularity"])
        self.top_tracks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tt_layout.addWidget(self.top_tracks_table)

        self.top_tracks_button = QPushButton("Update Top Tracks")
        self.top_tracks_button.clicked.connect(self.get_top_tracks)
        tt_layout.addWidget(self.top_tracks_button)

        layout.addWidget(tt_frame)

        # --- Top Artists Section ---
        ta_frame = QFrame()
        ta_frame.setFrameShape(QFrame.Shape.StyledPanel)
        ta_layout = QVBoxLayout(ta_frame)

        ta_label = QLabel("Your Top Artists")
        ta_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        ta_layout.addWidget(ta_label)

        ta_options_layout = QHBoxLayout()
        ta_options_layout.addWidget(QLabel("Time Range:"))
        self.ta_time_range_group = QButtonGroup(self)

        ta_short = QRadioButton("Short (4 wks)")
        ta_short.time_range = "short_term"
        ta_medium = QRadioButton("Medium (6 mos)")
        ta_medium.time_range = "medium_term"
        ta_medium.setChecked(True)
        ta_long = QRadioButton("Long (All time)")
        ta_long.time_range = "long_term"

        self.ta_time_range_group.addButton(ta_short)
        self.ta_time_range_group.addButton(ta_medium)
        self.ta_time_range_group.addButton(ta_long)

        ta_options_layout.addWidget(ta_short)
        ta_options_layout.addWidget(ta_medium)
        ta_options_layout.addWidget(ta_long)
        ta_options_layout.addStretch()
        ta_layout.addLayout(ta_options_layout)

        self.top_artists_table = QTableWidget()
        self.top_artists_table.setColumnCount(2)
        self.top_artists_table.setHorizontalHeaderLabels(["Artist", "Genres"])
        self.top_artists_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ta_layout.addWidget(self.top_artists_table)

        self.top_artists_button = QPushButton("Update Top Artists")
        self.top_artists_button.clicked.connect(self.get_top_artists)
        ta_layout.addWidget(self.top_artists_button)

        layout.addWidget(ta_frame)

    def init_top_100_tab(self):
        layout = QVBoxLayout(self.top_100_tab)
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

    def load_all_tracks_for_analysis(self):
        if self.data_df.empty:
            return

        display_df = self.data_df.dropna(subset=['track_name', 'artist_name'])
        self.tracks_table.setRowCount(len(display_df))

        for i, row in enumerate(display_df.itertuples()):
            track_id = str(row.track_id)
            track_name = str(row.track_name)
            artist_name = str(row.artist_name)

            item_analysis = QTableWidgetItem(track_name)
            item_analysis.setData(Qt.ItemDataRole.UserRole, track_id)
            self.tracks_table.setItem(i, 0, item_analysis)
            self.tracks_table.setItem(i, 1, QTableWidgetItem(artist_name))

    def open_comparison_dialog(self):
        selected_rows = self.tracks_table.selectionModel().selectedRows()
        if len(selected_rows) != 2:
            QMessageBox.warning(self, "Selection Error", "Please select exactly two tracks to compare.")
            return

        track_ids = [self.tracks_table.item(row.row(), 0).data(Qt.ItemDataRole.UserRole) for row in selected_rows]
        dialog = ComparisonDialog(self.data_df, track_ids, self)
        dialog.exec()

    def find_unique_tracks(self):
        if self.anomaly_detector.model is None:
            QMessageBox.warning(self, "Model Error", "Anomaly detection model is not loaded. Please run 'python src/Main/Model.py' to train it.")
            return

        anomalous_tracks = self.anomaly_detector.find_anomalies(self.data_df, n=10)

        if anomalous_tracks is not None:
            self.unique_tracks_table.setRowCount(len(anomalous_tracks))
            for i, row in enumerate(anomalous_tracks.itertuples()):
                self.unique_tracks_table.setItem(i, 0, QTableWidgetItem(str(row.track_name)))
                self.unique_tracks_table.setItem(i, 1, QTableWidgetItem(str(row.artist_name)))
                self.unique_tracks_table.setItem(i, 2, QTableWidgetItem(f"{row.anomaly_score:.4f}"))

    def set_spotify_ui_enabled(self, enabled):
        self.search_tab.setEnabled(enabled)
        self.user_data_tab.setEnabled(enabled)
        self.top_100_tab.setEnabled(enabled)

    def on_auth_finished(self, auth_info):
        if auth_info and auth_info.get("token"):
            self.set_spotify_ui_enabled(True)
            self.auth_widget.auth_status_label.setText("Authenticated Successfully")
            if auth_info.get("method") == "user_login":
                self.load_initial_user_data()
        else:
            self.set_spotify_ui_enabled(False)
            self.auth_widget.auth_status_label.setText("Authentication Failed")

    def start_worker(self, fn, on_finished, *args, **kwargs):
        worker = Worker(fn, *args, **kwargs)
        worker.finished.connect(on_finished)
        worker.error.connect(self.on_worker_error)
        worker.finished.connect(lambda: self.workers.remove(worker))
        worker.error.connect(lambda: self.workers.remove(worker))
        self.workers.append(worker)
        worker.start()

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

    def search_tracks(self):
        track_name = self.track_name_input.text().strip() or None
        artist = self.artist_input.text().strip() or None
        query = self.query_input.text().strip()
        self.start_worker(self.main_app.session.searchTrack, self.on_search_finished, track=track_name, artist=artist, query=query, limit=20)

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
        selected_button = self.tt_time_range_group.checkedButton()
        time_range = selected_button.time_range if selected_button else "medium_term"
        self.start_worker(self.main_app.data_Retrieval.get_top_tracks, self.on_top_tracks_finished, time_range=time_range)

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
        selected_button = self.ta_time_range_group.checkedButton()
        time_range = selected_button.time_range if selected_button else "medium_term"
        self.start_worker(self.main_app.data_Retrieval.get_top_artists, self.on_top_artists_finished, time_range=time_range)

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
        self.top_100_table.setRowCount(len(results))
        for i, row_data in enumerate(results):
            self.top_100_table.setItem(i, 0, QTableWidgetItem(row_data[0]))
            self.top_100_table.setItem(i, 1, QTableWidgetItem(row_data[1]))
            self.top_100_table.setItem(i, 2, QTableWidgetItem(row_data[2]))
            self.top_100_table.setItem(i, 3, QTableWidgetItem(str(row_data[3])))
        self.update_top_100_button.setEnabled(True)

    def on_worker_error(self, error):
        error_message = f"An error occurred: {error}"
        print(error_message)
        QMessageBox.critical(self, "Application Error", error_message)

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
