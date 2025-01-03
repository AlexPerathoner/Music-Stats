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
    print(sql_str)
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
    print(sql_str)
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
    print(sql_str)
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
