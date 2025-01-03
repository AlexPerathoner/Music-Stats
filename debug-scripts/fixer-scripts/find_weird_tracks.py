"""find tracks whose first play data is a lot later than its added date"""

import sqlite3
import pandas as pd
import logging
import seaborn as sns
from utils import parse_date


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE_PLAY_DATA = "music-play-count-db-untouched-plays.sqlite3"
DB_FILE_FIXED = "music-play-count-db-fixed.sqlite3"


def main():
    conn = sqlite3.connect(DB_FILE_FIXED)
    cur = conn.cursor()

    sql_str = """
        select t.hash, min_date, tracks.date_added, max_count
        from
        (
        select hash, min(date_count) as min_date, max(count) as max_count
        from play_counts
        group by hash
        ) as t left join tracks on tracks.hash = t.hash
        where 
        date_added != "2020-11-20"
        ;"""

    logger.info(sql_str)

    try:
        cur.execute(sql_str)
        df = pd.DataFrame(
            cur.fetchall(),
            columns=[
                "hash",
                "min_date",
                "date_added",
                "max_count",
            ],
        )
        logger.info(f"df: {df}")
        for row in df.itertuples():
            hash = row[1]
            min_date = row[2]
            date_added = row[3]
            max_count = row[4]
            # parse date
            min_date = parse_date(min_date)
            date_added = parse_date(date_added)
            # check if more than 60 days difference
            if (min_date - date_added).days <= 100 and (
                min_date - date_added
            ).days > 50:
                logger.error(
                    f"{hash} {min_date}\t{date_added}\t{max_count}\t{(min_date - date_added).days}"
                )

    finally:
        logger.info("Closing")
        conn.close()


if __name__ == "__main__":
    logging.getLogger("matplotlib.font_manager").disabled = True
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # or any other level
    logger.addHandler(ch)
    fh = logging.FileHandler("out.log")
    fh.setLevel(logging.DEBUG)  # or any level you want
    logger.addHandler(fh)
    main()
