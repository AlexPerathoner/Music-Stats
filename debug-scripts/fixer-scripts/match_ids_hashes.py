import sqlite3
import pandas as pd
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE_PLAY_DATA = "music-play-count-db-untouched-plays.sqlite3"
DB_FILE_FIXED = "music-play-count-db-fixed.sqlite3"


def main():
    conn_play_data = sqlite3.connect(DB_FILE_PLAY_DATA)
    conn_play_data_cur = conn_play_data.cursor()

    conn_fixed = sqlite3.connect(DB_FILE_FIXED)
    conn_fixed_cur = conn_fixed.cursor()

    mapping = {  # song_id to hash
        # "10585": "0a6b7",
        # "10613": "74e00",
        # "10573": "acc6c",
        # "10537": "bc8a8",
        # "10455": "0ba7e",
        # "10611": "54b9a",
        # "10621": "670cd",
        # "10429": "deae8",
        # "10417": "0f456",
        # "10457": "a351c",  # day after
        # "10361": "027ce",  # day after
        # "10543": "7024c",  # day after
        # "10677": "17d19",  # day after
        # "10641": "c0103",  # after end
        # "10355": "89601",  # after end
        # "10333": "fc134",  # after end
        # "10393": "02fc6",  # after end # WRONG! Added date doesn't match
        # "10407": "1fc78",  # after end
        # "10347": "b0625",  # after end
        # "10353": "cedd3",  # after end
        # "5145": "200ec",
        "10505": "0006e",
    }
    logger.info(f"Mapping: {mapping}")
    song_ids = list(mapping.keys())
    extended_mapping = {}

    for k, m in mapping.items():
        sql_str = f"""
            select * from tracks where hash like '{m}%'
        """
        logger.info(sql_str)
        conn_fixed_cur.execute(sql_str)
        df_tracks = pd.DataFrame(
            conn_fixed_cur.fetchall(),
            columns=[
                "hash",
                "song_name",
                "artist_name",
                "album_name",
                "date_added",
                "path",
                "present_in_lib",
                "present_in_bak",
                "last_play_count",
                "cloud_status",
                "last_play_date",
            ],
        )
        if len(df_tracks) != 1:
            logger.error(f"Expected 1 row, got {len(df_tracks)}")
            exit(1)
        hash_track = df_tracks["hash"].iloc[0]
        extended_mapping[k] = hash_track

    sql_str = f"""
        select * from play_counts where song_id in ({','.join(song_ids)})
    """
    logger.info(sql_str)
    conn_play_data_cur.execute(sql_str)
    df_play_data = pd.DataFrame(
        conn_play_data_cur.fetchall(),
        columns=["song_id", "count", "date_count"],
    )

    logger.info(extended_mapping)

    try:
        logger.info("Import play data...")

        logger.info("Importing play data done.")
        c = 0
        tot = len(df_play_data)
        for row in df_play_data.iterrows():
            song_id = row[1]["song_id"]
            count = row[1]["count"]
            date_count = row[1]["date_count"]
            hash_track = extended_mapping[str(song_id)]

            sql_str = f"insert into play_counts (count, date_count, hash, song_id) values ({count}, '{date_count}', '{hash_track}', {song_id});"
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
