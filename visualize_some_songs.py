import datetime
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from utils import parse_date

DB_FILE = "music-play-count-db.sqlite3"


def visualize_song_time_series(df):
    # Convert date_count to datetime
    df["date_count"] = pd.to_datetime(df["date_count"])

    # order by date to prevent lines from jumping around
    df = df.sort_values(by="date_count")

    # Set up the plot with a larger figure size for better readability
    plt.figure(figsize=(15, 8))
    # set font that supports kanji

    # Use a color palette that provides distinct colors for different series
    color_palette = sns.color_palette("husl", n_colors=len(df["hash"].unique()))

    # Group the dataframe by song_id, with items ordered by last_play_count
    grouped = df.groupby("hash")

    # Plot each song_id as a separate line
    for (hash, group), color in zip(grouped, color_palette):
        song_name = group["hash"].iloc[0][0:5]
        plt.plot(
            group["date_count"],
            group["count"],
            label=f"{song_name}",
            color=color,
            marker="",
            linewidth=0.5,
        )  # Add markers to show individual data points
        # also plot a single point with the last play count
        if "last_play_count" in group.columns and "last_play_date" in group.columns:
            last_play_count = group["last_play_count"].iloc[-1]
            last_play_date_raw = group["last_play_date"].iloc[-1]
            if last_play_date_raw == "missing value":
                continue
            last_play_date = parse_date(last_play_date_raw)
            plt.scatter(
                last_play_date,
                last_play_count,
                color=color,
                marker="o",
                s=10,
            )

        if "date_added" in group.columns:
            date_added = pd.to_datetime(group["date_added"].iloc[-1])
            plt.scatter(
                date_added,
                0,
                color=color,
                marker="o",
                s=10,
            )

    # Customize the plot
    plt.title("Count by Date for Different Songs", fontsize=16)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Count", fontsize=12)
    plt.rcParams["font.family"] = "Hiragino sans"

    # Set x-axis to show only years
    max_date = df["date_count"].max()
    min_date = df["date_count"].min()
    number_of_days = (max_date - min_date).days
    number_of_ticks = 30
    interval = number_of_days // number_of_ticks
    if interval == 0:
        interval = 1

    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=interval))
    plt.xticks(rotation=45)

    plt.grid(True, linestyle="--", alpha=0.7)

    # Add legend with a smaller font and outside the plot to avoid overcrowding
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)

    # Adjust layout to prevent cutting off labels
    plt.tight_layout()

    # save to file with YYYYMMDD-HHMMSS
    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    filename = f"out/plot-{date_str}-{time_str}.png"
    plt.savefig(filename, dpi=300)

    # Show the plot
    plt.show()


if __name__ == "__main__":
    DB_FILE = "music-play-count-db.sqlite3"

    ids = []
    song_ids_to_ignore = [
        8143,
        10233,
        5145,
        7641,
        7833,
        8037,
        8041,
        8045,
        8075,
        8189,
        8251,
        8499,
        9321,
        9477,
    ]

    # count_data = get_count_data_for_ids(DB_FILE, ids)
    # df = pd.DataFrame(
    #     count_data,
    #     columns=[
    #         "song_id",
    #         "count",
    #         "date_count",
    #         "hash",
    #         "last_played_count",
    #         "song_name",
    #     ],
    # )

    # for new db
    # df = pd.DataFrame(
    #     count_data,
    #     columns=[
    #         "hash",
    #         "count",
    #         "date_count",
    #         "song_id",
    #         "last_played_count",
    #         "song_name",
    #     ],
    # )

    # count_data = get_count_data_for_ids_from_backup_raw(DB_FILE, ids)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    hashes = [
        "ff2ce0ef451765215e548d358b48413b6c9d92d4071bdc7cdaa377a678e6e284",
    ]
    sql_str = f"""
        select play_counts.hash, count, date_count, date_added, last_play_date, last_play_count
        from play_counts left join tracks on tracks.hash = play_counts.hash
        """
    # where play_counts.hash in ({','.join([f"'{hash}'" for hash in hashes])})
    # """
    cur.execute(sql_str)
    count_data = cur.fetchall()
    df = pd.DataFrame(
        count_data,
        columns=[
            "hash",
            "count",
            "date_count",
            "date_added",
            "last_play_date",
            "last_play_count",
        ],
    )

    visualize_song_time_series(df)
