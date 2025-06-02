#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EEG音乐系统 - 可视化服务器启动脚本
支持选择Flask或WebSocket服务器
"""

import argparse
import asyncio
import threading
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from eeg_music.server.WebServer import run_webserver_thread
from eeg_music.server.FlaskServer import run_flaskserver_thread
from eeg_music.reader.ArduinoSerialReader import ArduinoSerialReader
from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader

def start_websocket_server(arduino_port, arduino_baudrate, mindwave_port, mindwave_baudrate, name):
    """启动原WebSocket服务器"""
    print("启动WebSocket服务器...")
    
    try:
        # 创建读取器
        arduino_reader = ArduinoSerialReader(port=arduino_port, baudrate=arduino_baudrate)
        mindwave_reader = MindwaveSerialReader(port=mindwave_port, baudrate=mindwave_baudrate, name=name)
        
        # 启动读取器
        arduino_reader.start_reading()
        mindwave_reader.start_reading()
        
        print(f"✅ Arduino读取器已启动 (端口: {arduino_port})")
        print(f"✅ Mindwave读取器已启动 (端口: {mindwave_port})")
        
        # 在线程中运行WebSocket服务器
        server_thread = threading.Thread(
            target=run_webserver_thread, 
            args=(arduino_reader, mindwave_reader),
            daemon=True
        )
        server_thread.start()
        
        # 等待线程完成或键盘中断
        try:
            server_thread.join()
        except KeyboardInterrupt:
            print("\nWebSocket服务器已停止。")
            
    except Exception as e:
        print(f"\n启动WebSocket服务器时出错: {e}")

def start_flask_server(arduino_port, arduino_baudrate, mindwave_port, mindwave_baudrate, name):
    """启动Flask服务器"""
    print("启动Flask服务器...")
    
    try:
        # 创建读取器
        arduino_reader = ArduinoSerialReader(port=arduino_port, baudrate=arduino_baudrate)
        mindwave_reader = MindwaveSerialReader(port=mindwave_port, baudrate=mindwave_baudrate, name=name)
        
        # 启动读取器
        arduino_reader.start_reading()
        mindwave_reader.start_reading()
        
        print(f"✅ Arduino读取器已启动 (端口: {arduino_port})")
        print(f"✅ Mindwave读取器已启动 (端口: {mindwave_port})")
        
        # 运行Flask服务器（阻塞式）
        run_flaskserver_thread(arduino_reader, mindwave_reader)
        
    except KeyboardInterrupt:
        print("\nFlask服务器已停止。")
    except Exception as e:
        print(f"\n启动Flask服务器时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description='EEG音乐系统可视化服务器')
    
    # 服务器选择
    parser.add_argument('--server-type', type=str, choices=['flask', 'websocket'], default='flask',
                        help='选择服务器类型 (default: flask)')
    
    # 硬件参数
    parser.add_argument('--arduino-port', type=str, default='COM3', 
                        help='Arduino端口 (default: COM3)')
    parser.add_argument('--arduino-baudrate', type=int, default=9600, 
                        help='Arduino波特率 (default: 9600)')
    parser.add_argument('--mindwave-port', type=str, default='COM4', 
                        help='Mindwave端口 (default: COM4)')
    parser.add_argument('--mindwave-baudrate', type=int, default=57600, 
                        help='Mindwave波特率 (default: 57600)')
    parser.add_argument('--name', type=str, default='default', 
                        help='Mindwave读取器名称 (default: default)')
    
    # 无硬件模式
    parser.add_argument('--no-hardware', action='store_true',
                        help='无硬件模式（仅启动服务器，不连接Arduino和Mindwave）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎵 EEG音乐系统可视化服务器")
    print("=" * 60)
    print(f"🔧 服务器类型: {args.server_type.upper()}")
    print(f"🎛️  硬件模式: {'禁用' if args.no_hardware else '启用'}")
    
    if not args.no_hardware:
        print(f"📡 Arduino端口: {args.arduino_port} ({args.arduino_baudrate} baud)")
        print(f"🧠 Mindwave端口: {args.mindwave_port} ({args.mindwave_baudrate} baud)")
    
    if args.server_type == 'flask':
        if args.no_hardware:
            print("🌐 启动地址: http://localhost:5500")
            print("🔌 Socket.IO: ws://localhost:5500")
        else:
            print("🌐 启动地址: http://localhost:5500")
            print("🔌 Socket.IO: ws://localhost:5500")
    else:
        print("🌐 WebSocket: ws://localhost:8765")
        print("📡 HTTP服务: http://localhost:8766")
    
    print("=" * 60)
    print()
    
    if args.no_hardware:
        # 无硬件模式
        if args.server_type == 'flask':
            from eeg_music.server.FlaskServer import FlaskServer
            server = FlaskServer()
            try:
                server.run(None, None)
            except KeyboardInterrupt:
                print("\nFlask服务器已停止。")
        else:
            from eeg_music.server.WebServer import run_webserver_thread
            try:
                run_webserver_thread(None, None)
            except KeyboardInterrupt:
                print("\nWebSocket服务器已停止。")
    else:
        # 硬件模式
        if args.server_type == 'flask':
            start_flask_server(
                args.arduino_port, args.arduino_baudrate,
                args.mindwave_port, args.mindwave_baudrate,
                args.name
            )
        else:
            start_websocket_server(
                args.arduino_port, args.arduino_baudrate,
                args.mindwave_port, args.mindwave_baudrate,
                args.name
            )

if __name__ == "__main__":
    main() 