import time
import argparse
import pygame
import numpy as np
from threading import Thread

from eeg_music.reader.ArduinoSerialReader import ArduinoSerialReader
from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader
from eeg_music.audio.MusicPlayer import MusicPlayer
from arduino.util.scale import map_to_frequency


def mindwave_play():
    """根据脑电波数据生成音乐"""
    # 命令行参数配置
    parser = argparse.ArgumentParser(description='脑电波音乐演奏')
    parser.add_argument('-p', '--port', help='串口设备路径')
    parser.add_argument('-b', '--baudrate', type=int, default=57600, help='波特率')
    parser.add_argument('-d', '--duration', type=int, help='演奏持续时间（秒）')
    parser.add_argument('-i', '--instrument', default='piano', 
                        choices=['piano', 'flute', 'violin', 'guitar', 'trumpet'], 
                        help='乐器音色选择')
    parser.add_argument('-n', '--name', default='default', help='被试者名称')
    args = parser.parse_args()
    
    # 初始化Pygame音频
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
    
    # 创建Mindwave读取器
    reader = MindwaveSerialReader(port=args.port, baudrate=args.baudrate, name=args.name)
    player = MusicPlayer()
    # 连接设备
    if reader.connect():
        try:
            print(f"开始根据脑电波数据演奏音乐，使用{args.instrument}音色...")
            start_time = time.time()
            last_play_time = 0
            
            # 定义一个简单的音阶（C大调）
            C_MAJOR_SCALE = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
            
            # 主循环
            while True:
                # 获取当前数据
                brain_data = {
                    'attention': reader.neuro.attention,
                    'meditation': reader.neuro.meditation,
                    'rawValue': reader.neuro.rawValue,
                    'delta': reader.neuro.delta,
                    'theta': reader.neuro.theta,
                    'lowAlpha': reader.neuro.lowAlpha,
                    'highAlpha': reader.neuro.highAlpha,
                    'lowBeta': reader.neuro.lowBeta,
                    'highBeta': reader.neuro.highBeta,
                    'lowGamma': reader.neuro.lowGamma,
                    'midGamma': reader.neuro.midGamma
                }
                
                current_time = time.time()
                
                # 每0.3秒播放一次音符
                if current_time - last_play_time >= 0.3:
                    # 使用专注度选择音符（0-100 -> 音阶的8个音符）
                    attention = max(1, min(100, brain_data['attention']))
                    note_index = int(map_to_frequency(attention, 0, 100, 0, len(C_MAJOR_SCALE)-1))
                    freq = C_MAJOR_SCALE[note_index]
                    
                    # 使用冥想度控制音符持续时间（0-100 -> 0.2-1.0秒）
                    meditation = max(1, min(100, brain_data['meditation']))
                    duration = map_to_frequency(meditation, 0, 100, 0.2, 1.0)
                    
                    # 使用beta波强度控制音量（0-最大值 -> 0.3-1.0）
                    beta_power = (brain_data['lowBeta'] + brain_data['highBeta']) / 2
                    intensity = map_to_frequency(beta_power, 0, 100000, 0.3, 1.0)
                    
                    print(f"专注度: {attention}, 冥想度: {meditation}, 播放音符: {freq:.2f}Hz, 持续: {duration:.2f}秒, 强度: {intensity:.2f}")
                    player.play_note(freq, duration, args.instrument, intensity, wait=False)
                    last_play_time = current_time
                
                # 检查是否达到指定的持续时间
                if args.duration and (time.time() - start_time) >= args.duration:
                    break
                    
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n停止演奏")
        finally:
            reader.disconnect()
    else:
        print("无法连接到脑电波设备，请检查连接或指定正确的端口")

def combined_play():
    """结合Arduino和脑电波数据生成音乐"""
    # 命令行参数配置
    parser = argparse.ArgumentParser(description='结合Arduino和脑电波的音乐演奏')
    parser.add_argument('--arduino-port', help='Arduino串口设备路径')
    parser.add_argument('--arduino-baudrate', type=int, default=9600, help='Arduino波特率')
    parser.add_argument('--mindwave-port', help='Mindwave串口设备路径')
    parser.add_argument('--mindwave-baudrate', type=int, default=57600, help='Mindwave波特率')
    parser.add_argument('-d', '--duration', type=int, help='演奏持续时间（秒）')
    parser.add_argument('-i', '--instrument', default='piano', 
                        choices=['piano', 'flute', 'violin', 'guitar', 'trumpet'], 
                        help='乐器音色选择')
    parser.add_argument('-n', '--name', default='default', help='被试者名称')
    args = parser.parse_args()
    
    # 初始化Pygame音频
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
    
    # 创建Arduino读取器
    arduino_reader = ArduinoSerialReader(port=args.arduino_port, baudrate=args.arduino_baudrate)
    arduino_connected = arduino_reader.connect()
    
    # 创建Mindwave读取器
    mindwave_reader = MindwaveSerialReader(port=args.mindwave_port, baudrate=args.mindwave_baudrate, name=args.name)
    mindwave_connected = mindwave_reader.connect()
    
    player = MusicPlayer()
    if not (arduino_connected or mindwave_connected):
        print("无法连接到任何设备，请检查连接")
        return
    
    print(f"Arduino连接状态: {'成功' if arduino_connected else '失败'}")
    print(f"Mindwave连接状态: {'成功' if mindwave_connected else '失败'}")
    print(f"开始演奏结合数据的音乐，使用{args.instrument}音色...")
    
    try:
        start_time = time.time()
        last_play_time = 0
        
        # 定义一个简单的音阶（C大调）
        C_MAJOR_SCALE = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
        
        # 主循环
        while True:
            current_time = time.time()
            
            # 处理Arduino数据
            if arduino_connected and arduino_reader.serial and arduino_reader.serial.in_waiting:
                try:
                    raw_line = arduino_reader.serial.readline()
                    line = raw_line.decode('utf-8', errors='replace').strip()
                    if line:
                        arduino_reader._parse_data(line)
                except Exception:
                    pass
            
            # 每0.25秒播放一次音符
            if current_time - last_play_time >= 0.25:
                # 从脑电波获取注意力作为音符选择
                if mindwave_connected:
                    attention = max(1, min(100, mindwave_reader.neuro.attention))
                    meditation = max(1, min(100, mindwave_reader.neuro.meditation))
                    beta_power = mindwave_reader.neuro.lowBeta + mindwave_reader.neuro.highBeta
                else:
                    attention = 50
                    meditation = 50
                    beta_power = 50000
                
                # 从Arduino获取距离作为频率修饰
                if arduino_connected:
                    arduino_data = arduino_reader.current_data
                    distance = arduino_data['distance']
                    voltage = arduino_data['voltage']
                else:
                    distance = 50
                    voltage = 2.5
                
                # 结合数据生成音乐参数
                note_index = int(map_to_frequency(attention, 0, 100, 0, len(C_MAJOR_SCALE)-1))
                base_freq = C_MAJOR_SCALE[note_index]
                
                # 使用距离微调频率（±半音）
                freq_modifier = map_to_frequency(distance, 30, 150, -20, 20)
                freq = base_freq + freq_modifier
                
                # 使用冥想度和电压控制持续时间
                duration = map_to_frequency(meditation * voltage, 0, 500, 0.15, 0.8)
                
                # 使用beta波和电压控制强度
                intensity = map_to_frequency(beta_power * voltage, 0, 500000, 0.4, 1.0)
                
                print(f"注意力: {attention}, 距离: {distance}, 频率: {freq:.1f}Hz, 持续: {duration:.2f}秒")
                player.play_note(freq, duration, args.instrument, intensity, wait=False)
                last_play_time = current_time
            
            # 检查是否达到指定的持续时间
            if args.duration and (time.time() - start_time) >= args.duration:
                break
                
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n停止演奏")
    finally:
        if arduino_connected:
            arduino_reader.disconnect()
        if mindwave_connected:
            mindwave_reader.disconnect()

if __name__ == "__main__":
    # 根据需要选择合适的演奏函数
    # mindwave_play()     # 仅使用脑电波数据
    combined_play()       # 结合两种数据源