# 创建 Conda 环境
source $HOME/anaconda3/etc/profile.d/conda.sh
conda create -n eeg_music python=3.9.21

# 激活环境
conda activate eeg_music

# 配置清华 PyPI 镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 pygame
pip install pygame
pip install pyserial
pip install torcheeg
pip install moabb