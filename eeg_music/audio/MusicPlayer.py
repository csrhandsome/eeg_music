import pygame
import time
import sys
import os
import csv
import numpy as np
from eeg_music.audio.generate_wave import generate_instrument_wave
import random
class MusicPlayer:
    """音乐播放器类，管理声音对象的创建和生命周期"""
    
    def __init__(self, max_sounds=100):
        """初始化音乐播放器
        
        参数:
            max_sounds: 最大同时存在的声音对象数量
        """
        self.sound_objects = []  # 存储声音对象
        self.MAX_SOUNDS = max_sounds
        
        # 确保pygame初始化
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
            
        # 导入音阶数据
        try:
            from eeg_music.audio.scales import INSTRUMENT_SCALES, TRADITIONAL_SCALE
            self.instrument_scales = INSTRUMENT_SCALES
            self.traditional_scale = TRADITIONAL_SCALE
            self.scales_available = True
        except ImportError:
            print("警告: 未找到音阶数据，将使用默认频率")
            self.scales_available = False
            self.instrument_scales = {}
            self.traditional_scale = {}
    
    def play_generated_note(self, freq, duration=0.5, instrument="piano", intensity=0.8, wait=True):
        """播放单个电子合成器音符
        
        参数:
            freq: 频率 (Hz)
            duration: 持续时间 (秒)
            instrument: 乐器类型
            intensity: 音量强度 (0-1)
            wait: 是否等待音符播放完毕
        """
        # 限制持续时间在合理范围内
        duration = min(max(duration, 0.1), 3.0)
        
        # 生成波形
        samples = generate_instrument_wave(freq=freq, duration=duration, instrument=instrument, intensity=intensity)
        sound = pygame.sndarray.make_sound(samples)
        
        # 保持对声音对象的引用
        self.sound_objects.append(sound)
        
        # 如果超过最大数量限制，只保留最新的一部分
        if len(self.sound_objects) > self.MAX_SOUNDS:
            self.sound_objects = self.sound_objects[-self.MAX_SOUNDS:]
        
        # 播放声音
        sound.play()
        
        if wait:
            # 等待音符播放完毕
            pygame.time.wait(int(duration * 1000))
    
    def play_wav_note(self, freq, duration=0.5, instrument="piano", intensity=0.8, wait=True, playback_mode="truncate"):
        """播放WAV文件中的音符
        
        参数:
            freq: 频率标识符 (用于构建文件路径)
            duration: 期望的播放持续时间 (秒)
            instrument: 乐器类型
            intensity: 音量强度 (0-1)
            wait: 是否等待播放完毕
            playback_mode: 播放模式
                - "truncate": 完整播放但在duration时间点停止 (推荐，保持音质)
                - "speedup": 在duration时间内快进播放完整个4秒文件 (会改变音调)
        """
        wav_file_path = f"data/instruments/{instrument}/{freq}.wav"
        try:
            # 加载WAV文件
            sound = pygame.mixer.Sound(wav_file_path)
            
            # 获取原始文件长度
            original_length = sound.get_length()  # 应该是约4秒
            
            if playback_mode == "speedup" and duration < original_length:
                # 模式1: 变速播放 - 在duration时间内播放完整个文件
                # 使用numpy进行音频重采样实现变速
                try:
                    # 获取原始音频数据
                    raw_array = pygame.sndarray.array(sound)
                    
                    # 计算变速比例
                    speed_factor = original_length / duration
                    
                    # 如果是立体声，需要处理两个声道
                    if len(raw_array.shape) == 2:
                        # 立体声
                        new_length = int(len(raw_array) / speed_factor)
                        resampled_left = np.interp(
                            np.linspace(0, len(raw_array) - 1, new_length),
                            np.arange(len(raw_array)),
                            raw_array[:, 0]
                        )
                        resampled_right = np.interp(
                            np.linspace(0, len(raw_array) - 1, new_length),
                            np.arange(len(raw_array)),
                            raw_array[:, 1]
                        )
                        resampled_array = np.column_stack((resampled_left, resampled_right))
                    else:
                        # 单声道
                        new_length = int(len(raw_array) / speed_factor)
                        resampled_array = np.interp(
                            np.linspace(0, len(raw_array) - 1, new_length),
                            np.arange(len(raw_array)),
                            raw_array
                        )
                    
                    # 确保数据类型匹配
                    resampled_array = resampled_array.astype(raw_array.dtype)
                    
                    # 创建新的Sound对象
                    sound = pygame.sndarray.make_sound(resampled_array)
                    actual_duration = duration
                    
                    # print(f"变速播放: 原长度 {original_length:.2f}秒 -> 目标长度 {duration:.2f}秒 (速度倍数: {speed_factor:.2f})")
                    
                except Exception as e:
                    print(f"变速处理失败，使用截断模式: {e}")
                    playback_mode = "truncate"
            
            if playback_mode == "truncate":
                # 模式2: 截断播放 - 完整播放但在duration时间点停止
                maxtime_ms = min(int(duration * 1000), int(original_length * 1000))
                actual_duration = min(duration, original_length)
                # print(f"截断播放: 原长度 {original_length:.2f}秒, 播放 {actual_duration:.2f}秒")
            else:
                # speedup模式成功，使用完整的duration
                maxtime_ms = int(duration * 1000)
                actual_duration = duration
            
            # 设置音量强度
            sound.set_volume(min(max(intensity, 0.0), 1.0))
            
            # 播放声音
            if playback_mode == "truncate":
                channel = sound.play(maxtime=maxtime_ms)
            else:
                channel = sound.play()
            
            if wait:
                # 等待实际播放时间
                pygame.time.wait(int(actual_duration * 1000))
            
            # 保持对声音对象的引用，防止被垃圾回收
            self.sound_objects.append(sound)
            
            # 限制声音对象数量
            if len(self.sound_objects) > self.MAX_SOUNDS:
                self.sound_objects = self.sound_objects[-self.MAX_SOUNDS:]
                
            # print(f"播放WAV音符: {wav_file_path}, 强度: {intensity:.2f}, 实际持续时间: {actual_duration:.2f}秒")
            
        except FileNotFoundError:
            print(f"错误: 找不到文件 {wav_file_path}")
            return
        except Exception as e:
            print(f"播放WAV文件时出错: {e}")
            return
    
    def play_csv_file(self, csv_file_path, data_callback=None):
        """
        播放CSV文件中的音符,支持可视化数据回调
        
        参数:
            csv_file_path: CSV文件路径
            data_callback: 可选的回调函数，用于发送可视化数据
                          回调函数签名: callback(data_dict)
        
        CSV格式应包含以下列:
        timestamp, freq, duration, instrument, intensity, note_name, session_name, 
        distance, scale, note, potentiometer, rotary_potentiometer, button_state
        """
        print(f"开始播放CSV文件: {csv_file_path}")
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                start_time = time.time()
                last_timestamp = 0
                
                for row in reader:
                    try:
                        # 解析音符数据
                        freq = float(row.get('freq', 0))
                        duration = float(row.get('duration', 0.5))
                        instrument = row.get('instrument', 'piano')
                        intensity = float(row.get('intensity', 0.8))
                        
                        # 解析时间戳，计算相对延迟
                        current_timestamp = float(row.get('timestamp', 0))
                        if last_timestamp > 0:
                            wait_time = current_timestamp - last_timestamp
                            if wait_time > 0:
                                time.sleep(min(wait_time, 2.0))  # 最大等待2秒
                        
                        # 播放音符
                        if freq > 0:
                            self.play_wav_note(freq, duration, instrument, intensity, wait=False)
                            #print(f"播放音符: 频率 {freq:.2f} Hz, 持续时间 {duration:.2f}秒, 乐器 {instrument}")
                            
                            # 如果提供了回调函数，发送可视化数据
                            if data_callback:
                                # 构造与Arduino数据兼容的数据包
                                visualization_data = {
                                    'freq': freq,
                                    'scale': row.get('scale', 'C Major'),
                                    'note': int(row.get('note', 0)),
                                    'distance': float(row.get('distance', 25)),
                                    'potentiometer': float(row.get('potentiometer', 2.5)),
                                    'rotary_potentiometer': row.get('rotary_potentiometer', '2.5'),
                                    'button_state': int(row.get('button_state', 0)),
                                    'timestamp': time.time(),
                                    # 标记这是回放数据
                                    'playback_mode': True,
                                    'playback_file': csv_file_path,
                                    'mood': int(row.get('mood', 0))
                                }
                                data_callback(visualization_data)
                        
                        last_timestamp = current_timestamp
                    
                    except (ValueError, KeyError) as e:
                        print(f"跳过无效行: {e}")
                        continue
                        
        except FileNotFoundError:
            print(f"错误: 找不到文件 {csv_file_path}")
        except Exception as e:
            print(f"播放CSV文件时出错: {e}")
        
        print("CSV文件播放完毕")
    
    def play_note(self, freq, duration=0.5, instrument="piano", intensity=0.8, wait=True, playback_mode="truncate"):
        """尝试播放音符,优先使用WAV文件,如果文件不存在则使用生成的音符
        
        参数:
            freq: 频率 (Hz) 或频率标识符
            duration: 持续时间 (秒)
            instrument: 乐器类型
            intensity: 音量强度 (0-1)
            wait: 是否等待音符播放完毕
            playback_mode: WAV播放模式 ("truncate" 或 "speedup")
        """
        # 直接检查文件是否存在，避免嵌套异常处理
        wav_file_path = f"data/instruments/{instrument}/{freq}.wav"
        
        if os.path.exists(wav_file_path):
            self.play_wav_note(freq, duration, instrument, intensity, wait, playback_mode)
            return
        else:
            # 文件不存在，直接使用生成音符
            print(f'play generated note: {freq}, {duration}, {instrument}, {intensity}')
            self.play_generated_note(freq, duration, instrument, intensity, wait)
            

