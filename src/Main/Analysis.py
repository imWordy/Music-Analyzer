import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plot_single_feature(df, track_ids, feature):
    """
    Generates a simple bar chart comparing a single audio feature between two tracks.

    Args:
        df (pd.DataFrame): The main DataFrame containing all track data.
        track_ids (list): A list containing the two track_ids to compare.
        feature (str): The single audio feature name (column) to plot.

    Returns:
        matplotlib.figure.Figure: The generated plot figure.
    """
    fig, ax = plt.subplots(figsize=(6, 4))

    # Filter for the two selected tracks
    df_selected = df[df['track_id'].isin(track_ids)].set_index('track_id').loc[track_ids]

    if feature not in df_selected.columns:
        ax.text(0.5, 0.5, f'Feature \'{feature}\' not found.', ha='center', va='center')
        return fig

    track_names = df_selected['track_name'].tolist()
    feature_values = df_selected[feature].tolist()

    ax.bar(track_names, feature_values, color=['skyblue', 'lightgreen'])
    ax.set_ylabel(feature.capitalize())
    ax.set_title(f'{feature.capitalize()} Comparison')
    
    # Add value labels on top of bars
    for i, value in enumerate(feature_values):
        ax.text(i, value, f'{value:.2f}', ha='center', va='bottom')

    fig.tight_layout()
    return fig

def plot_feature_comparison(df, track_ids, features_to_compare):
    """
    (This function is no longer used by the main GUI but is kept for potential future use)
    Generates a bar chart comparing audio features for a list of tracks.
    """
    df_selected = df[df['track_id'].isin(track_ids)]

    if df_selected.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No data found for the selected tracks.', ha='center', va='center', transform=ax.transAxes)
        return fig

    track_names_for_plot = df_selected['track_name'].tolist()
    n_tracks = len(df_selected)
    n_features = len(features_to_compare)
    fig, ax = plt.subplots(figsize=(12, 7))
    index = np.arange(n_tracks)
    bar_width = 0.8 / n_features

    for i, feature in enumerate(features_to_compare):
        if feature in df_selected.columns:
            feature_values = df_selected[feature]
            ax.bar(index + i * bar_width, feature_values, bar_width, label=feature)

    ax.set_xlabel('Tracks')
    ax.set_ylabel('Values')
    ax.set_title('Comparison of Audio Features Across Tracks')
    ax.set_xticks(index + bar_width * (n_features - 1) / 2)
    ax.set_xticklabels(track_names_for_plot, rotation=45, ha="right")
    ax.legend()
    fig.tight_layout()
    return fig
