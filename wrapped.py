"""Series of functions that generate a series of images / pdf from the data in the last year"""

import sqlite3
import pandas as pd
from wrapped_utils.general_stats import create_general_stats
from wrapped_utils.trends_stats import create_trends_stats
from wrapped_utils.heatmap import create_heatmap

DB_FILE = "music-play-count-db.sqlite3"


def complete_df(df):
    """Adds a data point for all songs that don't have some data on the last day.
    This data should not be present in the db, but is added here to make the plot look nicer.
    """
    max_date = df["date_count"].max()
    last_day_for_each_song_df = df.groupby("hash")["date_count"].max()
    for hash, last_day in last_day_for_each_song_df.items():
        count = df[df["hash"] == hash]["count"].iloc[-1]
        if last_day == max_date:
            continue
        # print(f"Hash: {hash}, last_day: {last_day}, count: {count}")

        # add a row for the last day with same count as last day
        df = pd.concat(
            [df, pd.DataFrame([{"hash": hash, "count": count, "date_count": max_date}])]
        )
    return df


def main():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    start_date = "2024-01-01"
    end_date = "2024-12-31"
    create_general_stats(conn, cur, start_date, end_date)
    create_trends_stats(cur, start_date, end_date)
    create_heatmap(cur, start_date, end_date)

    # todo should do more, especially animations... will do another time... check jira for more
    conn.close()


if __name__ == "__main__":
    DB_FILE = "music-play-count-db.sqlite3"
    main()
