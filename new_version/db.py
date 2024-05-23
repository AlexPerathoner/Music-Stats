
import sqlite3

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
            'song_name': row[1],
            'artist_name': row[2],
            'album_name': row[3],
            'date_added': row[4],
            'count': {}
        }

    for row in count_data:
        song_id = row[0]
        count = row[1]
        date_count = row[2]
        data[song_id]['count'][date_count] = count
    return data