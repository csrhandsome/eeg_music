#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EEG音乐系统 - Flask服务器启动示例
替代原有的WebSocket服务器，使用Flask + Socket.IO
"""

import os
import sys
import argparse
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from eeg_music.server.FlaskServer import FlaskServer, run_flaskserver_thread

def run_flask_server_only():
    """启动仅提供API和Socket.IO服务的Flask服务器，不需要硬件连接"""
    print("启动Flask服务器（无硬件模式）...")
    
    # 创建FlaskServer实例
    flaskserver = FlaskServer()
    
    try:
        # 直接运行Flask服务器，不需要Arduino和Mindwave读取器
        flaskserver.run(arduino_reader=None, mindwave_reader=None)
    except KeyboardInterrupt:
        print("\nFlask服务器已停止。")
    except Exception as e:
        print(f"\n启动Flask服务器时出错: {e}")

def run_flask_with_hardware(arduino_port=None, mindwave_port=None):
    """启动包含硬件支持的Flask服务器"""
    print("启动Flask服务器（硬件支持模式）...")
    
    arduino_reader = None
    mindwave_reader = None
    
    # 启动Arduino读取器
    if arduino_port:
        try:
            from eeg_music.reader.ArduinoSerialReader import ArduinoSerialReader
            arduino_reader = ArduinoSerialReader(port=arduino_port)
            arduino_reader.start_reading()
            print(f"✅ Arduino读取器已启动 (端口: {arduino_port})")
        except ImportError:
            print("❌ 无法导入ArduinoSerialReader")
        except Exception as e:
            print(f"❌ Arduino读取器启动失败: {e}")
    
    # 启动Mindwave读取器
    if mindwave_port:
        try:
            from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader
            mindwave_reader = MindwaveSerialReader(port=mindwave_port)
            mindwave_reader.start_reading()
            print(f"✅ Mindwave读取器已启动 (端口: {mindwave_port})")
        except ImportError:
            print("❌ 无法导入MindwaveSerialReader")
        except Exception as e:
            print(f"❌ Mindwave读取器启动失败: {e}")
    
    # 使用线程运行Flask服务器
    try:
        run_flaskserver_thread(arduino_reader, mindwave_reader)
    except KeyboardInterrupt:
        print("\nFlask服务器已停止。")
    except Exception as e:
        print(f"\n启动Flask服务器时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description='启动Flask服务器')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务器地址 (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5500, help='服务器端口 (default: 8766)')
    parser.add_argument('--with-arduino', action='store_true', help='启用Arduino数据读取器')
    parser.add_argument('--with-mindwave', action='store_true', help='启用Mindwave数据读取器')
    parser.add_argument('--arduino-port', type=str, default='/dev/ttyUSB0', help='Arduino串口设备')
    parser.add_argument('--mindwave-port', type=str, default='/dev/ttyACM0', help='Mindwave串口设备')
    
    args = parser.parse_args()
    
    
    if args.with_arduino or args.with_mindwave:
        # 硬件模式
        arduino_port = args.arduino_port if args.with_arduino else None
        mindwave_port = args.mindwave_port if args.with_mindwave else None
        run_flask_with_hardware(arduino_port, mindwave_port)
    else:
        # 仅API模式
        run_flask_server_only()

if __name__ == "__main__":
    main() 