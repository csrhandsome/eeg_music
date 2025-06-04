import time
import argparse
import pygame
import asyncio
import threading
from eeg_music.reader.ArduinoSerialReader import ArduinoSerialReader
from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader
from eeg_music.audio.MusicPlayer import MusicPlayer
from eeg_music.audio.MusicDataRecorder import MusicDataRecorder
from eeg_music.util.map import map_to_frequency
from eeg_music.audio.scales import get_closest_note, map_value_to_note
from eeg_music.server.FlaskServer import FlaskServer

def test_playback_functionality():
    """测试历史文件回放功能"""
    print("测试历史文件回放功能...")
    
    # 创建FlaskServer实例（不需要Arduino连接）
    flaskserver = FlaskServer()
    
    # 启动Flask服务器线程
    flask_thread = threading.Thread(
        target=lambda: flaskserver.run(None, None),
        daemon=True
    )
    flask_thread.start()
    
    print("Flask服务器已启动，等待用户在网页上选择文件进行回放...")
    print("请打开浏览器访问: http://localhost:5500/history.html")
    print("选择一个心音轨迹文件来测试回放功能")
    print("按 Ctrl+C 停止测试")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n测试结束")

def arduino_play_by_rate():
    """根据Arduino传感器数据播放指定的频率"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Arduino 传感器音乐演奏')
    parser.add_argument('--arduino_port',default='/dev/ttyUSB0', help='串口设备路径,例如COM3(Windows)或/dev/ttyUSB0(Linux)')
    parser.add_argument('--mindwave_port', default='/dev/ttyACM0',help='串口设备路径,例如COM3(Windows)或/dev/ttyACM0(Linux)')
    parser.add_argument('--arduino_baudrate', type=int, default=9600, help='Arduino波特率')
    parser.add_argument('--mindwave_baudrate', type=int, default=57600,help='Mindwave串口设备路径')
    parser.add_argument('-d', '--duration', type=int, help='演奏持续时间（秒），默认持续到中断')
    parser.add_argument('-i', '--instrument', default='piano', choices=['piano', 'flute', 'violin', 'guitar', 'trumpet'], help='乐器音色选择')
    parser.add_argument('-r', '--rate', type=float, default=0.35, help='播放速率(秒),默认0.35秒一个音符')
    parser.add_argument('-m', '--max-sounds', type=int, default=100, help='最大同时存在的声音对象数量')
    
    args = parser.parse_args()
    

    # 创建Arduino读取器
    arduino_reader = None
    if args.arduino_port:
        arduino_reader = ArduinoSerialReader(
            port=args.arduino_port,
            baudrate=args.arduino_baudrate
        )
    
    # 创建Mindwave读取器（如果指定了端口）
    # mindwave_reader = None
    # if args.mindwave_port:
    #     mindwave_reader = MindwaveSerialReader(
    #         port=args.mindwave_port,
    #         baudrate=args.mindwave_baudrate,
    #         name="default"
    #     )
    
    # 创建FlaskServer实例
    flaskserver = FlaskServer()
    flaskserver.set_data_readers(arduino_reader, None)
    
    # 启动flask的WebSocket服务器线程
    # lambda 在这里充当了一个"包裹器"或"适配器"，它把一个需要参数的函数调用转化成了一个不需要参数的函数
    flask_thread = threading.Thread(
        target=lambda: flaskserver.run(arduino_reader, None),  # 传递flaskserver实例
        daemon=True  # 设为守护线程，主线程结束时自动退出
    )
    flask_thread.start()
    
    # 创建音乐播放器实例
    player = MusicPlayer(max_sounds=args.max_sounds)
    
    # 使用FlaskServer中的MusicDataRecorder实例
    recorder = flaskserver.get_music_recorder()
    
    print(f"开始根据传感器数据演奏音乐，使用{args.instrument}音色...")
    # 连接Arduino
    if arduino_reader.connect():
        try:
            start_time = time.time()
            last_play_time = 0
            
            # 用于存储最后处理的数据行，避免重复处理相同数据
            last_processed_line = ""
            
            # 主循环
            while True:
                # 读取一行数据
                if arduino_reader.serial and arduino_reader.serial.in_waiting:
                    raw_line = arduino_reader.serial.readline()
                    try:
                        line = raw_line.decode('utf-8').strip()
                        # 避免处理重复数据
                        if line and line != last_processed_line:
                            arduino_reader._parse_data(line)
                            last_processed_line = line
                            
                            # 获取当前数据
                            arduino_data = arduino_reader.current_data
                            current_time = time.time()
                            
                            # 限制播放频率
                            if current_time - last_play_time >= args.rate:
                                distance = arduino_data['distance']
                                if arduino_data['freq'] > 0:
                                    # 使用Arduino提供的频率
                                    freq = arduino_data['freq']
                                else:
                                    # 或者使用距离映射到频率
                                    freq = map_to_frequency(distance, 0, 100)
                                
                                # 安全处理电压值
                                voltage = min(max(arduino_data['potentiometer'], 0), 5)
                                
                                # 根据传感器数据动态调整音符持续时间
                                base_duration = 1.5 + (voltage / 5) * 0.5  # 1.5-2秒
                                
                                # 为不同乐器调整持续时间策略
                                if args.instrument == 'piano':
                                    # 钢琴音符可以短一些
                                    duration = min(base_duration, 0.8)
                                elif args.instrument in ['flute', 'violin']:
                                    # 管弦乐器需要更长的持续时间
                                    duration = min(base_duration * 1.5, 1.5)
                                else:
                                    duration = min(base_duration, 1.0)
                                # duration=1.5
                                # 播放音符 - 使用类方法而不是全局函数
                                
                                if distance < 50 :
                                    # 检查录制状态，只有在录制状态下才记录音符
                                    if flaskserver.is_recording_active():
                                        recorder.record_note(freq, duration, args.instrument, intensity=0.8)
                                        # print(f"录制音符: 频率 {freq:.2f} Hz, 持续时间 {duration:.2f}秒")
                                    # else:
                                    #     print(f"播放音符: 频率 {freq:.2f} Hz, 持续时间 {duration:.2f}秒 (未录制)")
                                    
                                    # 始终播放音符，不管录制状态
                                    player.play_wav_note(freq, duration, args.instrument, intensity=0.8, 
                                                     wait=False)
                                # 更新上次播放时间
                                last_play_time = current_time
                    except UnicodeDecodeError:
                        pass
                
                # 检查是否达到指定的持续时间
                if args.duration and (time.time() - start_time) >= args.duration:
                    recorder.save_to_file()
                    break
                    
                # 增加休眠时间，减少CPU占用
                time.sleep(0.03)
                
        except KeyboardInterrupt:
            print("\n停止演奏")
        finally:
            # 关闭连接
            recorder.save_to_file()
            arduino_reader.disconnect()
            print(f"播放器中的声音对象数量: {len(player.sound_objects)}")
    else:
        print("无法连接到Arduino设备,请检查连接或指定正确的端口")

    


if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--test-playback":
        test_playback_functionality()
    else:
        arduino_play_by_rate()
    # arduino_play_by_scale()
