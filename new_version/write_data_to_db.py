
# read output_as_meta.csv and write to database
import pandas as pd
import sqlite3
import os

META_FILE = 'output_as_meta.txt' # csv format
COUNT_FILE = 'output_as_count.txt' # csv format
DB_FILE = 'music-play-count-db.sqlite3'
DB_INIT_FILE = 'init.sql'

def db_empty():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    conn.close()
    return len(tables) == 0

def init_db():
    conn = sqlite3.connect(DB_FILE)
    with open(DB_INIT_FILE, 'r') as f:
        conn.executescript(f.read())
    conn.close()
    print("Database initialized")

def add_meta_data():
    meta = pd.read_csv(META_FILE, sep=';', encoding='utf-16', header=None)
    meta.columns = ['song_id', 'song_name', 'artist_name', 'album_name', 'date_added', 'test']
    # remove test column - no idea why present - shouldn't be there
    meta = meta.drop('test', axis=1)
    print("Found %d tracks" % len(meta))

    # print row with values in test column
    # print(meta[meta['test'].notnull()])

    # insert meta data to database
    conn = sqlite3.connect(DB_FILE)
    for row in meta.iterrows():
        conn.execute("INSERT OR REPLACE INTO tracks (song_id, song_name, artist_name, album_name, date_added) VALUES (?, ?, ?, ?, ?)", (row[1]['song_id'], row[1]['song_name'], row[1]['artist_name'], row[1]['album_name'], row[1]['date_added']))

    conn.commit()
    conn.close()
    
    print("Meta data written to database")

def add_count_data():
    count = pd.read_csv(COUNT_FILE, sep=';', encoding='utf-16', header=None)
    count.columns = ['song_id', 'count']
    print("Found %d counts" % len(count))

    # add column "date_count" with current date
    count['date_count'] = pd.to_datetime('today').date()
    print("Date: ", count['date_count'].iloc[0])

    # insert count data to database
    conn = sqlite3.connect(DB_FILE)
    # insert new values, should be an update if song_id and date_count already exists
    for row in count.iterrows():
        date_string = row[1]['date_count'].strftime('%Y-%m-%d')
        conn.execute("INSERT OR REPLACE INTO play_counts (song_id, count, date_count) VALUES (?, ?, ?)", (row[1]['song_id'], row[1]['count'], date_string))
        conn.commit()
    
    conn.close()


    print("Count data written to database")


if __name__ == '__main__':
    if not os.path.exists(DB_FILE) or db_empty():
        init_db()
    add_meta_data()
    add_count_data()