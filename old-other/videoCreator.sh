#!/usr/bin/env bash

rm chart.mp4
ffmpeg -framerate 4 -pattern_type glob -i 'charts/chart/*.png' -c:v libx264 -pix_fmt yuv420p chart.mp4

rm topSongs.mp4
ffmpeg -framerate 3 -pattern_type glob -i 'charts/topSongs/*.png' -c:v libx264 -pix_fmt yuv420p topSongs.mp4