-- From TablePlus 2024.12.28
-- old-db.sqlite3
--
--
--
--
--
--
select
    *
from
    play_counts
where
    date_count = "2024-06-21"
    and count > 240;

insert into
    play_counts (song_id, date_count, count)
values
    (4379, "2024-06-21", 242);

delete from play_counts
where
    date_count = "2021-07-19";

select
    *
from
    tracks
where
    song_id in (7393, 7417);

select
    *
from
    play_counts
where
    date_count = "2024-11-24"
    and COUNT >= 220;

select
    *
from
    play_counts
where
    song_id = 8143
order by
    count desc;

delete from play_counts
where
    date_count = "2023-01-09";

select
    c.*,
    tracks.date_added
from
    (
        SELECT
            *
        FROM
            play_counts
        where
            date_count < "2024-03-22"
            and song_id in (
                8143,
                10233,
                5145,
                7641,
                7833,
                8037,
                8041,
                8045,
                8075,
                8189,
                8251,
                8499,
                9321,
                9477
            )
    ) as c
    join tracks on c.song_id = tracks.song_id;

-- get possible matches
select
    *
from
    (
        select
            song_id,
            min(count) as min_count,
            max(COUNT) as max_count,
            min(date_count) as first_date
        from
            play_counts
        group by
            song_id
    )
where
    max_count <= 28
    and first_date >= "2024-04-26"
order by
    max_count desc;

-- get all play counts of possible matches to visualize with python
select
    *
from
    play_counts
where
    song_id in (
        select
            song_id
        from
            (
                select
                    song_id,
                    min(count) as min_count,
                    max(COUNT) as max_count,
                    min(date_count) as first_date
                from
                    play_counts
                group by
                    song_id
            )
        where
            max_count <= 28
            and first_date >= "2024-04-26"
    );

-- find how many songs are still missing to get matched
select
    count(DISTINCT song_id)
from
    play_counts;

delete from play_counts
where
    song_id = 5145
    and date_count <= "2021-05-04";

select
    count(*)
from
    play_counts;