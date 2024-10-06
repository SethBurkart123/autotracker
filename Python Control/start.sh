#! /bin/bash

cd ~/Documents/AutoTracker/Python\ Control
git pull

#source venv/bin/activate

while true; do
    python3 main.py
    sleep 1
done
