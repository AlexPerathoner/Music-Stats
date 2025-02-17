import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from wrapped_utils.distribution_graph import plot_distribution


def create_distribution_plot(durations, path):
    data = [row[0] for row in durations]
    data = np.array(data)
    # filter out data over 1000 seconds
    data = data[data < 1000]

    # Create the distribution plot
    fig, ax = plot_distribution(
        data,
        bins=30,
        title="Duration Distribution",
        xlabel="Duration (seconds)",
        ylabel="Density",
    )
    plt.savefig(path)


def create_duration_distribution_plot(cur, start_date, end_date, path):
    cur.execute(
        f"select duration from tracks where date_added >= '{start_date}' and date_added <= '{end_date}';"
    )
    create_distribution_plot(cur.fetchall(), path)

    # cur.execute(
    #     f"select duration from tracks where date_added < '{start_date}';",
    # )
    # create_distribution_plot(
    #     cur.fetchall(),
    # )


def get_top_songs(cur, start_date, end_date, count):
    """get hashes of most played songs whose date added is in interval"""
    df = cur.execute(
        f"""
        select p.hash, max_count
        from
        (   select hash, max(count) as max_count
            from play_counts
            group by hash
        ) p left JOIN tracks ON p.hash = tracks.hash
        where date_added >= "{start_date}" and date_added <= "{end_date}"
        order by max_count desc
        """
    ).fetchall()
    return pd.DataFrame(
        df,
        columns=["hash", "max_count"],
    ).head(count)


def create_all_plays_plot(cur, start_date, end_date, path):
    cur.execute(
        f"""
        select p.*, t.song_name, t.date_added
        from play_counts p
        left join tracks t on p.hash = t.hash
        where p.hash in (select hash
        from tracks
        where date_added <= "{end_date}"
        and date_added >= "{start_date}")
        """
    )
    rows = cur.fetchall()
    df = pd.DataFrame(
        rows, columns=["hash", "count", "date_count", "song_name", "date_added"]
    )
    # calculate for all rows difference between date_count - date_added
    df["date_count"] = pd.to_datetime(df["date_count"])

    top_songs = get_top_songs(cur, start_date, end_date, 5)["hash"].to_list()

    plt.figure(figsize=(12, 6))
    unique_hashes = df["hash"].unique()
    colors = sns.color_palette("husl", n_colors=len(unique_hashes))

    for hash_id, color in zip(unique_hashes, colors):
        mask = df["hash"] == hash_id
        subset = df[mask]
        song_name = subset["song_name"].iloc[0]
        label = None
        if hash_id in top_songs:
            label = song_name
        plt.plot(
            subset["date_count"],
            subset["count"],
            linestyle="-",  # Connect points with lines
            color=color,
            alpha=0.7,  # Some transparency
            label=label,
        )

    plt.xlabel("Days After Song Was Added To Library")
    plt.ylabel("Play Count")
    plt.title("Play Count Evolution Over Time")
    plt.grid(True, alpha=0.3)

    # If there are too many hashes, you might want to limit the legend
    if len(unique_hashes) > 10:
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", title="Songs")

    plt.tight_layout()
    plt.savefig(path)


def create_plays_after_added_plot(cur, start_date, end_date, path):
    cur.execute(
        f"""
        select p.*, t.song_name, t.date_added
        from play_counts p
        left join tracks t on p.hash = t.hash
        where p.hash in (select hash
        from tracks
        where date_added <= "{end_date}"
        and date_added >= "{start_date}")
        """
    )
    rows = cur.fetchall()
    df = pd.DataFrame(
        rows, columns=["hash", "count", "date_count", "song_name", "date_added"]
    )
    # calculate for all rows difference between date_count - date_added
    df["date_count"] = pd.to_datetime(df["date_count"])
    df["date_added"] = pd.to_datetime(df["date_added"])
    df["days_after_added"] = (
        df["date_count"] - df["date_added"]
    ).dt.total_seconds() / (24 * 60 * 60)

    top_songs = get_top_songs(cur, start_date, end_date, 5)["hash"].to_list()

    plt.figure(figsize=(12, 6))
    unique_hashes = df["hash"].unique()
    colors = sns.color_palette("husl", n_colors=len(unique_hashes))

    for hash_id, color in zip(unique_hashes, colors):
        mask = df["hash"] == hash_id
        subset = df[mask]
        song_name = subset["song_name"].iloc[0]
        label = None
        if hash_id in top_songs:
            label = song_name
        plt.plot(
            subset["days_after_added"],
            subset["count"],
            linestyle="-",  # Connect points with lines
            color=color,
            alpha=0.7,  # Some transparency
            label=label,
        )

    plt.xlabel("Days After Song Was Added To Library")
    plt.ylabel("Play Count")
    plt.title("Play Count Evolution Over Time")
    plt.grid(True, alpha=0.3)

    # If there are too many hashes, you might want to limit the legend
    if len(unique_hashes) > 10:
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", title="Songs")

    plt.tight_layout()
    plt.savefig(path)


def create_trends_stats(cur, start_date, end_date):
    create_duration_distribution_plot(
        cur, start_date, end_date, f"out/distribution_{start_date}_{end_date}.png"
    )
    create_plays_after_added_plot(
        cur, start_date, end_date, f"out/evolution_{start_date}_{end_date}.png"
    )
    create_all_plays_plot(
        cur, start_date, end_date, f"out/all_plays_{start_date}_{end_date}.png"
    )
