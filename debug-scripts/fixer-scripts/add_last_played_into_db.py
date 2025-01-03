"""
from db get songs that have last_played_count > max_count in play data (or no max count at all -> no play data)
for those, insert play date @ last_play_count point into play_counts
"""

import sqlite3
import pandas as pd
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE = "music-play-count-db.sqlite3"


def main():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    sql_str = """
        SELECT *
        from (
        select tracks.hash, max(COUNT) as max_count, tracks.last_play_count, tracks.last_play_date, tracks.date_added
        from tracks left JOIN play_counts ON play_counts.hash = tracks.hash
        group by tracks.hash
        )
        where
        last_play_count > max_count
        or max_count is null;
    """
    cur.execute(sql_str)
    df = pd.DataFrame(
        cur.fetchall(),
        columns=[
            "hash",
            "max_count",
            "last_play_count",
            "last_play_date",
            "date_added",
        ],
    )
    logger.info(f"Number of rows: {len(df)}")

    c = 0
    for index, row in df.iterrows():
        hash = row["hash"]
        max_count = row["max_count"]
        last_play_count = row["last_play_count"]
        last_play_date = row["last_play_date"]
        date_added = row["date_added"]
        logger.info(
            f"\nHash: {hash}, max_count: {max_count}, last_play_count: {last_play_count}, last_play_date: {last_play_date}"
        )

        if last_play_count == 0:
            logger.debug(
                f"last_play_count is 0, inserting {hash} at date_added {date_added}"
            )
            date_to_insert = date_added
        elif last_play_date == "missing value":
            logger.debug(
                f"last play date missing, inserting {hash} at date_added {date_added}"
            )
            date_to_insert = date_added
        else:
            logger.debug(f"inserting {hash} at last_play_date {last_play_date}")
            date_to_insert = last_play_date

        insert_sql_str = f"insert into play_counts (count, date_count, hash) values ({last_play_count}, '{date_to_insert}', '{hash}');"
        logger.debug(insert_sql_str)
        conn.execute(insert_sql_str)
        conn.commit()

    logger.info("Closing")
    conn.close()


if __name__ == "__main__":
    logging.getLogger("matplotlib.font_manager").disabled = True
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # or any other level
    logger.addHandler(ch)
    fh = logging.FileHandler("logs/add_last_played_into_db.log")
    fh.setLevel(logging.DEBUG)  # or any level you want
    logger.addHandler(fh)
    main()
