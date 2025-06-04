# EEG音乐生成系统

基于脑电波(EEG)和Arduino传感器数据的实时音乐生成系统。该项目结合了神经科学、音乐理论和嵌入式系统，能够根据用户的脑电活动和物理交互实时生成音乐。

## 🎵 项目特色

- **多模态输入**: 支持脑电波(Mindwave)和Arduino传感器数据
- **实时音乐生成**: 根据传感器数据实时生成不同乐器音色
- **Web可视化**: 提供实时数据可视化界面
- **多种乐器**: 支持钢琴、小提琴、长笛、吉他、小号等音色
- **数据记录**: 支持音乐数据和脑电数据的记录与分析

## 🎬 演示视频

![演示视频](data/img/demo_play.mp4)

*演示视频展示了系统的实时音乐生成效果*

## 🛠️ 系统架构

```
EEG音乐系统
├── 硬件层
│   ├── Mindwave脑电设备 (/dev/ttyACM0)
│   └── Arduino传感器 (/dev/ttyUSB0)
│       ├── 超声波距离传感器
│       ├── 电位器
│       └── RGB LED灯带
├── 数据处理层
│   ├── 脑电信号处理
│   ├── 传感器数据解析
│   └── 音乐参数映射
├── 音频生成层
│   ├── 音符频率计算
│   ├── 乐器音色合成
│   └── 实时音频播放
└── 可视化层
    ├── Web实时显示
    └── 数据记录分析
```

## 📋 系统要求

### 硬件要求
- **脑电设备**: Mindwave Mobile/Mobile 2
- **Arduino开发板**: Arduino Uno/Nano
- **传感器模块**:
  - HC-SR04超声波传感器
  - 滑动电位器
  - 旋转电位器
  - WS2812B RGB LED灯带
  - 按钮开关

### 软件要求
- **操作系统**: Linux (推荐Ubuntu 20.04+)
- **Python**: 3.9+
- **Anaconda**: 用于环境管理

## 🚀 安装指南

### 环境要求
- **Python**: 3.9+ (推荐3.9.21)
- **操作系统**: Linux (推荐), Windows, macOS
- **内存**: 至少4GB RAM
- **存储**: 至少2GB可用空间

### 1. 克隆项目
```bash
git clone <repository-url>
cd eeg_music
```

### 2. 创建Python虚拟环境

#### 方法1：使用Conda (推荐)
```bash
# 创建conda环境
conda create -n eeg_music python=3.9.21
conda activate eeg_music
```

#### 方法2：使用虚拟环境
```bash
# 创建虚拟环境
python3 -m venv eeg_music_env
source eeg_music_env/bin/activate  # Linux/macOS
# 或 Windows: eeg_music_env\Scripts\activate
```

### 3. 安装依赖包

#### 方法1：使用requirements.txt (推荐)
```bash
# 安装所有依赖
pip install -r requirements.txt
```

#### 方法2：手动安装核心依赖
```bash
# 基础音频和串口库
pip install pygame>=2.1.0 pyserial>=3.5 numpy>=1.21.0

# Web服务器组件
pip install Flask==2.3.3 Flask-SocketIO==5.3.6 Flask-CORS==4.0.0
pip install python-socketio==5.8.0 eventlet==0.33.3

# 异步HTTP和WebSocket
pip install aiohttp>=3.8.0 websockets>=10.0

# 机器学习和脑电处理 (可选)
pip install torch>=1.13.0 torcheeg>=1.0.11 moabb>=0.4.6
pip install scikit-learn>=1.1.0 matplotlib>=3.5.0

# 其他工具
pip install tqdm>=4.64.0
```

### 4. 验证安装
```bash
# 检查Python包
python -c "import pygame, serial, flask, numpy; print('核心依赖安装成功!')"

# 检查串口设备 (Linux)
ls /dev/tty*

# 测试音频系统
python -c "import pygame; pygame.mixer.init(); print('音频系统正常!')"
```

### 5. 硬件连接与配置

#### Arduino设置
```bash
# 连接Arduino到USB端口
# 通常会显示为 /dev/ttyUSB0 (Linux) 或 COM3 (Windows)

# 检查Arduino连接
python -m eeg_music.reader.ArduinoSerialReader -l

# 设置设备权限 (Linux)
sudo chmod 666 /dev/ttyUSB0
sudo usermod -a -G dialout $USER  # 添加用户到dialout组
```

#### Mindwave脑电设备设置
```bash
# 连接Mindwave设备
# 通常会显示为 /dev/ttyACM0 (Linux) 或 COM4 (Windows)

# 设置设备权限 (Linux)
sudo chmod 666 /dev/ttyACM0

# 测试脑电设备连接
python -m eeg_music.example.example_record --test-connection
```

#### 设备权限配置 (Linux)
```bash
# 方法1：临时权限 (重启后失效)
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyACM0

# 方法2：永久权限 (推荐)
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER
# 注销并重新登录使组权限生效

# 方法3：创建udev规则
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", MODE="0666"' | sudo tee /etc/udev/rules.d/99-arduino.rules
sudo udevadm control --reload-rules
```

## ⚡ 快速开始

### 🎵 最简单的开始方式

1. **激活环境并启动Arduino音乐播放**：
```bash
# 激活conda环境
conda activate eeg_music

# 启动Arduino音乐播放（钢琴音色）
python -m eeg_music.example.example_arduino_play -i piano
```

2. **打开Web可视化**：
```bash
# 在新终端中启动Web服务器
python3 -m http.server 5500

# 浏览器访问: http://localhost:5500/visualization/arduino_visualization.html
```

3. **开始演奏**：
   - 在Arduino传感器前挥手控制距离
   - 调节电位器改变音符参数
   - 观察Web界面的实时数据显示

### 🔧 常用命令

```bash
# 1. 检查设备连接
python -m eeg_music.reader.ArduinoSerialReader -l

# 2. 测试音频系统
python -c "import pygame; pygame.mixer.init(); print('音频系统正常!')"

# 3. 启动完整的可视化系统
bash scripts/start_eeg_music.sh
```

## 🎮 详细使用方法

### 快速启动指南
运行启动脚本查看所有可用命令：
```bash
bash scripts/start_eeg_music.sh
```

### 1. Arduino音乐播放
基于Arduino传感器数据生成音乐：
```bash
# 激活环境
source $HOME/anaconda3/etc/profile.d/conda.sh
conda activate eeg_music

# 启动Arduino音乐播放
python -m eeg_music.example.example_arduino_play -i piano

# 可选参数
python -m eeg_music.example.example_arduino_play \
  --arduino_port /dev/ttyUSB0 \
  --instrument violin \
  --rate 0.35 \
  --duration 60
```

### 2. Web可视化服务器
启动Web服务器查看实时数据：
```bash
python3 -m http.server 5500
```
访问: `http://localhost:5500/visualization/arduino_visualization.html`

### 3. 组合模式播放
同时使用Arduino和脑电数据：
```bash
python -m eeg_music.example.example_combined_play \
  --arduino-port /dev/ttyUSB0 \
  --mindwave-port /dev/ttyACM0 \
  -i violin
```

### 4. 脑电数据记录
记录脑电数据用于后续分析：
```bash
python -m eeg_music.example.example_record \
  -p /dev/ttyACM0 \
  -n "张三" \
  -m "放松" \
  -d 300
```

### 5. 设备检查
检查可用的串口设备：
```bash
python -m eeg_music.reader.ArduinoSerialReader -l
```

## 🎼 音乐生成原理

### 传感器到音乐的映射
- **距离传感器** → 音符选择 (音高)
- **滑动电位器** → 音符持续时间
- **旋转电位器** → 音阶选择 (C大调、G大调等)
- **脑电注意力** → 音符频率微调
- **脑电冥想度** → 音量控制

### 支持的音阶
- C大调 (C Major)
- G大调 (G Major)  
- D大调 (D Major)
- E小调 (E Minor)
- A小调 (A Minor)

### 支持的乐器音色
- 钢琴 (Piano)
- 小提琴 (Violin)
- 长笛 (Flute)
- 吉他 (Guitar)
- 小号 (Trumpet)

## 📊 数据格式

### Arduino数据格式
```
时间戳,距离,音阶,音符,频率,电位器,旋转电位器,按钮状态
2024-01-01 12:00:00,25.5,C Major,3,329.63,2.5,G Major,0
```

### 脑电数据格式
```json
{
  "timestamp": "2024-01-01 12:00:00",
  "attention": 75,
  "meditation": 60,
  "delta": 12000,
  "theta": 15000,
  "lowAlpha": 8000,
  "highAlpha": 9000,
  "lowBeta": 12000,
  "highBeta": 8000,
  "lowGamma": 5000,
  "midGamma": 3000
}
```

## 🌐 网络配置

### 树莓派部署
项目支持在树莓派上运行：
- **树莓派4B**: `192.168.5.12`
- **树莓派5**: `192.168.5.11`

SSH连接：
```bash
ssh three@192.168.5.12  # 树莓派4B
ssh three@192.168.5.11  # 树莓派5
```

### Web服务访问
- 本地访问: `http://localhost:5500`
- 树莓派访问: `http://192.168.5.11:5500`

## 🔧 故障排除

### 安装问题

1. **依赖包安装失败**
   ```bash
   # 更新pip
   pip install --upgrade pip setuptools wheel
   
   # 如果torch安装失败，尝试CPU版本
   pip install torch==1.13.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
   
   # 如果torcheeg安装失败，使用conda
   conda install -c conda-forge torcheeg
   ```

2. **Python版本兼容性**
   ```bash
   # 检查Python版本
   python --version  # 需要3.9+
   
   # 如果版本过低，安装新版本
   conda install python=3.9.21
   ```

### 设备连接问题

3. **Arduino设备连接失败**
   ```bash
   # 检查设备连接
   ls -la /dev/tty*
   dmesg | grep tty  # 查看设备日志
   
   # 修改设备权限
   sudo chmod 666 /dev/ttyUSB0
   sudo usermod -a -G dialout $USER
   
   # 测试串口通信
   python -c "import serial; s=serial.Serial('/dev/ttyUSB0', 9600); print('连接成功')"
   ```

4. **Mindwave脑电设备连接**
   ```bash
   # 检查设备状态
   ls -la /dev/ttyACM*
   
   # 设置权限
   sudo chmod 666 /dev/ttyACM0
   
   # 检查设备信息
   udevadm info -a -n /dev/ttyACM0
   ```

### 音频问题

5. **音频播放问题**
   ```bash
   # 检查音频系统
   pulseaudio --check
   
   # 重启音频服务
   pulseaudio --kill && pulseaudio --start
   
   # 测试pygame音频
   python -c "import pygame; pygame.mixer.init(); print('音频初始化成功')"
   
   # 如果还有问题，尝试ALSA
   export SDL_AUDIODRIVER=alsa
   ```

6. **音频延迟问题**
   ```bash
   # 降低音频缓冲区大小
   export SDL_AUDIODRIVER=pulse
   export PULSE_LATENCY_MSEC=30
   ```

### 网络和Web服务问题

7. **Flask服务器启动失败**
   ```bash
   # 检查端口占用
   netstat -tlnp | grep :5500
   
   # 杀死占用端口的进程
   sudo kill -9 $(lsof -t -i:5500)
   
   # 更换端口启动
   python3 -m http.server 8000
   ```

8. **WebSocket连接失败**
   ```bash
   # 检查防火墙设置
   sudo ufw status
   sudo ufw allow 5500
   
   # 检查网络连接
   ping localhost
   curl http://localhost:5500
   ```

### 性能问题

9. **CPU占用过高**
   ```bash
   # 降低采样频率
   python -m eeg_music.example.example_arduino_play --rate 0.5
   
   # 减少最大声音数量
   python -m eeg_music.example.example_arduino_play --max-sounds 50
   ```

10. **内存不足**
    ```bash
    # 检查内存使用
    free -h
    
    # 清理Python缓存
    find . -type d -name __pycache__ -exec rm -r {} +
    
    # 重启Python环境
    conda deactivate && conda activate eeg_music
    ```

### 数据问题

11. **数据记录失败**
    ```bash
    # 检查数据目录权限
    ls -la data/
    chmod 755 data/
    
    # 手动创建目录
    mkdir -p data/eeg data/music_notes
    ```

12. **Arduino通信问题**
    - 检查波特率设置(9600)
    - 验证Arduino代码上传
    - 检查传感器连接
    - 重新插拔USB线
    - 重启Arduino设备

## 📁 项目结构

```
eeg_music/
├── arduino/                 # Arduino代码
│   ├── arduino.ino         # 主程序
│   └── old/                # 历史版本
├── data/                   # 数据文件
│   ├── eeg/               # 脑电数据
│   ├── img/               # 图片资源
│   │   └── demo_play.mp4  # 演示视频
│   ├── instrument/        # 乐器音色文件
│   └── music_notes/       # 音符记录
├── eeg_music/             # 主要Python包
│   ├── audio/             # 音频处理
│   ├── example/           # 示例程序
│   ├── reader/            # 数据读取
│   ├── server/            # Web服务器
│   └── util/              # 工具函数
├── scripts/               # 启动脚本
│   ├── start_eeg_music.sh # 主启动脚本
│   ├── simple_play.sh     # 简单播放
│   ├── python_server.sh   # Web服务器
│   └── environment.sh     # 环境配置
├── visualization/         # Web可视化
└── README.md             # 项目文档
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发环境设置
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建GitHub Issue
- 发送邮件至项目维护者

---

*让音乐与科技完美融合，用脑电波奏响未来之声！* 🎵🧠✨