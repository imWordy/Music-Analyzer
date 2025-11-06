import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

def find_similar_songs(df, seed_track_id, features, n=10):
    """
    Finds the most similar songs to a seed song based on audio features.
    """
    # Scale the features
    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df[features])
    df_scaled = pd.DataFrame(df_scaled, columns=features, index=df.index)

    # Get the vector for the seed track
    seed_vector = df_scaled.loc[df[df['track_id'] == seed_track_id].index]

    # Calculate cosine similarity
    sim_scores = cosine_similarity(seed_vector, df_scaled)
    sim_scores = sim_scores[0]

    # Add scores to the original dataframe and sort
    df['similarity'] = sim_scores
    df_similar = df.sort_values(by='similarity', ascending=False)

    # Exclude the seed track itself and return the top n
    df_similar = df_similar[df_similar['track_id'] != seed_track_id]
    return df_similar.head(n)

def plot_radar_chart(df, track_ids, features):
    """
    Generates a radar chart to compare multiple audio features for up to 3 tracks.
    """
    df_selected = df[df['track_id'].isin(track_ids)]
    track_names = df_selected['track_name'].tolist()

    # Normalize the feature data across the entire dataset for a fair comparison
    df_features = df[features].copy()
    df_normalized = (df_features - df_features.min()) / (df_features.max() - df_features.min())

    # Get the normalized data for the selected tracks
    data = df_normalized.loc[df_selected.index].values

    num_vars = len(features)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for i, (row, track_name) in enumerate(zip(data, track_names)):
        values = np.concatenate((row, row[:1]))
        ax.plot(angles, values, label=track_name, linewidth=2)
        ax.fill(angles, values, alpha=0.25)

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(features, size=12)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.set_title('Song Feature Radar Comparison', size=20, y=1.1)

    return fig

def plot_feature_distribution(df, feature):
    """
    Generates a histogram and density plot for a single audio feature.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df[feature], kde=True, ax=ax, color='skyblue', bins=30)
    mean_val = df[feature].mean()
    ax.axvline(mean_val, color='r', linestyle='--', linewidth=2)
    ax.text(mean_val * 1.1, ax.get_ylim()[1] * 0.9, f'Mean: {mean_val:.2f}', color='r')
    ax.set_title(f'Distribution of {feature.capitalize()}', fontsize=16)
    ax.set_xlabel(feature.capitalize(), fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    fig.tight_layout()
    return fig

def plot_correlation_heatmap(df, features):
    """
    Generates a heatmap of the correlation matrix for the given features.
    """
    corr = df[features].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm', ax=ax)
    ax.set_title('Correlation Matrix of Audio Features', fontsize=16)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    fig.tight_layout()
    return fig

def plot_scatter(df, feature1, feature2):
    """
    Generates a scatter plot to show the. relationship between two features.
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=df, x=feature1, y=feature2, alpha=0.5, ax=ax)
    ax.set_title(f'{feature1.capitalize()} vs. {feature2.capitalize()}', fontsize=16)
    ax.set_xlabel(feature1.capitalize(), fontsize=12)
    ax.set_ylabel(feature2.capitalize(), fontsize=12)
    fig.tight_layout()
    return fig
