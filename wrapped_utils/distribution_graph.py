import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


def plot_distribution(
    data, bins="auto", title="Distribution Curve", xlabel="Value", ylabel="Frequency"
):
    """
    Creates a distribution plot with a kernel density estimation curve.

    Args:
        data (list or numpy.array): List of numerical values
        bins (int or str): Number of bins for histogram or 'auto' for automatic selection
        title (str): Title of the plot
        xlabel (str): Label for x-axis
        ylabel (str): Label for y-axis

    Returns:
        tuple: Figure and axes objects from matplotlib
    """
    # Convert to numpy array if needed
    data = np.array(data)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot histogram
    counts, bins, _ = ax.hist(
        data, bins=bins, density=True, alpha=0.6, color="skyblue", label="Histogram"
    )

    # Calculate KDE (Kernel Density Estimation)
    kde = stats.gaussian_kde(data)
    x_range = np.linspace(min(data), max(data), 200)
    ax.plot(x_range, kde(x_range), "r-", lw=2, label="KDE")

    # Add mean and median lines
    mean = np.mean(data)
    median = np.median(data)
    ax.axvline(
        mean, color="green", linestyle="--", alpha=0.8, label=f"Mean: {mean:.2f}"
    )
    ax.axvline(
        median, color="orange", linestyle="--", alpha=0.8, label=f"Median: {median:.2f}"
    )

    # Add statistical information
    stats_text = f"n: {len(data)}\n"
    stats_text += f"Mean: {mean:.2f}\n"
    stats_text += f"Median: {median:.2f}\n"
    stats_text += f"Std Dev: {np.std(data):.2f}"
    ax.text(
        0.95,
        0.95,
        stats_text,
        transform=ax.transAxes,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    # Customize plot
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig, ax


def create_distribution_graph(df, time_listened_seconds, path):
    df = df.sort_values(by="time_listened", ascending=False)
    tot = len(df)
    plt.figure(figsize=(12, 6))
    plot_data = []
    for i in range(tot):
        top_songs_by_time = df.head(i + 1)
        time_perc = (
            top_songs_by_time["time_listened"].sum() / time_listened_seconds * 100
        )
        plot_data.append(time_perc)

    plt.plot(range(tot), plot_data)
    plt.fill_between(range(tot), plot_data, color="blue", alpha=0.2)
    plt.xticks(range(0, tot, 100))
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.title("Percentage of Time Listened by Top Songs")
    plt.ylabel("Percentage of Total Listening Time")
    plt.xlabel("Top Songs")
    plt.savefig(path)
