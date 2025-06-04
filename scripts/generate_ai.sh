# http://<树莓派的IP地址>:<端口号>/visualization/arduino_visualization.html
source $HOME/anaconda3/etc/profile.d/conda.sh
conda activate eeg_music
python -m eeg_music.reader.DeepseekReader --prompt "创作一首快乐的小曲子" --save