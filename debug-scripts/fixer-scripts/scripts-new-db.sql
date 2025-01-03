-- From TablePlus 2024.12.28
-- fixed-db.sqlite3
--
--
--
--
--
--
CREATE TABLE
    play_counts (
        "hash" text DEFAULT NULL,
        count number NOT NULL,
        date_count date NOT NULL,
        PRIMARY KEY (hash, date_count),
        FOREIGN KEY (hash) REFERENCES tracks (hash)
    );

delete from play_counts;

select
    c.*,
    tracks.last_play_count,
    tracks.song_name
from
    (
        SELECT
            *
        FROM
            play_counts
    ) as c
    left JOIN tracks ON c.hash = tracks.hash;

select
    *
from
    play_counts
where
    date_count = "2024-11-24"
    and COUNT >= 220;

-- get all songs that have 0 play count entries
select
    tracks.hash,
    song_name,
    date_added,
    last_play_count,
    last_play_date
from
    tracks
    left join (
        select
            hash,
            count(*) coun
        from
            play_counts
        group by
            hash
    ) as c on tracks.hash = c.hash
where
    coun is null
order by
    last_play_count desc;

-- find songs added in 2024
select
    *
from
    tracks
where
    date_added like "2024%";

-- find possible matches
select
    *
from
    (
        select
            song_id,
            min(count) as min_count,
            max(COUNT) as max_count,
            min(date_count) as first_date,
            max(date_count) as max_date
        from
            play_counts
        group by
            song_id
    )
where
    max_count > 0
    and first_date > "2024"
order by
    max_count desc;

-- find songs with plays before date added (result: none)
select
    p.*,
    t.date_added
from
    (
        select
            hash,
            song_id,
            min(count) as min_count,
            max(COUNT) as max_count,
            min(date_count) as first_date,
            max(date_count) as max_date
        from
            play_counts
        group by
            hash
    ) as p
    left join tracks t on p.hash = t.hash
where
    first_date < date_added
    and date_added != "2020-11-20"
order by
    first_date asc;

select
    tracks.hash,
    song_name,
    date_added,
    last_play_count,
    last_play_date
from
    tracks
    left join (
        select
            hash,
            count(*) coun
        from
            play_counts
        group by
            hash
    ) as c on tracks.hash = c.hash
where
    coun is null
    and date_added > '2024-01-01'
order by
    last_play_count desc
limit
    10;

-- try to find series match
select
    *
from
    play_counts
where
    date_count = "2024-11-16"
    and COUNT = 28;

-- find by hash start
select
    *
from
    tracks
where
    hash like "02fc%";

select
    hash,
    date_added,
    last_play_count,
    last_play_date
from
    tracks
    left join;

select
    *
from
    play_counts;

where
select
    hash,
    min(date_count) as min_date,
    max(count) as max_count,
    max(count) -1 as max_count_minus_one
from
    play_counts
group by
    hash;

select
    t.hash,
    min_date,
    tracks.date_added
from
    (
        select
            hash,
            min(date_count) as min_date
        from
            play_counts
        group by
            hash
    ) as t
    left join tracks on tracks.hash = t.hash
where
    date_added != "2020-11-20";

select
    count(*)
from
    play_counts;

delete from play_counts
where
    hash = "7737dad376cf522fac91543dc3240f146ab0fdeef17fa5211deccf37646a11d5"
    and count < 23;

select
    play_counts.hash,
    song_id,
    count,
    date_count,
    date_added,
    last_play_date,
    last_play_count
from
    play_counts
    left join tracks on tracks.hash = play_counts.hash
where
    play_counts.hash = "c509c499546d720dbe5c8eae323cbb8cabe6a0876c7451bb83b1d22c1f2f2aa8";