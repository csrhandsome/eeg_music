import time
import argparse
import pygame
from eeg_music.reader.ArduinoSerialReader import ArduinoSerialReader
from eeg_music.audio.MusicPlayer import MusicPlayer
from arduino.util.scale import map_to_frequency
from data.instrument.scales import get_closest_note, map_value_to_note

def arduino_play_by_scale():
    """根据Arduino传感器数据播放制定音阶"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Arduino 传感器音乐演奏')
    parser.add_argument('-p', '--port', help='串口设备路径,例如COM3(Windows)或/dev/ttyUSB0(Linux)')
    parser.add_argument('-b', '--baudrate', type=int, default=9600, help='波特率,默认9600')
    parser.add_argument('-d', '--duration', type=int, help='演奏持续时间（秒），默认持续到中断')
    parser.add_argument('-i', '--instrument', default='piano', choices=['piano', 'flute', 'violin', 'guitar', 'trumpet'], help='乐器音色选择')
    parser.add_argument('-t', '--threshold', type=float, default=5.0, help='传感器变化触发阈值，默认5.0')
    parser.add_argument('-m', '--max-sounds', type=int, default=100, help='最大同时存在的声音对象数量')
    parser.add_argument('-s', '--scale', default='default', choices=['default', 'pentatonic'], help='音阶类型，默认使用乐器标准音阶，pentatonic为五声音阶')
    parser.add_argument('-min', '--min-value', type=float, default=0, help='传感器最小值，用于音阶映射')
    parser.add_argument('-max', '--max-value', type=float, default=100, help='传感器最大值，用于音阶映射')
    
    args = parser.parse_args()
    
    # 创建音乐播放器实例
    player = MusicPlayer(max_sounds=args.max_sounds)
    
    # 创建Arduino读取器
    reader = ArduinoSerialReader(
        port=args.port,
        baudrate=args.baudrate
    )
    
    # 连接Arduino
    if reader.connect():
        try:
            print(f"开始根据传感器数据演奏音乐，使用{args.instrument}音色和{args.scale}音阶...")
            print(f"当传感器值变化超过{args.threshold}时将触发音符")
            start_time = time.time()
            
            # 用于存储最后处理的数据行，避免重复处理相同数据
            last_processed_line = ""
            
            # 存储上一次的传感器数据，用于计算变化
            last_data = None
            
            # 主循环
            while True:
                # 读取一行数据
                if reader.serial and reader.serial.in_waiting:
                    raw_line = reader.serial.readline()
                    try:
                        line = raw_line.decode('utf-8').strip()
                        # 避免处理重复数据
                        if line and line != last_processed_line:
                            reader._parse_data(line)
                            last_processed_line = line
                            
                            # 获取当前数据
                            current_data = reader.get_current_data()
                            
                            # 如果有上一次的数据，计算变化并判断是否触发音符
                            if last_data is not None:
                                # 计算距离、电压或频率的变化
                                distance_change = abs(current_data['distance'] - last_data['distance'])
                                voltage_change = abs(current_data['voltage'] - last_data['voltage'])
                                
                                # 使用主要传感器数据作为触发判断 (可以根据实际需要选择距离或电压)
                                sensor_change = max(distance_change, voltage_change * 20)  # 放大电压变化使其与距离变化可比
                                
                                # 当变化超过阈值时触发音符
                                if sensor_change > args.threshold:
                                    # 使用传感器数据映射到音阶中的音符
                                    if current_data['frequency'] > 0:
                                        # 使用Arduino提供的频率，找到最接近的音阶音符
                                        raw_freq = current_data['frequency']
                                        freq = get_closest_note(raw_freq, args.instrument, args.scale)
                                    else:
                                        # 使用距离值映射到音阶
                                        sensor_value = current_data['distance']
                                        freq = map_value_to_note(
                                            sensor_value, 
                                            args.min_value, 
                                            args.max_value,
                                            args.instrument,
                                            args.scale
                                        )
                                    
                                    # 根据传感器数据动态调整音符持续时间
                                    # 电压值越高，持续时间越长
                                    voltage = min(max(current_data['voltage'], 0), 5)
                                    base_duration = 0.2 + (voltage / 5) * 0.8  # 0.2-1.0秒
                                    
                                    # 为不同乐器调整持续时间策略
                                    if args.instrument == 'piano':
                                        # 钢琴音符可以短一些
                                        duration = min(base_duration, 0.8)
                                    elif args.instrument in ['flute', 'violin']:
                                        # 管弦乐器需要更长的持续时间
                                        duration = min(base_duration * 1.5, 1.5)
                                    else:
                                        duration = min(base_duration, 1.0)
                                    
                                    # 播放音符
                                    note_name = [name for name, f in player.instrument_scales.get(args.instrument, {}).items() 
                                                if abs(f - freq) < 0.1]
                                    note_str = note_name[0] if note_name else "未知音符"
                                    print(f"触发音符: {note_str} ({freq:.2f} Hz), 持续时间 {duration:.2f}秒, 变化量: {sensor_change:.2f}")
                                    player.play_note(freq, duration, args.instrument, intensity=0.8, wait=False)
                            
                            # 更新上一次的数据
                            last_data = current_data.copy()
                            
                    except UnicodeDecodeError:
                        pass
                
                # 检查是否达到指定的持续时间
                if args.duration and (time.time() - start_time) >= args.duration:
                    break
                    
                # 增加休眠时间，减少CPU占用
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\n停止演奏")
        finally:
            # 关闭连接
            reader.disconnect()
            print(f"播放器中的声音对象数量: {len(player.sound_objects)}")
    else:
        print("无法连接到Arduino设备,请检查连接或指定正确的端口")


def arduino_play_by_rate():
    """根据Arduino传感器数据播放指定的频率"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Arduino 传感器音乐演奏')
    parser.add_argument('-p', '--port', help='串口设备路径,例如COM3(Windows)或/dev/ttyUSB0(Linux)')
    parser.add_argument('-b', '--baudrate', type=int, default=9600, help='波特率,默认9600')
    parser.add_argument('-d', '--duration', type=int, help='演奏持续时间（秒），默认持续到中断')
    parser.add_argument('-i', '--instrument', default='piano', choices=['piano', 'flute', 'violin', 'guitar', 'trumpet'], help='乐器音色选择')
    parser.add_argument('-r', '--rate', type=float, default=0.35, help='播放速率(秒),默认0.3秒一个音符')
    parser.add_argument('-m', '--max-sounds', type=int, default=100, help='最大同时存在的声音对象数量')
    args = parser.parse_args()
    
    # 创建音乐播放器实例
    player = MusicPlayer(max_sounds=args.max_sounds)
    
    # 创建Arduino读取器
    reader = ArduinoSerialReader(
        port=args.port,
        baudrate=args.baudrate
    )
    
    # 连接Arduino
    if reader.connect():
        try:
            print(f"开始根据传感器数据演奏音乐，使用{args.instrument}音色...")
            start_time = time.time()
            last_play_time = 0
            
            # 用于存储最后处理的数据行，避免重复处理相同数据
            last_processed_line = ""
            
            # 主循环
            while True:
                # 读取一行数据
                if reader.serial and reader.serial.in_waiting:
                    raw_line = reader.serial.readline()
                    try:
                        line = raw_line.decode('utf-8').strip()
                        # 避免处理重复数据
                        if line and line != last_processed_line:
                            reader._parse_data(line)
                            last_processed_line = line
                            
                            # 获取当前数据
                            data = reader.get_current_data()
                            current_time = time.time()
                            
                            # 限制播放频率
                            if current_time - last_play_time >= args.rate:
                                if data['frequency'] > 0:
                                    # 使用Arduino提供的频率
                                    freq = data['frequency']
                                else:
                                    # 或者使用距离映射到频率
                                    freq = map_to_frequency(data['distance'], 0, 100)
                                
                                # 安全处理电压值
                                voltage = min(max(data['voltage'], 0), 5)
                                
                                # 根据传感器数据动态调整音符持续时间
                                base_duration = 0.2 + (voltage / 5) * 0.8  # 0.2-1.0秒
                                
                                # 为不同乐器调整持续时间策略
                                if args.instrument == 'piano':
                                    # 钢琴音符可以短一些
                                    duration = min(base_duration, 0.8)
                                elif args.instrument in ['flute', 'violin']:
                                    # 管弦乐器需要更长的持续时间
                                    duration = min(base_duration * 1.5, 1.5)
                                else:
                                    duration = min(base_duration, 1.0)
                                
                                # 播放音符 - 使用类方法而不是全局函数
                                print(f"播放音符: 频率 {freq:.2f} Hz, 持续时间 {duration:.2f}秒")
                                player.play_note(freq, duration, args.instrument, intensity=0.8, wait=False)
                                
                                # 更新上次播放时间
                                last_play_time = current_time
                    except UnicodeDecodeError:
                        pass
                
                # 检查是否达到指定的持续时间
                if args.duration and (time.time() - start_time) >= args.duration:
                    break
                    
                # 增加休眠时间，减少CPU占用
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\n停止演奏")
        finally:
            # 关闭连接
            reader.disconnect()
            print(f"播放器中的声音对象数量: {len(player.sound_objects)}")
    else:
        print("无法连接到Arduino设备,请检查连接或指定正确的端口")

    


if __name__ == "__main__":
    arduino_play_by_rate()
    # arduino_play_by_scale()
