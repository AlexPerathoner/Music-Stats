"""
daily checks to make sure everything is as expected
"""

import logging
import sqlite3
import pandas as pd
from datetime import datetime
import os
import subprocess


def display_notification(title, message, beep_count=1):
    subprocess.run(
        [
            "osascript",
            "-e",
            f'display notification "{message}" with title "{title}"',
        ]
    )
    if beep_count > 0:
        subprocess.run(["osascript", "-e", f"beep {beep_count}"])
        subprocess.run(["afplay", "/System/Library/Sounds/Sosumi.aiff"])


def display_error_check_notification():
    display_notification(
        "Music Stats: ERROR checking data!", "Music Stats: ERROR checking data!", 5
    )


def check_path_exists(path):
    return os.path.exists(path)


def check_paths_exist(cur):
    cur.execute(
        f"""
        select path
        from tracks;
        """
    )
    rows = cur.fetchall()
    df = pd.DataFrame(
        rows,
        columns=["path"],
    )
    # for each, call check_path_exists
    df["exists"] = df["path"].apply(check_path_exists)
    return df[df["exists"] == False]


def get_songs_with_same_hash(cur):
    cur.execute(
        f"""
        select hash, song_name, artist_name, album_name, date_added, is_favorited, duration, path, count(hash) as count
        from tracks
        group by tracks."hash" having count(*) > 1;
        """
    )
    rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=[
            "hash",
            "song_name",
            "artist_name",
            "album_name",
            "date_added",
            "is_favorited",
            "duration",
            "path",
            "count",
        ],
    )


def get_songs_with_same_path(cur):
    cur.execute(
        f"""
        select hash, song_name, artist_name, album_name, date_added, is_favorited, duration, path, count(path) as count
        from tracks
        group by tracks."path" having count(*) > 1;
        """
    )
    rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=[
            "hash",
            "song_name",
            "artist_name",
            "album_name",
            "date_added",
            "is_favorited",
            "duration",
            "path",
            "count",
        ],
    )


def get_songs_with_unknown_status(cur):
    cur.execute(
        f"""
        select hash, song_name, artist_name, album_name, date_added, is_favorited, duration, path
        from tracks
        where cloud_status != 'unknown';
        """
    )
    rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=[
            "hash",
            "song_name",
            "artist_name",
            "album_name",
            "date_added",
            "is_favorited",
            "duration",
            "path",
        ],
    )


def get_play_counts_with_missing_tracks(cur):
    cur.execute(
        f"""
        select hash, count, date_count
        from play_counts
        where hash not in (select hash from tracks);
        """
    )
    rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=["hash", "count", "date_count"],
    )


def get_songs_with_play_data_before_added(cur):
    cur.execute(
        f"""
        select p.*, t.date_added from
            (select hash, min(count) as min_count, max(COUNT) as max_count, min(date_count) as first_date, max(date_count) as max_date
            from play_counts
            group by hash) as p left join tracks t on p.hash = t.hash
        where
        first_date < date_added
        and date_added != "2020-11-20"
        """
    )
    rows = cur.fetchall()
    return pd.DataFrame(
        rows,
        columns=[
            "hash",
            "min_count",
            "max_count",
            "first_date",
            "max_date",
            "date_added",
        ],
    )


def get_songs_inconsistent_increase(cur):
    cur.execute(
        f"""
        select hash, count, date_count
        from play_counts
        """
    )
    rows = cur.fetchall()
    play_data_df = pd.DataFrame(
        rows,
        columns=["hash", "count", "date_count"],
    )
    cur.execute(
        f"""
        select hash
        from tracks
        """
    )
    rows = cur.fetchall()
    tracks_df = pd.DataFrame(
        rows,
        columns=["hash"],
    )
    # for each row in tracks, get all play data for that song (hash)
    failing_hashes = []
    for index, row in tracks_df.iterrows():
        hash = row["hash"]
        filtered_play_data_df = play_data_df[play_data_df["hash"] == hash]
        # sort by date_count
        filtered_play_data_df = filtered_play_data_df.sort_values(
            by="date_count", ascending=True
        )
        # check if play data is monotonically increasing
        if not filtered_play_data_df["count"].is_monotonic_increasing:
            failing_hashes.append(hash)
    return tracks_df[tracks_df["hash"].isin(failing_hashes)]


def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)


def get_latest_plays(cur):
    """Get latest play count for any song. Should not be older than 2 days."""
    # get all play data for song
    cur.execute(
        f"""
        select max(date_count)
from play_counts;
        """
    )
    rows = cur.fetchall()
    play_data_df = pd.DataFrame(
        rows,
        columns=["max_date"],
    )
    max_date = play_data_df["max_date"].values[0]
    # todays date in YYYY-MM-DD format
    today = datetime.now().strftime("%Y-%m-%d")
    # if difference between today and max_date is greater than 2 days, return 0
    return days_between(today, max_date)


def main(logger):
    DB_FILE = "music-play-count-db.sqlite3"
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    errors = 0

    logger.info("Checking if all songs have paths that exist in os...")
    df = check_paths_exist(cur)
    if len(df) > 0:
        logger.error("Found %d songs with missing files" % len(df))
        logger.error(df)
        errors += 1
    logger.info("Checking if multiple songs have same hash...")
    df = get_songs_with_same_hash(cur)
    if len(df) > 0:
        logger.error("Found %d songs with same hash" % len(df))
        logger.error(df)
        errors += 1
    logger.info("Checking if multiple songs have same path...")
    df = get_songs_with_same_path(cur)
    if len(df) > 0:
        logger.warning("Found %d songs with same path" % len(df))
        logger.warning(df)
        errors += 1
    logger.info("Checking if counts for all songs is monotonically increasing...")
    df = get_songs_inconsistent_increase(cur)
    if len(df) > 0:
        logger.error("Found %d songs with inconsistent increase" % len(df))
        logger.error(df)
        errors += 1
    logger.info("Checking if any song has play data before it was added...")
    df = get_songs_with_play_data_before_added(cur)
    if len(df) > 0:
        logger.error("Found %d songs with play data before it was added" % len(df))
        logger.error(df)
        errors += 1
    logger.info("Checking if any song has cloud_status != 'unknown'...")
    df = get_songs_with_unknown_status(cur)
    if len(df) > 0:
        logger.error("Found %d songs with cloud_status != 'unknown'" % len(df))
        logger.error(df)
        errors += 1
    logger.info("Checking if some play count data has hashes that are not in tracks...")
    df = get_play_counts_with_missing_tracks(cur)
    if len(df) > 0:
        logger.error("Found %d play count data with missing tracks" % len(df))
        logger.error(df)
        errors += 1
    days = get_latest_plays(cur)
    logger.info("Last play data is %d days ago" % days)
    if days >= 2:
        logger.error("Last play data is %d days ago" % days)
        errors += 1

    if errors > 0:
        logger.error("Found %d errors" % errors)
        display_error_check_notification()
        exit(1)
    else:
        logger.info("Finished with no errors found.")
        exit(0)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT = (
        "\n[%(levelname)s/%(name)s:%(lineno)d] %(asctime)s "
        + "(%(processName)s/%(threadName)s)\n> %(message)s"
    )
    FORMATTER = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # CONSOLE level
    ch.setFormatter(FORMATTER)
    logger.addHandler(ch)
    fh = logging.FileHandler(
        "logs/checks-script-" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".log"
    )
    fh.setLevel(logging.DEBUG)  # FILE level
    fh.setFormatter(FORMATTER)
    logger.addHandler(fh)
    main(logger)
