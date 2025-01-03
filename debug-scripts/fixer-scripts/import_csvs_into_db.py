"""
read all csv from the last debugging days, for each row add to sqlite3 db.
only adds a row in play_counts if count increased. doesn't modify meta data
"""

import datetime
import sqlite3
import pandas as pd
import logging
from utils import parse_date


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE = "music-play-count-db.sqlite3"


def main():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    csvs_paths = [
        # "count-data-while-fixing/play-count-export2024-12-11.csv",
        # "count-data-while-fixing/play-count-export2024-12-12.csv",
        # "count-data-while-fixing/play-count-export2024-12-13.csv",
        # "count-data-while-fixing/play-count-export2024-12-14.csv",
        # "count-data-while-fixing/play-count-export2024-12-15.csv",
        # "count-data-while-fixing/play-count-export2024-12-17.csv",
        # "count-data-while-fixing/play-count-export2024-12-19.csv",
        # "count-data-while-fixing/play-count-export2024-12-20.csv",
        # "count-data-while-fixing/play-count-export2024-12-24.csv",
        # "count-data-while-fixing/play-count-export2024-12-27.csv",
        "count-data-while-fixing/play-count-export2024-12-28.csv",
        "count-data-while-fixing/play-count-export2024-12-31.csv",
    ]

    cur.execute("select hash from tracks")
    tracks_in_db_list = pd.DataFrame(
        cur.fetchall(),
        columns=["hash"],
    )["hash"].tolist()

    updates_counter = 0
    for csv_file_path in csvs_paths:
        print(f"Importing {csv_file_path}")
        tracks_csv_df = pd.read_csv(csv_file_path)
        date_from_path = csv_file_path.split("play-count-export")[1].split(".csv")[0]
        cur.execute(
            f"""
            select hash, max(count) as max_count
            from play_counts
            where date_count <= '{date_from_path}'
            group by hash
            """
        )
        play_count_data_in_db_df = pd.DataFrame(
            cur.fetchall(),
            columns=["hash", "max_count"],
        )
        for index, track in tracks_csv_df.iterrows():
            hash_track = track["hash"]
            play_count = track["play_count"]
            new_track = False
            filtered_df = play_count_data_in_db_df[
                play_count_data_in_db_df["hash"] == hash_track
            ]
            if len(filtered_df) == 0:
                if hash_track in tracks_in_db_list:
                    logger.info(f"Song has no play data yet {hash_track}")
                    new_track = True
                else:
                    logger.error(f"Song not found in db!! {hash_track}")
                    # todo: should be added before inserting play data (but should NOT happen during this script)
                    continue
            else:
                old_play_count = filtered_df["max_count"].values[0]
                if old_play_count == play_count:
                    continue

            if old_play_count > play_count and not new_track:
                logger.error(
                    f"Song {hash_track} with play count {play_count} is lower than previous play count {old_play_count}"
                )
                continue
            logger.debug(
                f"Inserting... {hash_track}, old play count: {old_play_count}, new: {play_count} on {date_from_path}"
            )
            insert_sql_str = f"insert into play_counts (count, date_count, hash) values ({play_count}, '{date_from_path}', '{hash_track}');"
            try:
                cur.execute(insert_sql_str)
                conn.commit()
            except sqlite3.IntegrityError as e:
                logger.error(f"Integrity error: {e}")
                if "UNIQUE constraint failed: play_counts.hash" in str(e):
                    if old_play_count == play_count:
                        logger.error(
                            "Same count as before, should have skipped already"
                        )
                        continue
                    elif old_play_count < play_count:
                        # e.g. b59592d7a0dbd679bef6ac876eb0e6a0b9893a1d88f98f2301028ad764e5744e	5	2024-12-17
                        # was added since last play date was 12-17 and no data before existed
                        # however, if date added is before 12-16, the existing row should be updated to a day before

                        # select from play count df all rows with hash
                        if len(filtered_df) == 1:
                            # select date added from meta data
                            sql_str = f"""
                                select date_added
                                from tracks
                                where hash = '{hash_track}'
                            """
                            logger.debug(sql_str)
                            cur.execute(sql_str)
                            result = cur.fetchall()
                            df = pd.DataFrame(
                                result,
                                columns=["date_added"],
                            )
                            date_added = parse_date(df["date_added"].values[0])
                            day_before = parse_date(
                                date_from_path
                            ) - datetime.timedelta(days=1)
                            if date_added < day_before:
                                logger.warning(
                                    f"Song was added before day before, updating that row and inserting anyway"
                                )
                                try:
                                    update_sql_str = f"update play_counts set date_count = '{day_before}' where hash = '{hash_track}';"
                                    logger.debug(update_sql_str)
                                    cur.execute(update_sql_str)
                                    conn.commit()
                                    insert_sql_str = f"insert into play_counts (count, date_count, hash) values ({play_count}, '{date_from_path}', '{hash_track}');"
                                    logger.debug(insert_sql_str)
                                    cur.execute(insert_sql_str)
                                    logger.info(
                                        f"{hash_track} updated single row entry to date before and inserted new row."
                                    )
                                    updates_counter += 1
                                    conn.commit()
                                except sqlite3.IntegrityError as e:
                                    logger.error(
                                        f"Integrity error: {e} for {hash_track} and {date_from_path}"
                                    )
                                except Exception as e:
                                    logger.error(f"Exception: {e}")
                            else:
                                logger.error("Not sure what to do")
                                exit(1)
            except Exception as e:
                logger.error(f"Exception: {e}")
            updates_counter += 1

    logger.info(f"Made {updates_counter} updates with {len(csvs_paths)} csvs")
    logger.info("Closing")
    conn.close()


if __name__ == "__main__":
    LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT = (
        "\n[%(levelname)s/%(name)s:%(lineno)d] %(asctime)s "
        + "(%(processName)s/%(threadName)s)\n> %(message)s"
    )
    FORMATTER = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)
    logging.getLogger("matplotlib.font_manager").disabled = True
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # or any other level
    ch.setFormatter(FORMATTER)
    logger.addHandler(ch)
    fh = logging.FileHandler(
        "logs/import_csvs_into_db"
        + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        + ".log"
    )
    fh.setLevel(logging.DEBUG)  # or any level you want
    fh.setFormatter(FORMATTER)
    logger.addHandler(fh)
    main()
