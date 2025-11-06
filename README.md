# Music Analyzer

This application is a comprehensive tool for the analysis and exploration of music data, leveraging a dataset of over 130,000 songs from Spotify. It provides several layers of analysis, from high-level data visualization to specific, user-focused models. The application is built using Python with the PySide6 (Qt) framework for the GUI and scikit-learn for the machine learning models.

---

## 1. Machine Learning Models

The application features two primary machine learning models that operate on the core dataset of song audio features.

### 1.1. Anomaly Detection for Unique Song Discovery

-   **What It Is:** This model is designed to identify which songs in the dataset are the most musically unique or "anomalous" compared to the norm.

-   **Model Choice & Justification:** We use the **Isolation Forest** algorithm. This is an unsupervised learning algorithm that is highly effective for anomaly detection. It works by randomly partitioning the data until it isolates each data point. The core idea is that anomalous points are "few and different," and should therefore be easier to isolate. This makes them require fewer partitions, which gives them a lower anomaly score. This method is efficient and performs well on high-dimensional data like our set of audio features, making it a perfect choice.

-   **Methodology:**
    1.  **Feature Selection:** The model is trained on the core audio features: `danceability`, `energy`, `key`, `loudness`, `mode`, `speechiness`, `acousticness`, `instrumentalness`, `liveness`, `valence`, and `tempo`.
    2.  **Preprocessing:** Before training, the features are scaled using `StandardScaler`. This is a critical step that standardizes the features by removing the mean and scaling to unit variance. This ensures that features with larger ranges (like `tempo`) do not disproportionately influence the model over features with smaller ranges (like `danceability`).
    3.  **Training & Prediction:** The Isolation Forest model is trained on the entire scaled dataset. The trained model is then saved to `anomaly_model.joblib` to avoid retraining every time the application starts. When a user requests the "Top 10 Most Unique Tracks," the model calculates an anomaly score for every song. The 10 songs with the lowest scores are presented as the most unique.

### 1.2. "Find Similar" Song Recommender

-   **What It Is:** This is a content-based filtering model that, given a user-selected "seed" song, finds the most musically similar songs from the entire dataset.

-   **Model Choice & Justification:** The model is based on **Cosine Similarity**. This is a metric used to measure the cosine of the angle between two non-zero vectors. In our case, each song is represented as a vector of its audio features. Cosine similarity is an excellent choice here because it measures the *orientation* of the vectors, not their magnitude. This means it focuses on the *proportion* of features in a song, rather than their absolute values. For example, two songs might have very different loudness levels but a similar profile of energy and danceability; cosine similarity will correctly identify them as similar.

-   **Methodology:**
    1.  **Feature Selection:** The same set of core audio features is used.
    2.  **Preprocessing:** As with the anomaly detection model, the features are scaled using `StandardScaler` to ensure each feature contributes equally to the similarity calculation.
    3.  **Similarity Calculation:** When a user selects a seed song and requests similar tracks, the following happens:
        -   The scaled feature vector of the seed song is retrieved.
        -   The cosine similarity is calculated between the seed song's vector and the vectors of all other songs in the dataset.
        -   The songs are then ranked by their similarity score (from highest to lowest), and the top 10 are returned as the recommendations.

---

## 2. Data & API Connectivity

### 2.1. Data Source & Preprocessing

-   **Primary Dataset:** The core of the application is the `SpotifyAudioFeaturesApril2019.csv` file, which contains over 130,000 tracks. This dataset includes the track name, artist name, and a rich set of pre-calculated audio features from Spotify.

-   **API Integration:** The application interacts with two main APIs:
    1.  **Spotify API:** Used for all user-specific data, including authentication, fetching user profiles, top tracks/artists, and recently played songs.
    2.  **Reccobeats API:** A supplementary API used to fetch audio features for tracks that are not in the local CSV file (e.g., for the user's recently played songs).

-   **Authentication:** The application supports two authentication flows:
    1.  **Client Credentials Flow:** Used for public, non-user-specific data. This is handled by the `authenticate` method in `spotifyClient.py`.
    2.  **Authorization Code Flow:** A more complex, user-interactive flow that allows the application to access a user's personal data after they grant permission. This is handled by the `get_auth_url` and `fetch_token_from_url` methods and requires a `redirect_uri` to be configured in your Spotify Developer dashboard.

### 2.2. Data Visualization

The application provides a rich suite of data visualization tools to explore the music dataset, all powered by `matplotlib` and `seaborn`.

-   **Radar Chart:** Found in the "Analysis" tab, this chart is used to compare the audio feature "fingerprints" of 1-3 selected songs. It's an excellent tool for seeing the relative strengths of different features in a song at a glance.

-   **Distribution Plot (Histogram/Density):** Found in the "Data Exploration" tab, this plot shows the frequency distribution of a single selected audio feature across the entire dataset. It helps to understand the overall character of the music library (e.g., "Is most of the music high-energy?").

-   **Correlation Heatmap:** This plot shows the correlation matrix of all audio features. It's a powerful tool for discovering relationships *between* features. For example, the strong positive correlation between `energy` and `loudness` is immediately visible.

-   **Scatter Plot:** This allows for a deep dive into the relationship between any two selected audio features. Each point on the plot is a song, making it easy to spot trends and clusters.
