import datetime
import sqlite3
import pandas as pd
from numpy import isnan
import matplotlib.pyplot as plt
from utils import parse_date, date_to_str
from db import get_count_data, get_meta_data
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE_PLAY_DATA = "music-play-count-db-untouched-plays.sqlite3"
DB_FILE_FIXED = "music-play-count-db-fixed.sqlite3"


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


ids_to_view = []


def check_last_play_count_plausible(df_songs, df_play_data, song_ids_to_ignore=[]):
    logger.info("Checking last play count plausible")
    errors = 0
    diffs = []
    for index, row in df_songs.iterrows():
        hash = row["hash"]
        song_id = row["song_id"]
        if song_id in song_ids_to_ignore:
            continue
        last_play_count = row["last_play_count"]  # current play count in Music app
        max_play_count = df_play_data[df_play_data["song_id"] == song_id][
            "count"
        ].max()  # max play count in db
        if last_play_count < max_play_count:
            logger.error(
                f"Last play count for hash {hash} and song_id {int(song_id)} is lower ({last_play_count}) than max play count ({max_play_count})"
            )
            if int(song_id) not in ids_to_view:
                ids_to_view.append(int(song_id))
            errors += 1
        diff = last_play_count - max_play_count
        if diff < 0:
            logger.error(f"Diff is negative {diff} for song_id {song_id}")
        diffs.append(diff)
    return diffs


def check_play_count_increase_plausible(df_songs, df_play_data, song_ids_to_ignore):
    logger.info("Checking play count increase plausible")
    # checking if each play_count for each song_id is higher than the previous one
    errors = 0
    for index, row in df_songs.iterrows():
        hash = row["hash"]
        song_id = row["song_id"]
        if song_id in song_ids_to_ignore:
            continue
        counts = df_play_data[df_play_data["song_id"] == song_id].sort_values(
            by="date_count", ascending=True
        )["count"]
        if len(counts) == 0:
            continue
        last_c = counts.iloc[0]
        i = 1
        for c in counts[1:]:
            if c < last_c:
                curr_date = df_play_data[df_play_data["song_id"] == song_id][
                    "date_count"
                ].iloc[i]
                logger.error(
                    f"Play count decreased for hash {hash} and song_id {int(song_id)} from {last_c} to {c} at {curr_date}"
                )
                if int(song_id) not in ids_to_view:
                    ids_to_view.append(int(song_id))
                errors += 1
            last_c = c
            i += 1

    return errors


def check_date_added_plausible(df_songs, df_play_data, song_ids_to_ignore):
    logger.info("Checking date added plausible")
    errors = 0
    # todo check if there are play_counts with play_date < date_added
    for index, row in df_songs.iterrows():
        hash = row["hash"]
        song_id = row["song_id"]
        if song_id in song_ids_to_ignore:
            continue
        date_added = row["date_added"]
        if date_added == "2020-11-20":  # library initialization
            continue
        first_play_date = df_play_data[df_play_data["song_id"] == song_id][
            "date_count"
        ].min()
        if date_added > str(first_play_date):
            logger.error(
                f"Song {hash} with song_id {int(song_id)} has been played before ({first_play_date}) than date added ({date_added})"
            )
            if int(song_id) not in ids_to_view:
                ids_to_view.append(int(song_id))
            errors += 1
    return errors


def check_play_count_plausible(df_songs, df_play_data, song_ids_to_ignore):
    errors = check_last_play_count_plausible(df_songs, df_play_data, song_ids_to_ignore)
    errors += check_play_count_increase_plausible(
        df_songs, df_play_data, song_ids_to_ignore
    )
    errors += check_date_added_plausible(df_songs, df_play_data, song_ids_to_ignore)
    logger.warning(f"Found {errors} errors")


def visualize_diffs_frequency(df_songs, df_play_data):
    diffs = check_last_play_count_plausible(df_songs, df_play_data)
    # count number each value in diffs appears
    freq = pd.Series(diffs).value_counts()

    plt.figure(figsize=(15, 8))
    plt.title("Frequency of play count differences", fontsize=16)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Count", fontsize=12)

    for index, row in freq.iteritems():
        print(index, row)
        plt.scatter(index, row, color="blue", marker="o", s=100)

    plt.show()


def get_mapping(mapping_map, value):
    if isnan(value):
        return None
    if value in mapping_map:
        return mapping_map[value]
    else:
        return None


def main():

    conn_fixed = sqlite3.connect(DB_FILE_FIXED)
    conn_fixed_cur = conn_fixed.cursor()
    conn_play_data = sqlite3.connect(DB_FILE_PLAY_DATA)
    conn_play_data_cur = conn_play_data.cursor()

    # check which tracks are in csv but not in db
    output_path = r"/Users/alex/AppsMine/music-stats/count-data-while-fixing/temp/play_count_export.txt"
    with open(output_path, "r", encoding="utf-16") as f:
        # read txt file
        lines = f.readlines()
        tracks = [line.strip() for line in lines]
        if len(tracks) == 0:
            raise Exception("No tracks found")
        tracks = [track.split(";") for track in tracks]
        df = pd.DataFrame(
            tracks,
            columns=[
                "song_id",
                "song_name",
                "artist_name",
                "album_name",
                "date_added",
                "track_path",
                "play_count",
                "cloud_status",
                "",
            ],
        )
        df = df[df["song_id"] != "\n"]
        df = df.drop(
            df.columns[-1], axis=1
        )  # removing last empty column (artifact of having ; at the end of the line)

    conn_fixed_cur.execute("select * from tracks")
    df_tracks = pd.DataFrame(
        conn_fixed_cur.fetchall(),
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
            "last_play_date",
        ],
    )

    print("Length csv: ", len(df))
    print("Length db: ", len(df_tracks))

    for index, row in df.iterrows():
        track_path = row["track_path"]
        if track_path not in df_tracks["path"].values:
            print(f"track_path {track_path} not found in db")

    exit(1)

    meta_data = get_meta_data(DB_FILE_PLAY_DATA)
    df_tracks = pd.DataFrame(
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
            "song_id",
            "last_play_count",
            "cloud_status",
        ],
    )
    hash_to_id_mapping = df_tracks.set_index("hash")["song_id"].to_dict()
    id_to_hash_mapping = df_tracks.set_index("song_id")["hash"].to_dict()

    meta_data = get_meta_data(DB_FILE_FIXED)
    df_tracks = pd.DataFrame(
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
            "last_play_date",
        ],
    )

    # add columns song_id
    df_tracks["song_id"] = df_tracks["hash"].apply(lambda x: hash_to_id_mapping[x])

    print(df_tracks)
    # conn_play_data_cur.execute(
    #     "select * from play_counts"  # where date_count >= '2024-03-22'"
    # )
    # df_play_data = pd.DataFrame(
    #     conn_play_data_cur.fetchall(),
    #     columns=["song_id", "count", "date_count"],
    # )
    conn_fixed_cur.execute("select * from play_counts")
    df_play_data = pd.DataFrame(
        conn_fixed_cur.fetchall(),
        columns=["hash", "count", "date_count", "song_id"],
    )
    visualize_diffs_frequency(df_tracks, df_play_data)

    exit(0)

    merge_with_pre_2024_play_count_data = False
    if merge_with_pre_2024_play_count_data:
        conn_fixed_cur.execute("select * from play_counts")
        df_play_data_fixed = pd.DataFrame(
            conn_fixed_cur.fetchall(),
            columns=["hash", "count", "date_count", "song_id"],
        )
        df_play_data_fixed = df_play_data_fixed.drop(columns=["hash"])
        # append data from df_play_data_fixed to df_play_data
        df_play_data = df_play_data.append(df_play_data_fixed)

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

    # check_play_count_plausible(
    #     df_tracks, df_play_data, song_ids_to_ignore
    # )  # already done. skip now and use directly ids_to_ignore

    logger.info(f"Length of df before filtering by song ids: {len(df_play_data)}")
    # filter df_play_data with id 4379
    # df_play_data = df_play_data[
    #     (df_play_data["song_id"] == 4379) | (df_play_data["song_id"] == 4795)
    # ]
    # visualize_song_time_series(df_play_data)
    logger.info("Mapping song_ids to hashes...")
    # apply mapping if song_id is not null
    df_play_data["hash"] = df_play_data["song_id"].apply(
        lambda x: get_mapping(id_to_hash_mapping, x)
    )
    logger.info(f"Length of df before filtering: {len(df_play_data)}")
    df_play_data = df_play_data[df_play_data["hash"].notnull()]
    logger.info(f"Length of df after filtering: {len(df_play_data)}")

    print(df_play_data)

    conn_fixed = sqlite3.connect(DB_FILE_FIXED)
    conn_fixed_cur = conn_fixed.cursor()
    conn_play_data = sqlite3.connect(DB_FILE_PLAY_DATA)
    conn_play_data_cur = conn_play_data.cursor()

    try:
        logger.info("Import play data...")

        logger.info("Importing play data done.")
        c = 0
        tot = len(df_play_data)
        for row in df_play_data.iterrows():
            hash = row[1]["hash"]
            song_id = row[1]["song_id"]
            if song_id in song_ids_to_ignore:
                continue
            count = row[1]["count"]
            date_count = row[1]["date_count"]
            sql_str = f"insert into play_counts (count, date_count, hash, song_id) values ({count}, '{date_count}', '{hash}', {song_id});"
            logger.debug(sql_str)
            conn_fixed_cur.execute(sql_str)
            conn_fixed.commit()

            sql_str_del = f"delete from play_counts where song_id = {song_id} and date_count = '{date_count}' and count = {count};"
            logger.debug(sql_str_del)
            conn_play_data_cur.execute(sql_str_del)
            conn_play_data.commit()

            c += 1
            logger.info(f"Processed {c} / {tot}")

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
    logging.getLogger("matplotlib.font_manager").disabled = True
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # or any other level
    logger.addHandler(ch)
    fh = logging.FileHandler("out.log")
    fh.setLevel(logging.DEBUG)  # or any level you want
    logger.addHandler(fh)
    main()
