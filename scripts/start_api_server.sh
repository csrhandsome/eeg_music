#!/bin/bash

echo "=== EEG音乐系统 - HTTP服务器启动脚本 ==="

# 激活conda环境
echo "激活conda环境..."
source $HOME/anaconda3/etc/profile.d/conda.sh
conda activate eeg_music

if [ $? -ne 0 ]; then
    echo "❌ 错误: 无法激活eeg_music环境"
    echo "请确保已经创建了eeg_music conda环境"
    exit 1
fi

echo "✅ conda环境已激活"

# 检查当前工作目录
current_dir=$(pwd)
echo "当前工作目录: $current_dir"

# 确保在正确的项目目录中
if [[ ! -d "eeg_music" ]] || [[ ! -d "data/music_notes" ]]; then
    echo "❌ 错误: 请在eeg_music项目根目录中运行此脚本"
    echo "应该包含 eeg_music/ 和 data/music_notes/ 目录"
    exit 1
fi

echo "✅ 项目目录检查通过"

# 启动简单HTTP服务器
echo ""
echo "🚀 启动HTTP服务器（静态文件服务）..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 HTTP服务器地址: http://localhost:5500"
echo "🏠 静态文件服务: http://localhost:5500/"
echo "📚 历史记录页面: http://localhost:5500/visualization/history.html"
echo "🎵 欢迎页面: http://localhost:5500/visualization/welcomepage.html"
echo "🎮 音游页面: http://localhost:5500/visualization/music_game_p5.html"
echo "📝 录制页面: http://localhost:5500/visualization/record.html"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 提示: 按 Ctrl+C 停止服务器"
echo ""

# 启动Python简单HTTP服务器
python3 -m http.server 5500

echo ""
echo "✅ HTTP服务器已停止"