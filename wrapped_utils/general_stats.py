import datetime
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import sys

sys.path.append("..")
from visualize_some_songs import visualize_song_time_series
from wrapped_utils.distribution_graph import plot_distribution


def dataframes_to_excel(dataframes, output_path, sheet_names=None):
    """
    Write multiple DataFrames to an Excel file, each in a separate sheet.

    Args:
        dataframes (list): List of pandas DataFrames
        output_path (str): Path where the Excel file will be saved
        sheet_names (list, optional): List of sheet names. If None, will use Sheet1, Sheet2, etc.

    Returns:
        None
    """
    # Input validation
    if not isinstance(dataframes, list):
        raise ValueError("dataframes must be a list of pandas DataFrames")

    if sheet_names and len(sheet_names) != len(dataframes):
        raise ValueError("Number of sheet names must match number of dataframes")

    # Create default sheet names if none provided
    if sheet_names is None:
        sheet_names = [f"Sheet{i+1}" for i in range(len(dataframes))]

    # Create Excel writer object
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Write each dataframe to a separate sheet
        for df, sheet_name in zip(dataframes, sheet_names):
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def format_seconds(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


def get_last_known_value_df(cur, date):
    """returns a df last known value for each hash before the date"""
    # also filtering by date_added to prevent including songs that were added years after the end date
    # can't filter by start_date because we want to include songs listened to in the interval, maybe which were added before the start date
    cur.execute(
        f"""
        with hash_records AS (
            select p.*
            from play_counts p left join tracks t on p.hash = t.hash
            where t.date_added <= '{date}'
        ),
        latest_before_interval AS (
            SELECT hash, count, date_count
            FROM hash_records h
            WHERE date_count <= '{date}'
            GROUP BY hash
            HAVING date_count = MAX(date_count)
        ),
        values_in_interval AS (
            SELECT *
            FROM hash_records h
            WHERE date_count = '{date}'
        )
        SELECT * FROM (
            SELECT hash, count, date_count FROM latest_before_interval
            UNION ALL
            SELECT hash, count, date_count FROM values_in_interval
            WHERE hash NOT IN (SELECT hash FROM latest_before_interval)
        )
        ORDER BY hash, date_count;
    """
    )
    rows = cur.fetchall()
    # create df with hash, count, date_count
    return pd.DataFrame(rows, columns=["hash", "count", "date_count"])


def get_start_date_hash_to_count_map(df):
    start_date_hash_to_count_map = {}
    hashes = df["hash"].unique()
    for h in hashes:
        start_date_hash_to_count_map[h] = df[df["hash"] == h]["count"].iloc[0]
    return start_date_hash_to_count_map


def get_end_date_hash_to_count_map(df):
    end_date_hash_to_count_map = {}
    hashes = df["hash"].unique()
    for h in hashes:
        end_date_hash_to_count_map[h] = df[df["hash"] == h]["count"].iloc[-1]
    return end_date_hash_to_count_map


def get_meta_from_hashes(conn, cur, df):
    hashes_list_str = str(df["hash"].to_list()).replace("[", "(").replace("]", ")")
    cur.execute(
        f"""
        select hash, song_name, artist_name, album_name, date_added, is_favorited, duration from tracks where hash in {hashes_list_str}
    """
    )
    rows = cur.fetchall()
    res_df = pd.DataFrame(
        rows,
        columns=[
            "hash",
            "song_name",
            "artist_name",
            "album_name",
            "date_added",
            "is_favorited",
            "duration",
        ],
    )

    res_df = pd.merge(df, res_df, on="hash")
    return res_df


def get_songs_added_in_interval(cur, start_date, end_date):
    """list of hashes of songs added in the interval"""
    cur.execute(
        f"""
        select hash
        from tracks
        where date_added >= '{start_date}'
        and date_added <= '{end_date}'
    """
    )
    rows = cur.fetchall()
    return [row[0] for row in rows]


def get_total_listening_time(conn, cur, start_date, end_date):
    # generate a df with hash, count at start_date. If hash is not in df, get the first previous count
    # for each hash, get the last count and calculate the difference

    start_date_hash_to_count_df = get_last_known_value_df(cur, start_date)
    end_date_hash_to_count_df = get_last_known_value_df(cur, end_date)

    songs_added_in_interval = get_songs_added_in_interval(cur, start_date, end_date)
    # create a map with values at start date. if there is no row for that day, get the last known value
    rows = []
    for row in end_date_hash_to_count_df.itertuples():
        track_hash = row.hash
        end_value = row.count
        filtered_df = start_value = start_date_hash_to_count_df[
            start_date_hash_to_count_df["hash"] == track_hash
        ]
        start_value = 0
        if track_hash not in songs_added_in_interval and len(filtered_df) != 0:
            start_value = filtered_df["count"].iloc[0]
        rows.append({"hash": track_hash, "increase": end_value - start_value})
    diff_hash_to_count_df = pd.DataFrame(rows)
    # sort by value desc
    diff_hash_to_count_df = diff_hash_to_count_df.sort_values(
        by="increase", ascending=False
    )
    total_number_of_songs = len(diff_hash_to_count_df)
    # filter by non 0 increase
    diff_hash_to_count_df = diff_hash_to_count_df[
        diff_hash_to_count_df["increase"] != 0
    ]
    listened_songs = len(diff_hash_to_count_df)
    total_increases = diff_hash_to_count_df["increase"].sum()

    res_df = get_meta_from_hashes(conn, cur, diff_hash_to_count_df)
    res_df["time_listened"] = res_df["duration"] * res_df["increase"]
    total_time_listened = res_df["time_listened"].sum()
    # format from seconds to HH:MM:SS
    res_df["time_listened_str"] = res_df["time_listened"].apply(
        lambda x: format_seconds(x)
    )

    # change order of columns: increase should be last
    res_df = res_df[
        [
            "hash",
            "song_name",
            "artist_name",
            "album_name",
            "date_added",
            "is_favorited",
            "increase",
            "duration",
            "time_listened",
            "time_listened_str",
        ]
    ]
    return (
        total_number_of_songs,
        listened_songs,
        total_time_listened,
        total_increases,
        res_df,
    )


def calculate_top_albums(listening_time_df):
    df = (
        listening_time_df[["album_name", "increase", "time_listened"]]
        .groupby("album_name")
        .sum()
        .sort_values(by="time_listened", ascending=False)
        .head(15)
    )
    df["time_listened_str"] = df["time_listened"].apply(lambda x: format_seconds(x))
    return df


def calculate_top_artists(listening_time_df):
    df = (
        listening_time_df[["artist_name", "increase", "time_listened"]]
        .groupby("artist_name")
        .sum()
        .sort_values(by="time_listened", ascending=False)
        .head(15)
    )
    df["time_listened_str"] = df["time_listened"].apply(lambda x: format_seconds(x))
    return df


def calculate_top_songs_overall(cur, end_date):
    # todo also create gif with bars changing positions with top songs overall
    df = cur.execute(
        f"""
        select tracks.song_name, tracks.artist_name, tracks.album_name, max_count, tracks.duration
        from
        (   select hash, max(count) as max_count
            from play_counts
            where date_count <= "{end_date}"
            group by hash
        ) p left JOIN tracks ON p.hash = tracks.hash
        """
    ).fetchall()
    df = pd.DataFrame(
        df,
        columns=[
            "song_name",
            "artist_name",
            "album_name",
            "total plays count",
            "duration",
        ],
    )
    df["time_listened"] = df["duration"] * df["total plays count"]
    df["time_listened_str"] = df["time_listened"].apply(lambda x: format_seconds(x))
    df.sort_values(by="total plays count", ascending=False, inplace=True)
    df = df.drop(columns=["time_listened", "duration"])
    return df.head(15)


def get_new_artists_count(cur, start_date, end_date):
    return cur.execute(  # todo including genres here could be interesting
        f"""
        select count(distinct artist_name) from tracks
        where date_added >= "{start_date}" and date_added <= "{end_date}"
        and artist_name not in (
            select artist_name
            from tracks
            where date_added > "{end_date}" and date_added < "{start_date}"
            and artist_name not null
        )
        """
    ).fetchone()[0]


def get_new_songs_count(cur, start_date, end_date):
    return cur.execute(
        f"""
        select count(*) from tracks
        where date_added >= "{start_date}" and date_added <= "{end_date}"
        """
    ).fetchone()[0]


def create_general_stats(conn, cur, start_date, end_date):
    print(f"GENERAL STATS FOR {start_date} - {end_date}")
    (
        total_number_of_songs,
        listened_songs,
        time_listened_seconds,
        total_increases,
        listening_time_df,
    ) = get_total_listening_time(conn, cur, start_date, end_date)
    print(
        f"You listened to {listened_songs} unique songs, for a total of {total_increases} times."
    )
    print(
        f"There are {total_number_of_songs} total songs in your library, so you listened to ({round(listened_songs/total_number_of_songs*100, 2)}% of them)."
    )
    new_songs_count = get_new_songs_count(cur, start_date, end_date)
    print(f"You added {new_songs_count} new songs to your library.")
    new_artists_count = get_new_artists_count(cur, start_date, end_date)
    print(f"You added {new_artists_count} new artists to your library.")

    seconds_in_one_year = 365 * 24 * 60 * 60
    print(
        f"Total time listened (HH:mm:ss): {format_seconds(time_listened_seconds)} ({round(time_listened_seconds/seconds_in_one_year*100, 2)}% of a year)"
    )
    print("\nYour top 10 songs by times (play count) listened were:")
    print(
        listening_time_df.sort_values(by="increase", ascending=False).head(10)[
            ["song_name", "artist_name", "increase"]
        ]
    )
    print("\nYour top 10 songs by time listened were:")
    top_songs_by_time = listening_time_df.sort_values(
        by="time_listened", ascending=False
    ).head(10)
    print(top_songs_by_time[["song_name", "artist_name", "time_listened_str"]])
    top_songs_time = top_songs_by_time["time_listened"].sum()
    print(
        f"You listened to this top songs for: {format_seconds(top_songs_time)} ({round(top_songs_time/time_listened_seconds*100, 2)}% of total listening time)"
    )  # todo here create graph that shows number of top songs / perc of total time listened

    ### EXCEL EXPORT
    # dataframes_to_excel(
    #     [listening_time_df], "total_listening_time.xlsx"
    # )  # todo: format as table, at least column width increase

    listening_time_grouped_by_artist_df = calculate_top_artists(listening_time_df)
    print("\nYour top artists by time listened were:")
    print(listening_time_grouped_by_artist_df)

    listening_time_grouped_by_album_df = calculate_top_albums(listening_time_df)
    print("\nYour top albums by time listened were:")
    print(listening_time_grouped_by_album_df)

    top_songs_overall_df = calculate_top_songs_overall(cur, end_date)
    print("\nYour top songs overall were:")
    print(top_songs_overall_df)
