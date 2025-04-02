# 创建 Conda 环境
conda create -n arduino_music python=3.10

# 激活环境
conda activate arduino_music

# 配置清华 PyPI 镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 pygame
pip install pygame
pip install pyserial