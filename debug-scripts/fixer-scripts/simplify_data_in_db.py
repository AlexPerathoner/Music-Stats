import sqlite3
import pandas as pd
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE_FIXED = "music-play-count-db.sqlite3"


def main():
    conn = sqlite3.connect(DB_FILE_FIXED)
    cur = conn.cursor()

    sql_str = """
        select * from play_counts"""
    logger.info(sql_str)
    cur.execute(sql_str)
    df_play_data = pd.DataFrame(
        cur.fetchall(),
        columns=["hash", "count", "date_count", "song_id"],
    )
    logger.info(df_play_data)

    hashes = df_play_data["hash"].unique()
    tot = len(hashes)
    c = 0
    for hash in hashes:
        logger.info(f"Hash: {hash}. {c} / {tot}")
        df_filtered = df_play_data[df_play_data["hash"] == hash]
        df_filtered = df_filtered.sort_values(by="date_count", ascending=True)
        for i in range(len(df_filtered)):
            if i == 0:
                continue
            if i == len(df_filtered) - 1:
                break
            next_count = df_filtered["count"].iloc[i + 1]
            prev_count = df_filtered["count"].iloc[i - 1]
            curr_count = df_filtered["count"].iloc[i]
            if next_count == curr_count and curr_count == prev_count:
                logger.info(
                    f"Deleting {hash} {df_filtered['count'].iloc[i]} {df_filtered['date_count'].iloc[i]}"
                )
                delete_sql_str = f"delete from play_counts where song_id = {df_filtered['song_id'].iloc[i]} and date_count = '{df_filtered['date_count'].iloc[i]}' and count = {curr_count} and hash = '{hash}';"
                cur.execute(delete_sql_str)
                conn.commit()

        c += 1

    logger.info("Closing")
    conn.close()


if __name__ == "__main__":
    logging.getLogger("matplotlib.font_manager").disabled = True
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # or any other level
    logger.addHandler(ch)
    fh = logging.FileHandler("out.log")
    fh.setLevel(logging.DEBUG)  # or any level you want
    logger.addHandler(fh)
    main()
