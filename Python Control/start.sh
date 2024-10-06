#! /bin/bash

cd ~/Documents/AutoTracker
git pull

while true; do
    python3 main.py
    sleep 1
done
