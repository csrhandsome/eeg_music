#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EEG音乐系统 - Flask服务器启动脚本
用于替代原有的WebSocket服务器
"""

import os
import sys
import argparse
from FlaskServer import FlaskServer, run_flaskserver_thread

def main():
    parser = argparse.ArgumentParser(description='启动EEG音乐系统Flask服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', default=5500, type=int, help='服务器端口 (默认: 5500)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--with-arduino', action='store_true', help='启用Arduino数据读取器')
    parser.add_argument('--with-mindwave', action='store_true', help='启用Mindwave数据读取器')
    parser.add_argument('--arduino-port', default='/dev/ttyUSB0', help='Arduino串口设备 (默认: /dev/ttyUSB0)')
    parser.add_argument('--mindwave-port', default='/dev/ttyUSB1', help='Mindwave串口设备 (默认: /dev/ttyUSB1)')
    
    args = parser.parse_args()
    
    # 创建Flask服务器实例
    server = FlaskServer()
    
    # 根据参数配置数据读取器
    arduino_reader = None
    mindwave_reader = None
    
    if args.with_arduino:
        try:
            # 动态导入Arduino读取器
            from eeg_music.reader.ArduinoSerialReader import ArduinoSerialReader
            arduino_reader = ArduinoSerialReader(port=args.arduino_port)
            arduino_reader.start_reading()
            print(f"✅ Arduino读取器已启动 (端口: {args.arduino_port})")
        except ImportError:
            print("❌ 无法导入ArduinoSerialReader，请检查模块路径")
        except Exception as e:
            print(f"❌ Arduino读取器启动失败: {e}")
    
    if args.with_mindwave:
        try:
            # 动态导入Mindwave读取器
            from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader
            mindwave_reader = MindwaveSerialReader(port=args.mindwave_port)
            mindwave_reader.start_reading()
            print(f"✅ Mindwave读取器已启动 (端口: {args.mindwave_port})")
        except ImportError:
            print("❌ 无法导入MindwaveSerialReader，请检查模块路径")
        except Exception as e:
            print(f"❌ Mindwave读取器启动失败: {e}")
    
    # 设置数据读取器
    server.set_data_readers(arduino_reader=arduino_reader, mindwave_reader=mindwave_reader)
    
    # 检查data目录
    data_dir = os.path.join(os.getcwd(), 'data', 'music_notes')
    if not os.path.exists(data_dir):
        print(f"⚠️  警告: data/music_notes 目录不存在，创建中...")
        os.makedirs(data_dir, exist_ok=True)
        print(f"✅ 已创建目录: {data_dir}")
    else:
        file_count = len([f for f in os.listdir(data_dir) if f.endswith('.csv')])
        print(f"📁 找到 {file_count} 个音乐记录文件")
    
    # 检查visualization目录
    vis_dir = os.path.join(os.getcwd(), 'visualization')
    if not os.path.exists(vis_dir):
        print(f"❌ 错误: visualization 目录不存在: {vis_dir}")
        print("请确保在项目根目录中运行此脚本")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("🚀 准备启动EEG音乐系统Flask服务器")
    print(f"📍 主机: {args.host}")
    print(f"🔌 端口: {args.port}")
    print(f"🔧 调试模式: {'启用' if args.debug else '禁用'}")
    print(f"🎛️  Arduino: {'启用' if args.with_arduino else '禁用'}")
    print(f"🧠 Mindwave: {'启用' if args.with_mindwave else '禁用'}")
    print("="*50)
    
    try:
        # 修改端口配置
        server.app.config['PORT'] = args.port
        
        # 启动服务器
        print(f"Flask服务器启动: http://{args.host}:{args.port}")
        print(f"SocketIO服务器启动: ws://{args.host}:{args.port}")
        
        # 启动数据广播
        server.start_data_broadcast()
        
        # 启动服务器
        server.socketio.run(server.app, host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n\n✅ Flask服务器已停止")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 