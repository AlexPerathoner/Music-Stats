"""
1. make connection to db
2. run
select * from
(select song_id, min(count) as min_count, max(COUNT) as max_count, min(date_count) as first_date, max(date_count) as max_date
from play_counts
group by song_id)
where
max_date = "2024-04-02";	
order by max_count desc;

3. get all song_ids: select * from play_counts where song_id in (...)

4. for each, insert into old db and delete from current one

"""

import sqlite3
import pandas as pd
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

DB_FILE_PLAY_DATA = "music-play-count-db-untouched-plays.sqlite3"
DB_FILE_FIXED = "music-play-count-db-fixed.sqlite3"


def main():

    conn_fixed = sqlite3.connect(DB_FILE_FIXED)
    conn_fixed_cur = conn_fixed.cursor()
    conn_play_data = sqlite3.connect(DB_FILE_PLAY_DATA)
    conn_play_data_cur = conn_play_data.cursor()

    sql_str = """
        select * from
        (select song_id, min(count) as min_count, max(COUNT) as max_count, min(date_count) as first_date, max(date_count) as max_date
        from play_counts
        group by song_id)
        where
        max_date = "2024-04-02";"""
    logger.info(sql_str)

    try:
        conn_fixed_cur.execute(sql_str)
        rows = conn_fixed_cur.fetchall()
        song_ids = [row[0] for row in rows]
        song_ids_str = [str(id) for id in song_ids]
        sql_str = f"""
            select * from play_counts where song_id in ({','.join(song_ids_str)})
            """
        logger.info(sql_str)
        conn_fixed_cur.execute(sql_str)
        df = pd.DataFrame(
            conn_fixed_cur.fetchall(),
            columns=["hash", "count", "date_count", "song_id"],
        )
        logger.info(f"df: {df}")
        for row in df.itertuples():
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
