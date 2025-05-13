#!/bin/bash
source $HOME/anaconda3/etc/profile.d/conda.sh
conda activate eeg_music
python -m eeg_music.example.example_play --arduino-port /dev/ttyUSB0 --mindwave-port /dev/ttyACM0 -i violin