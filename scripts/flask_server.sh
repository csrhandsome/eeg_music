# http://<树莓派的IP地址>:<端口号>/visualization/arduino_visualization.html
source $HOME/anaconda3/etc/profile.d/conda.sh
conda activate eeg_music
python3 -m eeg_music.example.example_flask_server