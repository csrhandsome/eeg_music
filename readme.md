# EEG音乐生成系统

基于脑电波(EEG)和Arduino传感器的实时音乐生成系统。

## 🎵 功能特色

- **多模态输入**: 支持脑电波(Mindwave)和Arduino传感器数据
- **实时音乐生成**: 根据传感器数据实时生成钢琴、小提琴、小号、古筝音色
- **Web可视化**: 提供实时数据可视化和音乐回放功能
- **情绪识别**: 基于脑电数据的KNN情绪分类
- **AI音乐生成**: DeepSeek API集成的智能音乐创作

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
- **脑电设备**: Mindwave Mobile (/dev/ttyACM0)
- **Arduino开发板**: Uno/Nano (/dev/ttyUSB0)
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

## 🚀 安装

### 1. 克隆项目
```bash
git clone <repository-url>
cd eeg_music
```

### 2. 创建环境
```bash
conda create -n eeg_music python=3.9.21
conda activate eeg_music
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 设备权限 (Linux)
```bash
sudo chmod 666 /dev/ttyUSB0 /dev/ttyACM0
sudo usermod -a -G dialout $USER
```

## ⚡ 快速开始

### 1. 启动音乐演奏
```bash
conda activate eeg_music
bash scripts/play.sh
```

### 2. 打开Web界面
```bash
# 新终端
python3 -m http.server 5500
# 浏览器访问: http://localhost:5500/visualization/welcomepage.html
```

## 🎮 主要功能

### Arduino音乐播放
```bash
python -m eeg_music.example.example_arduino_play -i piano
```

### 组合模式(脑电+Arduino)
```bash
python -m eeg_music.example.example_combine_play
```

### 脑电数据记录
```bash
python -m eeg_music.example.example_record -p /dev/ttyACM0 -n "用户名" -d 300
```

### AI音乐生成
```bash
python -m eeg_music.reader.DeepseekReader --prompt "创作一首快乐的小曲子"
```

## 🎼 传感器映射

- **距离传感器** → 音符选择
- **滑动电位器** → 音符持续时间  
- **旋转电位器** → 音阶选择
- **脑电注意力** → 音符强度
- **脑电情绪** → 乐器选择 (0=钢琴 1=小提琴 2=小号 3=古筝)

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
├── arduino/           # Arduino代码
├── data/             # 数据和音色文件
├── eeg_music/        # Python包
├── scripts/          # 启动脚本
├── visualization/    # Web界面
└── requirements.txt  # 依赖包
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