import datetime
import pandas as pd
from utils import parse_date, date_to_str


DB_FILE_PLAY_DATA = "music-play-count-db-untouched-plays.sqlite3"


def main():
    try:
        count_data = get_count_data(DB_FILE_PLAY_DATA)
        df = pd.DataFrame(count_data, columns=["song_id", "count", "date_count"])

        current_date = parse_date("2024-11-24")
        min_date = df["date_count"].min()
        old_song_count = 99999999
        while date_to_str(current_date) >= min_date:
            song_count = len(df[df["date_count"] == date_to_str(current_date)])
            if song_count != 0:
                print(current_date, song_count)
                if old_song_count < song_count:
                    print(
                        "Less songs in db than on day before!",
                        song_count,
                        old_song_count,
                        date_to_str(current_date),
                    )
                old_song_count = song_count

            current_date = current_date - datetime.timedelta(days=1)
    except KeyboardInterrupt as e:
        print("exception", e)
    finally:
        print("Closing")


if __name__ == "__main__":
    main()
