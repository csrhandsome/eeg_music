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

### 1. 克隆项目
```bash
git clone <repository-url>
cd eeg_music
```

### 2. 创建Conda环境
```bash
# 运行环境配置脚本
bash scripts/environment.sh
```

或手动创建：
```bash
# 创建conda环境
conda create -n eeg_music python=3.9.21
conda activate eeg_music

# 安装依赖
pip install pygame pyserial torcheeg moabb websockets aiohttp
pip install Flask==2.3.3
pip install Flask-SocketIO==5.3.6
pip install Flask-CORS==4.0.0
pip install python-socketio==5.8.0
pip install eventlet==0.33.3 

```

### 3. 硬件连接
- 将Mindwave设备连接到 `/dev/ttyACM0`
- 将Arduino设备连接到 `/dev/ttyUSB0`
- 确保设备权限正确：
```bash
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyACM0
```

## 🎮 使用方法

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

### 常见问题

1. **设备连接失败**
   ```bash
   # 检查设备连接
   ls -la /dev/tty*
   # 修改设备权限
   sudo chmod 666 /dev/ttyUSB0
   sudo chmod 666 /dev/ttyACM0
   ```

2. **音频播放问题**
   ```bash
   # 检查音频系统
   pulseaudio --check
   # 重启音频服务
   pulseaudio --kill && pulseaudio --start
   ```

3. **脑电设备连接**
   - 确保电极湿润
   - 检查设备配对状态
   - 验证串口波特率(57600)

4. **Arduino通信问题**
   - 检查波特率设置(9600)
   - 验证Arduino代码上传
   - 检查传感器连接

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