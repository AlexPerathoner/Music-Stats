from utils.errors import (
    TrackHashNotFoundError,
    InsertTrackError,
    UpdateTrackError,
)
from utils.warnings import (
    CloudStatusChangedWarning,
    PathChangedWarning,
)

### used in main daemon


def is_row_in_db(logger, hash_track, date_from_path, new_play_count, cur):
    sql_str = f"""
        select count
        from play_counts
        where hash = '{hash_track}' and date_count = '{date_from_path}' and count = {new_play_count}
    """
    logger.debug(sql_str)
    cur.execute(sql_str)
    result = cur.fetchall()
    return len(result) > 0


def update_song_in_db(logger, track, cur):
    # date added ignored - can't change in time
    song_name = track["song_name"]
    artist_name = track["artist_name"]
    album_name = track["album_name"]
    track_path = track["track_path"]
    duration = track["duration"]
    cloud_status = track["cloud_status"]
    is_favorited = track["is_favorited"]
    hash_track = track["hash"]
    # first check if the hash is present in db
    sql_str = f"""
        select hash, cloud_status, path
        from tracks
        where hash = '{hash_track}'
    """
    cur.execute(sql_str)
    result = cur.fetchall()
    if len(result) == 0:
        raise TrackHashNotFoundError(f"Hash {hash_track} not found in db")

    cur.execute(
        "update tracks set song_name = ?, artist_name = ?, album_name = ?, path = ?, duration = ?, cloud_status = ?, is_favorited = ? where hash = ?;",
        (
            song_name,
            artist_name,
            album_name,
            track_path,
            duration,
            cloud_status,
            is_favorited,
            hash_track,
        ),
    )
    if cur.rowcount == 0 or cur.rowcount > 1:
        raise UpdateTrackError(f"Could not update track {hash_track}")

    old_cloud_status = result[0][1]
    if old_cloud_status != cloud_status:
        logger.error(
            f"Cloud status changed for {hash_track} from {old_cloud_status} to {cloud_status}"
        )
        raise CloudStatusChangedWarning(f"Cloud status changed for {hash_track}")
    old_track_path = result[0][2]
    if old_track_path != track_path:
        logger.error(
            f"Path changed for {hash_track} from {old_track_path} to {track_path}"
        )
        raise PathChangedWarning(f"Path changed for {hash_track}")


def insert_song_into_db(track, cur):
    song_name = track["song_name"]
    artist_name = track["artist_name"]
    album_name = track["album_name"]
    date_added = track["date_added"]
    track_path = track["track_path"]
    duration = track["duration"]
    cloud_status = track["cloud_status"]
    hash_track = track["hash"]
    is_favorite = track["is_favorite"]

    insert_sql_str = f"insert into tracks (song_name, artist_name, album_name, date_added, path, duration, cloud_status, hash, is_favorite) values ('{song_name}', '{artist_name}', '{album_name}', '{date_added}', '{track_path}', '{duration}', '{cloud_status}', '{hash_track}', '{is_favorite}');"
    cur.execute(insert_sql_str)
    if cur.rowcount == 0 or cur.rowcount > 1:
        raise InsertTrackError(f"Could not insert track {hash_track}")


### used in checks

import sqlite3


def get_count_data_for_ids(db_file, ids):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    sql_str = """
        select c.*, tracks.last_play_count, tracks.song_name
        from (
        SELECT * FROM
            play_counts
        
            """
    if ids != []:
        sql_str += "where song_id in " + str(ids).replace("[", "(").replace("]", ")")
        sql_str += " or hash is null"
    sql_str += """
        ) as c
        left JOIN tracks ON c.hash = tracks.hash
        """
    c.execute(sql_str)
    rows = c.fetchall()
    conn.close()
    return rows


def get_count_data_for_ids_from_backup(db_file, ids):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    sql_str = """
    select c.*, tracks.date_added, tracks.song_name
    from (
        SELECT * FROM
            play_counts
            """
    if len(ids) > 0:
        sql_str += " where song_id in " + str(ids).replace("[", "(").replace("]", ")")
    sql_str += """
        ) as c join tracks on c.song_id = tracks.song_id
        """
    c.execute(sql_str)
    rows = c.fetchall()
    conn.close()
    return rows


def get_count_data_for_ids_from_backup_raw(db_file, ids):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    sql_str = """
        SELECT * FROM
            play_counts
            """
    if len(ids) > 0:
        sql_str += " where song_id in " + str(ids).replace("[", "(").replace("]", ")")
    c.execute(sql_str)
    rows = c.fetchall()
    conn.close()
    return rows


def get_count_data(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT * FROM play_counts")
    rows = c.fetchall()
    conn.close()
    return rows


def get_meta_data(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT * FROM tracks")
    rows = c.fetchall()
    conn.close()
    return rows


def build_data(count_data, meta_data):
    data = {}
    for row in meta_data:
        data[row[0]] = {
            "song_name": row[1],
            "artist_name": row[2],
            "album_name": row[3],
            "date_added": row[4],
            "count": {},
        }

    for row in count_data:
        song_id = row[0]
        count = row[1]
        date_count = row[2]
        data[song_id]["count"][date_count] = count
    return data
