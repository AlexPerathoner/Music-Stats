
import os
import subprocess
import sqlite3
import hashlib
import librosa
import pandas as pd
import pydub
from db import get_meta_data

def get_hash(file_path, level=0):
    def recode_file(file_path):
        print("Recoding file...", file_path)
        p = subprocess.Popen(["ffmpeg", '-i', file_path, '-acodec', 'copy', f"{file_path}.tmp.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.wait()
        os.remove(file_path)
        os.rename(f"{file_path}.tmp.mp3", file_path)

    def load_audio(filepath):
        try:
            y, sr = librosa.load(filepath, mono=False, sr=22050)
            if (y.shape[0] == 2 and len(y[0]) == 0) or (y.shape[0] > 2 and len(y) == 0):
                print(f"Loading {filepath} with explicit duration")
                dur = int(pydub.utils.mediainfo(filepath)["duration"].split(".")[0])
                y, sr = librosa.load(filepath, mono=False, sr=22050, duration=dur)
            return y
        except Exception as e:
            print(f"Error loading audio file {filepath}: {e}")
            return None

    # Load audio files
    print("Loading audio file... " + file_path)
    audio = load_audio(file_path)
    if level < 3:
        if audio is not None:
            bytes_data = audio.tobytes()
            # check if empty
            if len(bytes_data) == 0:
                print("Audio is empty. Trying to recode file.")
                recode_file(file_path)
                return get_hash(file_path, level=level+1)
        else:
            print("Audio is None. Trying to recode file.")
            recode_file(file_path)
            return get_hash(file_path, level=level+1)
    else:
        print("FATAL ERROR. Recoding file did not help.")
        return None
    hash = hashlib.sha256(bytes_data).hexdigest()
    print(hash)
    return hash

def main():
    DB_FILE = 'music-play-count-db.sqlite3'
    meta_data = get_meta_data(DB_FILE)
    df_meta = pd.DataFrame(meta_data, columns=['hash', 'song_name', 'artist_name', 'album_name', 'date_added', 'path', 'present_in_bak', 'present_in_lib', 'song_id', 'last_play_count', 'cloud_status'])
    
    df_meta = df_meta[df_meta['last_play_count'].isna()]
    df_meta = df_meta[df_meta['path'] != '']
    print(df_meta)

    conn = sqlite3.connect(DB_FILE)
    
    c = 0
    tot = len(df_meta)
    for row in df_meta.iterrows():
        c += 1
        path = row[1][5]
        print("%d / %d" % (c, tot))
        print("\tcalculating hash for %s" % path)
        track_hash = get_hash(path)
        if track_hash is None:
            # fatal error, should show alert if happening in script
            continue
        print("\thash: %s" % track_hash)
        conn.execute("UPDATE tracks SET hash = ? WHERE path = ?", (track_hash, path))
        conn.commit()

    print("Closing...")
    conn.close()


if __name__ == "__main__":
    main()
    # print(get_hash('/Users/alex/Music/Musica/Music/Sting/Unknown Album/06 I Burn for You.mp3'))
