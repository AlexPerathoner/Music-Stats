"2d"

import datetime
import sqlite3
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import logging
import seaborn as sns


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE_PLAY_DATA = "music-play-count-db-untouched-plays.sqlite3"
DB_FILE_FIXED = "music-play-count-db-fixed.sqlite3"


def visualize_song_time_series_3d(df, df_tracks_with_last_play_date):
    # Convert date_count to datetime
    df["date_count"] = pd.to_datetime(df["date_count"])

    # order by date to prevent lines from jumping around
    df = df.sort_values(by="date_count")

    # Set up the plot with a larger figure size for better readability
    fig = plt.figure(figsize=(15, 8))

    ax = fig.add_subplot(111, projection="3d")
    # axs[0].set_proj_type('ortho'
    ax.set_proj_type("ortho")
    # set font that supports kanji

    # Use a color palette that provides distinct colors for different series
    color_palette = sns.color_palette("husl", n_colors=len(df["song_id"].unique()))

    # Group the dataframe by song_id, with items ordered by last_play_count
    grouped = df.groupby("song_id")

    z_level = 0
    # Plot each song_id as a separate line
    for (hash, group), color in zip(grouped, color_palette):
        if "song_name" in group.columns:
            song_name = group["song_name"].iloc[0]
        else:
            song_name = group["song_id"].iloc[0]

        dates_num = mdates.date2num(group["date_count"])
        ax.plot(
            dates_num,
            [z_level] * len(group["date_count"]),
            group["count"],
            label=f"{song_name}",
            color=color,
            marker="",
        )
        z_level += 1
    color_palette = sns.color_palette(
        "husl", n_colors=len(df_tracks_with_last_play_date["hash"].unique())
    )

    # Group the dataframe by song_id, with items ordered by last_play_count
    # plot points
    grouped = df_tracks_with_last_play_date.groupby("hash")
    z_level = 0
    for (hash, group), color in zip(grouped, color_palette):
        last_play_count = group["last_play_count"].iloc[-1]
        if last_play_count is 0:
            continue
        raw_value = group["last_play_date"].iloc[-1]
        if raw_value == "missing value":
            continue
        last_play_date = pd.to_datetime(raw_value)
        last_play_date_num = mdates.date2num(last_play_date)
        ax.scatter(
            last_play_date_num,
            z_level,
            last_play_count,
            label=f"{hash[0:9]}",
            color=color,
            marker="o",
            s=100,
        )
        ax.text(last_play_date_num, z_level, last_play_count, hash[0:5])

        logger.debug(f"{hash[0:5]} {last_play_date} {last_play_count}")
        date_added = pd.to_datetime(group["date_added"].iloc[-1])
        date_added_num = mdates.date2num(date_added)
        ax.scatter(
            date_added_num,
            z_level,
            0,
            color=color,
            marker="o",
            s=100,
        )

        ax.text(date_added_num, z_level, 0, hash[0:5])

        z_level += 1

    # Customize the plot
    plt.title("Count by Date for Different Songs", fontsize=16)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Count", fontsize=12)
    plt.rcParams["font.family"] = "Hiragino sans"

    # Set x-axis to show only years
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y%m"))
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
    plt.savefig(filename)

    # Show the plot
    plt.show()


def visualize_song_time_series(df, df_tracks_with_last_play_date):
    # Convert date_count to datetime
    df["date_count"] = pd.to_datetime(df["date_count"])

    # order by date to prevent lines from jumping around
    df = df.sort_values(by="date_count")

    # Set up the plot with a larger figure size for better readability
    plt.figure(figsize=(15, 8))
    # set font that supports kanji

    # Use a color palette that provides distinct colors for different series
    color_palette = sns.color_palette("husl", n_colors=len(df["song_id"].unique()))

    # Group the dataframe by song_id, with items ordered by last_play_count
    grouped = df.groupby("song_id")

    # Plot each song_id as a separate line
    for (hash, group), color in zip(grouped, color_palette):
        song_id = group["song_id"].iloc[0]
        max_count = group["count"].max()
        min_count = group["count"].min()
        # find first date with count > max_count
        first_max_date = group[group["count"] == max_count]["date_count"].min()
        first_date = group["date_count"].min()
        print(f"{song_id} {max_count} {min_count} {first_max_date}")
        plt.plot(
            group["date_count"],
            group["count"],
            label=f"{song_id}",
            color=color,
            marker="",
        )
        plt.annotate(
            f"{song_id}",
            (first_date, min_count),
            xytext=(0, 5),
            textcoords="offset points",
            va="center",
        )

    color_palette = sns.color_palette(
        "husl", n_colors=len(df_tracks_with_last_play_date["hash"].unique())
    )

    # Group the dataframe by song_id, with items ordered by last_play_count
    # plot points
    labels = []
    x = []
    y = []
    grouped = df_tracks_with_last_play_date.groupby("hash")
    for (hash, group), color in zip(grouped, color_palette):
        last_play_count = group["last_play_count"].iloc[-1]
        if last_play_count is 0:
            continue
        raw_value = group["last_play_date"].iloc[-1]
        if raw_value == "missing value":
            continue
        last_play_date = pd.to_datetime(raw_value)
        plt.scatter(
            last_play_date,
            last_play_count,
            label=f"{hash[0:5]}",
            color=color,
            marker="o",
            s=100,
        )
        labels.append(hash[0:5])
        x.append(last_play_date)
        y.append(last_play_count)
        logger.debug(f"{hash[0:5]} {last_play_date} {last_play_count}")
        date_added = pd.to_datetime(group["date_added"].iloc[-1])
        plt.scatter(
            date_added,
            0,
            color=color,
            marker="o",
            s=100,
        )
        labels.append(hash[0:5])
        x.append(date_added)
        y.append(0)

    for i, label in enumerate(labels):
        plt.annotate(
            label, (x[i], y[i]), xytext=(0, 5), textcoords="offset points", va="center"
        )

    # Customize the plot
    plt.title("Count by Date for Different Songs", fontsize=16)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Count", fontsize=12)
    plt.rcParams["font.family"] = "Hiragino sans"

    # Set x-axis to show only years
    number_of_days = len(df["date_count"].unique())
    number_of_ticks = 30
    interval = number_of_days // number_of_ticks
    if interval == 0:
        interval = 1
    # Set x-axis to show only every fifth day
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
    plt.savefig(filename)

    # Show the plot
    plt.show()


def main():
    conn_play_data = sqlite3.connect(DB_FILE_PLAY_DATA)
    conn_play_data_cur = conn_play_data.cursor()

    ## no limit
    MAX_COUNT_UPPER_BOUND = 300
    MAX_COUNT_LOWER_BOUND = 0
    FIRST_DATE_LOWER_BOUND = "2015-10-30"
    FIRST_DATE_UPPER_BOUND = "2024-12-30"
    ##

    MAX_COUNT_UPPER_BOUND = 20
    MAX_COUNT_LOWER_BOUND = 15
    FIRST_DATE_LOWER_BOUND = "2024-04-01"
    # FIRST_DATE_UPPER_BOUND = "2024-12-30"

    USE_3D = False

    conn_play_data_cur.execute(
        f"""select *
            from play_counts
            where song_id in (
            select song_id
            from
            (select song_id, min(count) as min_count, max(COUNT) as max_count, min(date_count) as first_date
            from play_counts
            group by song_id)
            where
                 max_count <= {MAX_COUNT_UPPER_BOUND}
                and max_count >= {MAX_COUNT_LOWER_BOUND}
                and first_date >= "{FIRST_DATE_LOWER_BOUND}"
                and first_date <= "{FIRST_DATE_UPPER_BOUND}"
            )
        """
    )
    df_play_data = pd.DataFrame(
        conn_play_data_cur.fetchall(),
        columns=["song_id", "count", "date_count"],
    )

    song_ids_to_ignore = []

    logger.info(
        f"Length of df before filtering out ignored song ids: {len(df_play_data)}"
    )
    df_play_data = df_play_data[~df_play_data["song_id"].isin(song_ids_to_ignore)]
    logger.info(
        f"Length of df after filtering out ignored song ids: {len(df_play_data)}"
    )

    print(df_play_data)

    conn_fixed = sqlite3.connect(DB_FILE_FIXED)
    conn_fixed_cur = conn_fixed.cursor()

    conn_fixed_cur.execute(
        f"""
        select tracks.hash, song_name, date_added, last_play_count, last_play_date
        from
        tracks left join
        (select hash, count(*) coun
        from play_counts
        group by hash) as c on tracks.hash = c.hash
        where coun is null
        and date_added >= '{FIRST_DATE_LOWER_BOUND}'
        and last_play_count <= {MAX_COUNT_UPPER_BOUND}
        and last_play_count >= {MAX_COUNT_LOWER_BOUND}
        and last_play_date <= '{FIRST_DATE_UPPER_BOUND}'
        order by last_play_count desc limit 10;"""
    )
    df_tracks_with_last_play_date = pd.DataFrame(
        conn_fixed_cur.fetchall(),
        columns=[
            "hash",
            "song_name",
            "date_added",
            "last_play_count",
            "last_play_date",
        ],
    )

    if USE_3D:
        visualize_song_time_series_3d(df_play_data, df_tracks_with_last_play_date)
    else:
        visualize_song_time_series(df_play_data, df_tracks_with_last_play_date)

    logger.info("Closing")
    conn_fixed.close()
    conn_play_data.close()


if __name__ == "__main__":
    logging.getLogger("matplotlib.font_manager").disabled = True
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # or any other level
    logger.addHandler(ch)
    fh = logging.FileHandler("out.log")
    fh.setLevel(logging.DEBUG)  # or any level you want
    logger.addHandler(fh)
    main()
