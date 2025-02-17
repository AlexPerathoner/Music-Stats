#!/bin/zsh

cd /Users/alex/AppsMine/music-stats/

source env/bin/activate;
python3.12 checks/checks.py # 3.12.8 is the version of python in the env
