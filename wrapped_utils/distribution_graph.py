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
