import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import joblib
import os

class AnomalyDetector:
    """
    A detector for identifying unique or anomalous songs based on audio features.

    This class loads a pre-trained Isolation Forest model to predict anomaly
    scores for a given set of songs.
    """
    def __init__(self, model_path='anomaly_model.joblib'):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self._load_model()

    def _load_model(self):
        """Loads the anomaly detection model and scaler from the specified path."""
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                self.model = data['model']
                self.scaler = data['scaler']
                print("Anomaly detection model loaded successfully.")
            except Exception as e:
                print(f"Error loading anomaly model: {e}")
        else:
            print(f"Anomaly model file not found at {self.model_path}. Please train the model first.")

    def find_anomalies(self, audio_features_df, n=10):
        """
        Finds the most anomalous tracks from a DataFrame of audio features.

        Args:
            audio_features_df (pd.DataFrame): DataFrame containing audio features.
            n (int): The number of top anomalies to return.

        Returns:
            pd.DataFrame: A DataFrame of the top n most anomalous tracks, or None.
        """
        if self.model is None:
            print("Anomaly model not loaded. Cannot find anomalies.")
            return None

        # Ensure the columns are in the correct order and drop non-feature columns
        features_to_scale = self.scaler.feature_names_in_
        X = audio_features_df[features_to_scale]
        X_scaled = self.scaler.transform(X)

        # Predict anomaly scores (lower scores are more anomalous)
        scores = self.model.decision_function(X_scaled)
        audio_features_df['anomaly_score'] = scores

        # Get the top n tracks with the lowest scores
        anomalous_tracks = audio_features_df.nsmallest(n, 'anomaly_score')
        return anomalous_tracks

def train_and_save_anomaly_model(csv_path, model_save_path='anomaly_model.joblib'):
    """
    Trains an anomaly detection model and saves it.

    Args:
        csv_path (str): The path to the training data CSV file.
        model_save_path (str): The path to save the trained model to.
    """
    print(f"Starting anomaly model training from {csv_path}...")
    df = pd.read_csv(csv_path)
    df.dropna(inplace=True)

    features = ['danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
    X = df[features]

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train the Isolation Forest model
    model = IsolationForest(n_estimators=100, contamination='auto', random_state=42)
    model.fit(X_scaled)

    print("Model training complete.")

    # Save the model and scaler
    model_payload = {
        'model': model,
        'scaler': scaler
    }
    joblib.dump(model_payload, model_save_path)
    print(f"Anomaly model saved to {model_save_path}")

if __name__ == '__main__':
    """
    This block allows the script to be run directly to train and save the anomaly model.
    """
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'DataBase', 'SpotifyAudioFeaturesApril2019.csv')
    train_and_save_anomaly_model(csv_file_path)
