#!/bin/bash
source $HOME/anaconda3/etc/profile.d/conda.sh
conda activate eeg_music
python -m eeg_music.example.example_record -p /dev/ttyACM0 -b 57600 -t 1 --name "csr"