import pygame
import time
import sys
import os
import csv
from eeg_music.audio.generate_wave import generate_instrument_wave

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
    
    def play_note(self, freq, duration=0.5, instrument="piano", intensity=0.8, wait=True):
        """播放单个音符
        
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
    
    def play_csv_file(self, csv_file_path):
        """
        播放CSV文件中的音符
        csv_data = {
            'timestamp': relative_time,
            'freq': freq,
            'duration': duration,
            'instrument': instrument,
            'intensity': intensity,
            'note_name': note_name,
            'session_name': self.session_name
            **arduino_data
            **mindwave_data
        }
        """
        with open(csv_file_path, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                freq = float(row['freq'])
                duration = float(row['duration'])
                instrument = row['instrument']
                intensity = float(row['intensity'])
                self.play_note(freq, duration, instrument, intensity, wait=False)
                time.sleep(duration)
    
    
    def play_note_by_name(self, note_name, duration=0.5, instrument="piano", intensity=0.8, wait=True):
        """按音符名称播放音符
        
        参数:
            note_name: 音符名称 (例如 'C4', 'A3' 等)
            duration: 持续时间 (秒)
            instrument: 乐器类型
            intensity: 音量强度 (0-1)
            wait: 是否等待音符播放完毕
        """
        if not self.scales_available:
            print("错误: 无法按音符名称播放，音阶数据不可用")
            return
            
        # 查找音符频率
        scale = self.instrument_scales.get(instrument, self.traditional_scale)
        if note_name in scale:
            freq = scale[note_name]
            self.play_note(freq, duration, instrument, intensity, wait)
        else:
            print(f"错误: 未找到音符 {note_name}")
            
    def play_sequence(self, notes, instrument="piano"):
        """播放一系列音符
        
        参数:
            notes: 音符列表，每个元素为(频率, 持续时间)元组
            instrument: 乐器类型
        """
        for freq, duration in notes:
            self.play_note(freq, duration, instrument)
            
    def play_sequence_by_name(self, notes, instrument="piano"):
        """按音符名称播放一系列音符
        
        参数:
            notes: 音符列表，每个元素为(音符名称, 持续时间)元组
            instrument: 乐器类型
        """
        if not self.scales_available:
            print("错误: 无法按音符名称播放，音阶数据不可用")
            return
            
        for note_name, duration in notes:
            self.play_note_by_name(note_name, duration, instrument)
            
    def play_little_star(self, instrument="piano"):
        """播放小星星旋律"""
        if self.scales_available:
            # 使用音符名称版本
            melody = [
                ('C4', 0.5), ('C4', 0.5), ('G4', 0.5), ('G4', 0.5),
                ('A4', 0.5), ('A4', 0.5), ('G4', 1.0),
                ('F4', 0.5), ('F4', 0.5), ('E4', 0.5), ('E4', 0.5),
                ('D4', 0.5), ('D4', 0.5), ('C4', 1.0)
            ]
            print(f"播放小星星 (使用{instrument}音色)")
            self.play_sequence_by_name(melody, instrument)
        else:
            # 小星星旋律对应的频率 (C C G G A A G, F F E E D D C)
            # 中央C（C4）的频率是261.63Hz
            C4 = 261.63
            D4 = 293.66
            E4 = 329.63
            F4 = 349.23
            G4 = 392.00
            A4 = 440.00
            
            # 小星星旋律
            melody = [
                (C4, 0.5), (C4, 0.5), (G4, 0.5), (G4, 0.5),
                (A4, 0.5), (A4, 0.5), (G4, 1.0),
                (F4, 0.5), (F4, 0.5), (E4, 0.5), (E4, 0.5),
                (D4, 0.5), (D4, 0.5), (C4, 1.0)
            ]
            
            print(f"播放小星星 (使用{instrument}音色)")
            self.play_sequence(melody, instrument)

