"""Script that should run in background each day to insert new play counts into db
"""

import datetime
import sqlite3
import pandas as pd
import logging
import sys
from utils.csv import export_hashes_and_counts_to_csv
from utils.applescript import (
    display_error_notification,
    display_warning_notification,
    display_finish_notification,
)
from utils.db import (
    is_row_in_db,
    update_song_in_db,
    insert_song_into_db,
    get_paths_set_in_db,
)
from utils.errors import (
    TrackHashNotFoundError,
    PlayCountDecreasedError,
    InsertPlayCountError,
    UpdatePlayCountError,
    InsertTrackError,
    HashNotGeneratedError,
    UpdateTrackError,
)
from utils.warnings import (
    CloudStatusChangedWarning,
    PathChangedWarning,
    SongWasUnfavoritedWarning,
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE = "music-play-count-db.sqlite3"


def import_csv_into_db(csv_file_path, insert_date):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("select hash from tracks")
    tracks_in_db_list = pd.DataFrame(
        cur.fetchall(),
        columns=["hash"],
    )["hash"].tolist()

    logger.info(f"Importing {csv_file_path}")
    tracks_csv_df = pd.read_csv(csv_file_path)
    cur.execute(
        f"""
        select hash, max(count) as max_count
        from play_counts
        group by hash
        """
    )
    play_count_data_in_db_df = pd.DataFrame(
        cur.fetchall(),
        columns=["hash", "max_count"],
    )

    different_songs_updates_counter = 0
    plays_updates_counter = 0
    new_songs_counter = 0
    errors = []
    warnings = []
    conn.set_trace_callback(logger.debug)
    for index, track in tracks_csv_df.iterrows():
        hash_track = track["hash"]
        new_play_count = track["play_count"]
        old_max_play_count = 0
        max_counts_for_current_hash_df = play_count_data_in_db_df[
            play_count_data_in_db_df["hash"] == hash_track
        ]
        if len(max_counts_for_current_hash_df) == 0:
            if hash_track in tracks_in_db_list:
                logger.info(f"Song has no play data yet {hash_track}")
            else:
                logger.info(f"Song not found in db: {hash_track}. Adding...")
                try:
                    insert_song_into_db(track, cur, logger)
                    new_songs_counter += 1
                except sqlite3.IntegrityError as e:
                    logger.error(f"Integrity error while inserting {hash_track}: {e}")
                    errors.append(f"Integrity error while inserting {hash_track}: {e}")
                    # todo find out how often this happens. consider removing 0.01s from file and re-encoding it
                    continue
                except Exception as e:
                    logger.error(f"Exception while inserting {hash_track}: {e}")
                    errors.append(f"Exception while inserting {hash_track}: {e}")
                    continue
        elif len(max_counts_for_current_hash_df) > 1:
            logger.error(f"Multiple rows for {hash_track}. Should not be possible.")

        try:
            update_song_in_db(logger, track, cur)
        except TrackHashNotFoundError as e:
            logger.error(f"Track hash not found in db for {hash_track}: {e}")
            errors.append(f"Track hash not found in db for {hash_track}: {e}")
            continue
        except CloudStatusChangedWarning as e:
            logger.warning(f"Cloud status changed for {hash_track}: {e}")
            warnings.append(f"Cloud status changed for {hash_track}: {e}")
        except PathChangedWarning as e:
            logger.warning(f"Path changed for {hash_track}: {e}")
            warnings.append(f"Path changed for {hash_track}: {e}")
        except SongWasUnfavoritedWarning as e:
            # could happen, but is weird - prob Apple Music messing up things
            logger.warning(f"Song was unfavorited for {hash_track}: {e}")
            warnings.append(f"Song was unfavorited for {hash_track}: {e}")
        except Exception as e:
            # probably a connection error, insert play data anyway, meta data should be updated on next run
            logger.error(f"Exception while updating {hash_track}: {e}")
            errors.append(f"Exception while updating {hash_track}: {e}")

        # for songs that were just added, there is no max_count in db yet. skip this part
        if len(max_counts_for_current_hash_df) != 0:
            # for songs that were already in db, there is a max_count in db. use that
            old_max_play_count = max_counts_for_current_hash_df["max_count"].values[0]
            if (
                old_max_play_count == new_play_count
            ):  # play count didn't change since last run, skipping song
                continue

            if old_max_play_count > new_play_count:
                logger.error(
                    f"Song {hash_track} with play count {new_play_count} is lower than previous play count {old_max_play_count}"
                )
                errors.append(
                    f"Song {hash_track} with play count {new_play_count} is lower than previous play count {old_max_play_count}"
                )
                # is probably swapping tracks, exit immediately. high prio error
                raise PlayCountDecreasedError(
                    f"Song {hash_track} with play count {new_play_count} is lower than previous play count {old_max_play_count}"
                )
        try:
            # check if row already exists
            if is_row_in_db(hash_track, insert_date, cur):
                logger.debug(f"Row already in db {hash_track}. Updating...")
                # this can happen if running as daemon, too
                # e.g. when running at least 2 times on the same day and both times the count increased
                # just update the count
                cur.execute(
                    "update play_counts set count = ? where hash = ? and date_count = ?;",
                    (new_play_count, hash_track, insert_date),
                )
                if cur.rowcount == 0 or cur.rowcount > 1:
                    raise UpdatePlayCountError(
                        f"Could not update play count for {hash_track}"
                    )
            else:
                logger.debug(
                    f"Inserting... {hash_track}, old play count: {old_max_play_count}, new: {new_play_count} on {insert_date}"
                )
                cur.execute(
                    "insert into play_counts (count, date_count, hash) values (?, ?, ?);",
                    (new_play_count, insert_date, hash_track),
                )
                if cur.rowcount == 0 or cur.rowcount > 1:
                    raise InsertPlayCountError(
                        f"Could not insert play count for {hash_track}"
                    )
        except sqlite3.IntegrityError as e:
            logger.error(
                f"Integrity error while inserting count data for {hash_track}: {e}"
            )
            errors.append(
                f"Integrity error while inserting count data for {hash_track}: {e}"
            )
        except Exception as e:
            logger.error(
                f"Exception while inserting count data for {hash_track} {type(e)}: {e}"
            )
            errors.append(
                f"Exception while inserting count data for {hash_track} {type(e)}: {e}"
            )

        different_songs_updates_counter += 1
        plays_updates_counter += (new_play_count - old_max_play_count)

    logger.info(f"Made {different_songs_updates_counter} updates.")

    conn.set_trace_callback(None)
    logger.info("Committing and closing")
    conn.commit()
    conn.close()

    return different_songs_updates_counter, plays_updates_counter, errors, warnings


def main():
    CSV_FILE_PATH = "temp/play_count_export.csv"
    try:
        start_time = datetime.datetime.now()
        paths_set = get_paths_set_in_db(logger, DB_FILE)
        logger.info(f"Found {len(paths_set)} paths in db.")
        export_hashes_and_counts_to_csv(logger, paths_set, CSV_FILE_PATH)
        end_time = datetime.datetime.now()
        logger.info(f"Exported to csv in {end_time - start_time} s.")

        start_time = datetime.datetime.now()
        todays_date = datetime.date.today().strftime("%Y-%m-%d")
        different_songs_updates_counter, plays_updates_counter, errors, warnings = import_csv_into_db(
            CSV_FILE_PATH, todays_date
        )
        end_time = datetime.datetime.now()
        logger.info(f"Imported to db in {end_time - start_time} s.")

        logger.info(f"Finished with {len(errors)} errors, {len(warnings)} warnings.")
        # first display warnings, then errors -> error notification will land on top
        if len(warnings) > 0:
            logger.warning(f"Warnings: {warnings}")
            display_warning_notification()
        if len(errors) > 0:
            logger.error(f"Errors: {errors}")
            display_error_notification()
        else:
            # showing only if no errors, draw attention to errors if any are present (even non-fatal)
            display_finish_notification(different_songs_updates_counter, plays_updates_counter)
    except (
        PlayCountDecreasedError,
        InsertPlayCountError,
        UpdatePlayCountError,
        InsertTrackError,
        UpdateTrackError,
        HashNotGeneratedError,
    ) as e:
        logger.error(
            f"High prio error happened of type {type(e)}. Exited immediately. {e}"
        )
        display_error_notification()
        sys.exit(1)
    except KeyboardInterrupt as e:
        logger.info("interrupted.")
    except Exception as e:
        logger.error(f"Fatal uncaught error {type(e)}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT = (
        "\n[%(levelname)s/%(name)s:%(lineno)d] %(asctime)s "
        + "(%(processName)s/%(threadName)s)\n> %(message)s"
    )
    FORMATTER = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)
    logging.getLogger("matplotlib.font_manager").disabled = True
    logging.getLogger("numba").setLevel(logging.WARNING)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # CONSOLE level
    ch.setFormatter(FORMATTER)
    logger.addHandler(ch)
    fh = logging.FileHandler(
        "logs/main-script-"
        + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        + ".log"
    )
    fh.setLevel(logging.DEBUG)  # FILE level
    fh.setFormatter(FORMATTER)
    logger.addHandler(fh)
    main()
