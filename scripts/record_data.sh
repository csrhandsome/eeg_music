#!/bin/bash
source $HOME/anaconda3/etc/profile.d/conda.sh
conda activate eeg_music
# csr
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "csr" -d 45 -m "happy"
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "csr" -d 45 -m "sad"
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "csr" -d 45 -m "angry"
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "csr" -d 45 -m "peaceful"

# qc
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "qc" -d 45 -m "happy"
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "qc" -d 45 -m "sad"
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "qc" -d 45 -m "angry"
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "qc" -d 45 -m "peaceful"

# tour
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "tour" -d 45 -m "happy"
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "tour" -d 45 -m "sad"
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "tour" -d 45 -m "angry"
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "tour" -d 45 -m "peaceful"



