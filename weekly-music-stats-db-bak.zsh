#!/bin/zsh 

cd /Users/alex/AppsMine/music-stats/

mkdir -p backups

# zip db file
zip -r music-play-count-db-bak.zip music-play-count-db.sqlite3
mv music-play-count-db-bak.zip backups/music-play-count-db-bak-$(date +%Y-%m-%d).zip
