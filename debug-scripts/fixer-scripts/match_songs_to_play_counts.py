import datetime
import sqlite3
import pandas as pd
from utils import parse_date, date_to_str
from db import get_count_data, get_meta_data
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE_PLAY_DATA = "music-play-count-db-untouched-plays.sqlite3"
DB_FILE_FIXED = "music-play-count-db-fixed.sqlite3"


def get_next_max_count(current_date, df_filtered_general):
    next_date = date_to_str(current_date - datetime.timedelta(days=1))
    next_max_date = df_filtered_general[df_filtered_general["date_count"] <= next_date][
        "date_count"
    ].max()
    df_filtered_by_next_day = df_filtered_general[
        df_filtered_general["date_count"] == next_max_date
    ]
    return df_filtered_by_next_day["count"].max()


def get_sort_counts(df_filtered_by_day):
    return df_filtered_by_day.sort_values(by="count", ascending=False)["count"]


def filter_df_by_date(df, date):
    if isinstance(date, str):
        return df[df["date_count"] == date]
    return df[df["date_count"] == date_to_str(date)]


def calculate_max_date(df):
    return df["date_count"].max()


def deal_with_song_dates(
    df_filtered_general,
    current_date,
    song_hash,
    song_name,
    artist_name,
    date_added,
    last_play_count,
    conn_fixed_cur,
    conn_play_data_cur,
    conn_fixed,
    conn_play_data,
):
    old_count = last_play_count
    old_song_id = 0
    first_loop = True
    insert_sql_str = ""
    conn_fixed_cur.execute(f"select * from play_counts where hash = '{song_hash}'")
    result = conn_fixed_cur.fetchall()
    df_already_in_db = pd.DataFrame(
        result, columns=["hash", "count", "date_count", "song_id"]
    )
    while date_to_str(current_date) >= date_added:
        df_filtered = filter_df_by_date(df_filtered_general, current_date)
        if df_filtered.empty:
            current_date = current_date - datetime.timedelta(days=1)
            continue
        # get last day
        max_date = df_filtered["date_count"].max()
        # max_date = date_to_str(current_date)

        # if max date is before date added, set current date to that (first available date in db) # EDIT: i have no idea what this is for
        # still not sure what it does, but it jumps to the first available date in db so lets keep it
        # i now know why it's there: if there are jumps in data it makes no sense to check each day and we can just jump to the first available date (max date)
        if max_date < date_to_str(current_date):
            logger.info("Setting current date to max date")
            current_date = parse_date(max_date)

        # if we have a row with that date for that song, skip
        df_already_in_db_filtered = filter_df_by_date(df_already_in_db, max_date)
        if not df_already_in_db_filtered.empty:
            logger.debug(f"Date already in db {song_name} {max_date}")
            current_date = current_date - datetime.timedelta(days=1)
            continue

        # get only data of that last day
        df_filtered_by_day = filter_df_by_date(df_filtered, max_date)
        if df_filtered_by_day.empty:
            logger.error(
                f"No date match found {song_name} {artist_name} {date_added} {last_play_count}"
            )
            exit(1)
        # get max count
        sorted_count = get_sort_counts(df_filtered_by_day)
        max_count = sorted_count.iloc[0]
        if len(sorted_count) == 1 or first_loop:
            second_max_count = max_count
        else:
            first_loop = False
            second_max_count = sorted_count.iloc[1]
        # filter by max count
        # here we also take the second possible song id into account and check for song_id, swapping is still possible
        df_filtered_by_day = df_filtered_by_day[
            (df_filtered_by_day["count"] == max_count)
            | (df_filtered_by_day["count"] == second_max_count)
        ]
        # Todo: date added is stil not taken into account
        # check if count is a lot less than lastplaycount, or better: check if next iteration (day before) would create problems
        # todo this is too slow. find other way: prioritize song_id, then count if doesn't make sense.
        next_max_count = get_next_max_count(current_date, df_filtered_general)
        if next_max_count > max_count:
            logger.warning(
                f"warning: next_max_count > max_count {next_max_count} {max_count}"
            )
            current_date = current_date - datetime.timedelta(days=1)
            continue

        if len(df_filtered_by_day) > 1:
            logger.info(
                f"Multiple rows with same count {max_count} {df_filtered_by_day}"
            )
            # check if one has the same song_id as before
            df_filtered_by_day_old_id = df_filtered_by_day[
                df_filtered_by_day["song_id"] == old_song_id
            ]
            if df_filtered_by_day_old_id.empty:
                logger.error(
                    f"No song_id match found {song_name} {artist_name} {date_added} {last_play_count}. Would ask for user input. "
                )
                exit(2)
                # ask input to continue
                song_ids = df_filtered_by_day["song_id"].tolist()
                sql_str = (
                    f"select * from tracks where song_id in ("
                    + ",".join([str(id) for id in song_ids])
                    + ")"
                )
                logger.debug(sql_str)
                conn_play_data_cur.execute(sql_str)
                possible_tracks = conn_play_data_cur.fetchall()
                if len(possible_tracks) == 1:
                    logger.info(f"Found one possible track {possible_tracks[0]}")
                    song_id = possible_tracks[0][0]
                    logger.info(f"Continuing with {song_id}")
                else:
                    logger.info(
                        f"Found {len(possible_tracks)} possible tracks for {song_name} {artist_name} {date_added} {last_play_count}"
                    )
                    logger.info(possible_tracks)
                    input_id = input("Enter song_id to continue: ")
                    song_id = int(input_id)
                    logger.info(f"Continuing with {song_id}")
                    df_filtered_by_day = df_filtered_by_day[
                        df_filtered_by_day["song_id"] == song_id
                    ]
                first_row = df_filtered_by_day.iloc[0]
                song_id = first_row[0]
            else:
                song_id = df_filtered_by_day_old_id["song_id"].iloc[0]

            logger.debug(f"Found one with same old song_id {song_id}")
        else:
            # only one row with that count
            first_row = df_filtered_by_day.iloc[0]
        song_id = first_row[0]
        count = int(first_row[1])
        date_count = max_date

        if count > old_count:
            logger.error(
                f"count got higher {song_name} {artist_name} {current_date} {date_count} {count} {old_count}"
            )
            # exit(1)

        old_song_id = song_id
        old_count = count

        # insert into db
        # todo you're retarded. move this to end of loop and do all at once

        insert_sql_str += f"insert into play_counts (count, date_count, hash, song_id) values ({count}, '{date_count}', '{song_hash}', {song_id});"
        logger.debug(f"Inserted: {count}, '{date_count}', '{song_hash}', {song_id}")
        # remove from play count one
        delete_sql_str = f"delete from play_counts where song_id = {song_id} and date_count = '{date_count}' and count = {count};"
        conn_play_data_cur.execute(delete_sql_str)
        conn_play_data.commit()
        # not necessary to filter general df, since we are already filtering by date at start
        # continue with previous date
        current_date = current_date - datetime.timedelta(days=1)

    conn_fixed_cur.execute(insert_sql_str)
    conn_fixed.commit()


def main():
    logger.info("Importing metadata...")
    meta_data = get_meta_data(DB_FILE_FIXED)
    df_fixed = pd.DataFrame(
        meta_data,
        columns=[
            "hash",
            "song_name",
            "artist_name",
            "album_name",
            "date_added",
            "path",
            "present_in_bak",
            "present_in_lib",
            "last_play_count",
            "cloud_status",
        ],
    )

    df_fixed = df_fixed.sort_values(by="last_play_count", ascending=False)

    conn_fixed = sqlite3.connect(DB_FILE_FIXED)
    conn_fixed_cur = conn_fixed.cursor()
    conn_play_data = sqlite3.connect(DB_FILE_PLAY_DATA)
    conn_play_data_cur = conn_play_data.cursor()

    try:
        c = 0
        for row in df_fixed.iterrows():
            count_data = get_count_data(DB_FILE_PLAY_DATA)
            df = pd.DataFrame(count_data, columns=["song_id", "count", "date_count"])

            song_hash = row[1][0]
            song_name = row[1][1]
            artist_name = row[1][2]
            date_added = row[1][4]
            last_play_count = row[1][8]
            logger.info(
                f"{song_hash} {song_name} {artist_name} {date_added} {last_play_count}"
            )

            # GENERAL FILTERING
            # filter by date added
            df_filtered_general = df[df["date_count"] >= date_added]
            # filter by last_play_count
            df_filtered_general = df_filtered_general[
                df_filtered_general["count"] <= last_play_count
            ]
            if df_filtered_general.empty:
                logger.error(
                    f"No match found {song_name} {artist_name} {date_added} {last_play_count}"
                )
                exit(1)

            # parse date
            current_date = parse_date("2024-11-24")
            deal_with_song_dates(
                df_filtered_general,
                current_date,
                song_hash,
                song_name,
                artist_name,
                date_added,
                last_play_count,
                conn_fixed_cur,
                conn_play_data_cur,
                conn_fixed,
                conn_play_data,
            )
            c += 1
            if c > 2:
                break  # for debug only
    except KeyboardInterrupt as e:
        logger.info("interrupted.")
    except Exception as e:
        logger.error(f"exception {e}")
        raise e
    finally:
        logger.info("Closing")
        conn_fixed.close()
        conn_play_data.close()


if __name__ == "__main__":
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # or any other level
    logger.addHandler(ch)
    fh = logging.FileHandler("out.log")
    fh.setLevel(logging.DEBUG)  # or any level you want
    logger.addHandler(fh)
    main()
