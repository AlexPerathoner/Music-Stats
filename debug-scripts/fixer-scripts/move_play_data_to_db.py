import sqlite3
import pandas as pd
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE_PLAY_DATA = "music-play-count-db-untouched-plays.sqlite3"
DB_FILE_FIXED = "music-play-count-db-fixed.sqlite3"


def main():
    # moves play data of given hashes from fixed to old db
    conn_play_data = sqlite3.connect(DB_FILE_PLAY_DATA)
    conn_play_data_cur = conn_play_data.cursor()
    conn_fixed = sqlite3.connect(DB_FILE_FIXED)
    conn_fixed_cur = conn_fixed.cursor()

    hashes_to_move = [
        "02fc6eb13880ef04155ebc039c53dd8f567ec4171226f75be949758dc46b70f2",
    ]

    sql_str = f"""
        select * from play_counts
        where hash in ({','.join([f"'{hash}'" for hash in hashes_to_move])})
        """
    logger.info(sql_str)
    conn_fixed_cur.execute(sql_str)
    df_play_data = pd.DataFrame(
        conn_fixed_cur.fetchall(),
        columns=["hash", "count", "date_count", "song_id"],
    )

    for row in df_play_data.itertuples():
        hash = row[1]
        count = row[2]
        date_count = row[3]
        song_id = row[4]
        logger.debug(f"Inserted: {count}, '{date_count}', {song_id}, {hash}")

        insert_sql_str = f"insert into play_counts (count, date_count, song_id) values ({count}, '{date_count}', {song_id});"
        conn_play_data_cur.execute(insert_sql_str)
        conn_play_data.commit()

        delete_sql_str = f"delete from play_counts where song_id = {song_id} and date_count = '{date_count}' and count = {count} and hash = '{hash}';"
        conn_fixed_cur.execute(delete_sql_str)
        conn_fixed.commit()

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
