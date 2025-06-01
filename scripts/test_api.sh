#!/bin/bash

echo "=== EEG音乐系统 - HTTP服务器功能测试脚本 ==="
echo ""

# 检测服务器是否运行
echo "🔍 检测HTTP服务器状态..."
if curl -s --connect-timeout 3 http://localhost:5500/ > /dev/null 2>&1; then
    echo "✅ HTTP服务器运行正常"
else
    echo "❌ HTTP服务器未运行或无法连接"
    echo "💡 请先运行: bash scripts/start_api_server.sh"
    exit 1
fi

echo ""

# 测试静态文件服务
echo "🌐 测试静态文件服务..."

echo "📚 测试历史记录页面..."
if curl -s --head http://localhost:5500/visualization/history.html | grep "200 OK" > /dev/null; then
    echo "✅ 历史记录页面访问正常"
else
    echo "❌ 历史记录页面访问失败"
fi

echo "🎵 测试欢迎页面..."
if curl -s --head http://localhost:5500/visualization/welcomepage.html | grep "200 OK" > /dev/null; then
    echo "✅ 欢迎页面访问正常"
else
    echo "❌ 欢迎页面访问失败"
fi

echo "🎮 测试音游页面..."
if curl -s --head http://localhost:5500/visualization/music_game_p5.html | grep "200 OK" > /dev/null; then
    echo "✅ 音游页面访问正常"
else
    echo "❌ 音游页面访问失败"
fi

echo "📝 测试录制页面..."
if curl -s --head http://localhost:5500/visualization/record.html | grep "200 OK" > /dev/null; then
    echo "✅ 录制页面访问正常"
else
    echo "❌ 录制页面访问失败"
fi

echo ""

# 检查music_notes目录
echo "📁 检查音乐记录文件..."
if [ -d "data/music_notes" ]; then
    file_count=$(find data/music_notes -name "*.csv" | wc -l)
    echo "📄 找到 $file_count 个音乐记录文件"
    
    if [ "$file_count" -gt 0 ]; then
        echo "✅ 音乐记录文件存在"
        echo "📋 最新的5个文件:"
        find data/music_notes -name "*.csv" -type f -printf '%T@ %p\n' | sort -nr | head -5 | while read timestamp file; do
            size=$(stat --format="%s" "$file" 2>/dev/null || echo "0")
            if [ "$size" -ge 1048576 ]; then
                size_str="$(($size / 1048576))MB"
            elif [ "$size" -ge 1024 ]; then
                size_str="$(($size / 1024))KB"
            else
                size_str="${size}B"
            fi
            basename_file=$(basename "$file")
            echo "  • $basename_file ($size_str)"
        done
    else
        echo "⚠️  音乐记录文件为空"
    fi
else
    echo "❌ data/music_notes 目录不存在"
fi

echo ""

# 显示所有可用的页面
echo "🔗 所有可用的页面:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏠 主页(根目录):      http://localhost:5500/"
echo "📚 历史记录页面:      http://localhost:5500/visualization/history.html"
echo "🎵 欢迎页面:         http://localhost:5500/visualization/welcomepage.html"
echo "🎮 音游页面:         http://localhost:5500/visualization/music_game_p5.html"
echo "📝 录制页面:         http://localhost:5500/visualization/record.html"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "✅ HTTP服务器测试完成！"

# 如果有参数，打开浏览器
if [ "$1" = "--open" ]; then
    echo ""
    echo "🚀 正在打开历史记录页面..."
    if command -v xdg-open > /dev/null; then
        xdg-open http://localhost:5500/visualization/history.html
    elif command -v open > /dev/null; then
        open http://localhost:5500/visualization/history.html
    else
        echo "💡 请手动在浏览器中打开: http://localhost:5500/visualization/history.html"
    fi
fi 