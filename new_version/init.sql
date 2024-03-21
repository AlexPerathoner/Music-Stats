-- sqlite3

CREATE TABLE IF NOT EXISTS tracks (
	song_id INT NOT NULL,
	song_name text NOT NULL,
	artist_name text,
	album_name text,
    PRIMARY KEY (song_id)
);

CREATE TABLE IF NOT EXISTS play_counts (
	song_id INT NOT NULL,
	count number NOT NULL,
	date_count date NOT NULL,
	PRIMARY KEY (song_id, date_count),
	FOREIGN KEY (song_id) REFERENCES tracks (song_id)
);

PRAGMA foreign_keys = ON;
