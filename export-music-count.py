# execute applescript to get path of each song and play count. add to db.

import os
import datetime
import subprocess
import sqlite3
import pandas as pd
from hash import get_hash

DB_FILE = "music-play-count-db.sqlite3"


def get_all_songs_from_apple_music(output_path):

    if os.path.exists(output_path):
        print("Removing old tmp output file...")
        os.remove(output_path)

    print("Running automator...")
    date_start = datetime.datetime.now()
    p = subprocess.Popen(
        ["automator", "/Users/alex/AppsMine/music-stats/exportMeta.workflow"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p.wait()
    date_end = datetime.datetime.now()
    print("Finished running automator in " + str(date_end - date_start) + " s.")
    if p.returncode != 0:
        print(p.stderr.read().decode())
        raise Exception("Automator returned with error code %d" % p.returncode)

    if not os.path.exists(output_path):
        raise Exception("Output path does not exist. Automator failed?")

    print("Converting to dataframe...")
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

    return df


def add_to_db(df):
    # add to db tracks
    print("Adding to db...")
    conn = sqlite3.connect(DB_FILE)
    for row in df.iterrows():
        track_hash = row[1][8]
        last_play_count = row[1][6]
        cloud_status = row[1][7]
        print(track_hash, last_play_count, cloud_status)
        conn.execute(
            "update tracks set last_play_count = ?, cloud_status = ? where hash = ?",
            (last_play_count, cloud_status, track_hash),
        )
        conn.commit()
    conn.close()


def export_hashes_and_counts_to_csv():
    output_path = r"/Users/alex/AppsMine/music-stats/count-data-while-fixing/temp/play_count_export.txt"
    # create necessary folders
    if not os.path.exists("count-data-while-fixing"):
        os.makedirs("count-data-while-fixing")
        os.makedirs("count-data-while-fixing/temp")

    df = get_all_songs_from_apple_music(output_path)
    print("Retrieved %d songs" % len(df))

    # calculating hash
    print("Calculating hash...")
    start_time = datetime.datetime.now()
    # df['hash'] = df.apply(lambda row: get_hash(row['track_path']), axis=1) # do this in a loop
    i = 0
    tot = len(df)
    for row in df.iterrows():
        track_path = row[1][5]
        track_hash = get_hash(track_path)
        df.loc[row[0], "hash"] = track_hash
        i += 1
        print("%d / %d" % (i, tot))

    print(
        "Finished calculating hash in "
        + str(datetime.datetime.now() - start_time)
        + " s."
    )
    # hash is None
    df_filtered_no_hash = df[df["hash"].isna()]
    print("Found %d songs with no hash" % len(df_filtered_no_hash))
    print(df_filtered_no_hash)

    # export to csv - only in debug
    print("Exporting to csv...")
    todays_date = datetime.date.today().strftime("%Y-%m-%d")
    df.to_csv(
        "count-data-while-fixing/play-count-export" + todays_date + ".csv", index=False
    )


def main():
    export_hashes_and_counts_to_csv()
    # todo think more about what data to include - update workflow, remove second workflow if necessary. test it
    # todo also clean db from debug columns
    # todo meta data should be updated each time. Track name, path etc etc. Only hash should be signicant right?
    # todo add more metadata: favorite, comment, skipped count, date, year, favorited, disliked


if __name__ == "__main__":
    main()
