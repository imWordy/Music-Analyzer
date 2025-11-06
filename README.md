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

---

## 3. Data Visualization & Analysis

The application provides a rich suite of data visualization tools to explore the music dataset. These are found in the "Analysis" and "Data Exploration" tabs.

### 3.1. Radar Chart (Track Comparison)

-   **What It Is:** The radar chart, found in the **Analysis** tab, is the primary tool for comparing the audio feature "fingerprints" of 1 to 3 songs. Each selected song is represented by a colored shape, and each corner of the chart represents a different audio feature. The further a point is from the center, the higher its value for that feature.

-   **How to Use It:** Select one, two, or three songs from the main tracklist in the "Analysis" tab and click the "Compare Selected Tracks" button.

-   **What It Tells You:** This chart is excellent for seeing the relative balance of features in a song. For example:
    -   A song with points skewed towards `danceability`, `energy`, and `valence` will likely be an upbeat, happy dance track.
    -   A song with a high value for `acousticness` and low values for `energy` and `loudness` is likely a mellow, acoustic piece.
    -   Comparing two songs might reveal that while they have similar energy levels, one is much more instrumental than the other.

### 3.2. Distribution Plot (Histogram)

-   **What It Is:** This plot, found in the **Data Exploration** tab, shows the frequency distribution of a single selected audio feature across the entire 130,000+ song dataset. The x-axis represents the value of the feature, and the y-axis shows how many songs have that value.

-   **How to Use It:** Select "Distribution" from the plot type dropdown, choose a feature, and click "Generate Plot."

-   **What It Tells You:** This plot is key to understanding the overall character of the music library. For instance:
    -   A distribution plot for `energy` might show a bi-modal distribution, indicating a large number of both low-energy and high-energy songs, but fewer in the middle.
    -   A plot for `instrumentalness` will likely be heavily skewed towards zero, as most songs contain vocals. The long tail of the distribution represents the purely instrumental tracks.
    -   The red dashed line indicates the *average* value for that feature across the whole dataset, giving you a quick reference point.

### 3.3. Correlation Heatmap

-   **What It Is:** This plot, also in the **Data Exploration** tab, is a powerful tool for discovering the relationships *between* different audio features. It is a grid where each cell shows the correlation coefficient between two features.

-   **How to Use It:** Select "Correlation Heatmap" from the plot type dropdown and click "Generate Plot."

-   **What It Tells You:** The heatmap reveals which features tend to move together:
    -   **Strong Positive Correlation (Bright Red):** A value close to +1.0 means that as one feature increases, the other tends to increase as well. For example, you will see a strong positive correlation between `energy` and `loudness`—energetic songs are almost always loud.
    -   **Strong Negative Correlation (Bright Blue):** A value close to -1.0 means that as one feature increases, the other tends to *decrease*. A classic example is the negative correlation between `acousticness` and `energy`.
    -   **No Correlation (Near Zero/White):** A value near 0 means the two features have little to no linear relationship (e.g., `danceability` and `key`).

### 3.4. Scatter Plot

-   **What It Is:** The scatter plot provides a more granular view of the relationship between any two specific audio features. Each dot on the plot represents a single song from the dataset.

-   **How to Use It:** Select "Scatter Plot" from the dropdown, choose two features you want to compare, and click "Generate Plot."

-   **Interpreting the Plots: Key Combinations**
    -   **`valence` vs. `energy` (The Mood Map):** This is the most famous combination. It maps songs to a four-quadrant emotional space:
        -   *Top-Right (High Valence, High Energy):* Happy, exciting, and energetic music. Think party anthems or upbeat pop.
        -   *Top-Left (High Valence, Low Energy):* Calm, positive, and peaceful music. Think of a lazy Sunday morning or a chill coffee shop.
        -   *Bottom-Left (Low Valence, Low Energy):* Sad, introspective, and melancholic music. This is the quadrant for ballads and ambient soundscapes.
        -   *Bottom-Right (Low Valence, High Energy):* Angry, intense, and chaotic music. Heavy metal and aggressive electronic music live here.

    -   **`acousticness` vs. `energy`:** This plot is excellent for separating produced, electronic music from live, acoustic performances.
        -   You will typically see a strong negative correlation, forming a diagonal line. Songs in the *top-left* (high acousticness, low energy) are likely solo piano or guitar tracks. Songs in the *bottom-right* (low acousticness, high energy) are likely electronic dance music or heavily produced pop.

    -   **`danceability` vs. `energy`:** This helps distinguish between different kinds of high-energy music.
        -   While often positively correlated, there are interesting exceptions. A track in the *top-right* (high danceability, high energy) is a classic club banger. However, a track in the *bottom-right* (low danceability, high energy) might be a fast-paced rock or metal song that is intense but not necessarily easy to dance to.

    -   **`speechiness` vs. `instrumentalness`:** This plot is ideal for identifying vocal-centric vs. instrumental-centric tracks.
        -   You should see two distinct clusters. A cluster in the *top-left* (high speechiness, low instrumentalness) will contain rap, podcasts, and spoken-word tracks. A cluster in the *bottom-right* (low speechiness, high instrumentalness) will contain classical music, ambient, and other instrumental genres. Most other pop/rock songs will be clustered near the bottom-left.

    -   **`loudness` vs. `energy`:** This plot demonstrates one of the strongest linear relationships in audio features. You will see a tight, diagonal line of points, confirming that as songs get more energetic, they almost always get louder. Outliers in this plot could be interesting anomalies.
