import numpy as np
import pygame
import time
from eeg_music.audio.generate_envelope import adsr_envelope, piano_envelope, tremolo_envelope

def generate_instrument_wave(freq, duration=1.0, instrument="piano", intensity=0.8):
    """
    生成各种乐器的波形
    
    参数:
        freq: 频率 (Hz)
        duration: 持续时间 (秒)
        instrument: 乐器类型 ('piano', 'flute', 'violin', 'guitar', 'trumpet')
        intensity: 强度参数 (0-1)，影响音色特性
        
    返回:
        波形数据 (16位整数数组)
    """
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # 基础波形（基频）
    wave = np.sin(2 * np.pi * freq * t)
    
    # 根据乐器类型叠加谐波和应用包络
    if instrument == "piano":
        # 钢琴音色：丰富的谐波 + 指数衰减
        # 降低高频谐波的强度，减少尖锐刺耳感
        wave += 0.5 * np.sin(2 * np.pi * 2 * freq * t)  # 第一泛音
        wave += 0.2 * np.sin(2 * np.pi * 3 * freq * t)  # 第二泛音强度
        wave += 0.08 * np.sin(2 * np.pi * 4 * freq * t)  # 第三泛音强度
        wave += 0.03 * np.sin(2 * np.pi * 5 * freq * t)  # 第四泛音强度
        
        # 添加更柔和的不和谐泛音
        wave += 0.01 * np.sin(2 * np.pi * (2*freq+1.5) * t)
        
        # 添加低频泛音增加温暖感
        wave += 0.15 * np.sin(2 * np.pi * 0.5 * freq * t)
        
        # 使用专用钢琴包络
        attack_speed = 8.0 + 4.0 * intensity  # 高强度时起音更快
        decay_speed = 2.0 + 3.0 * (1-intensity)  # 低强度时衰减更快
        envelope = piano_envelope(t, duration, attack_speed, decay_speed)
        
        # 对高频成分应用额外的衰减
        high_freq_fade = np.exp(-4.0 * t/duration)  # 高频衰减比整体更快
        high_freq_comp = 0.08 * np.sin(2 * np.pi * 6 * freq * t) + 0.04 * np.sin(2 * np.pi * 7 * freq * t)
        wave += high_freq_comp * high_freq_fade
        
    elif instrument == "flute":
        # 长笛音色：以基频为主，少量谐波，丰富的气声
        wave += 0.3 * np.sin(2 * np.pi * 2 * freq * t)
        wave += 0.1 * np.sin(2 * np.pi * 3 * freq * t)
        wave += 0.02 * np.sin(2 * np.pi * 4 * freq * t)
        
        # 添加气息噪声 (强度随intensity变化)
        noise = np.random.normal(0, 0.01 + 0.02 * (1-intensity), len(t))
        wave += noise
        
        # 添加轻微的频率颤音
        vibrato_amount = 0.005 * (0.5 + intensity)  # 强度影响颤音深度
        vibrato_rate = 4.5 + intensity * 1.5  # 强度影响颤音速度
        vibrato = vibrato_amount * np.sin(2 * np.pi * vibrato_rate * t)
        wave_vibrato = np.sin(2 * np.pi * freq * (t + vibrato))
        wave = 0.7 * wave + 0.3 * wave_vibrato
        
        # 使用ADSR包络
        attack_time = 0.12 * (2-intensity)  # 强度越大，起音越快
        decay_time = 0.05
        sustain_level = 0.7 + 0.2 * intensity
        release_time = 0.1 * (1 + 0.5 * (1-intensity))
        envelope = adsr_envelope(t, attack_time, decay_time, sustain_level, release_time, duration, 'sine')
        
    elif instrument == "violin":
        # 小提琴音色：丰富的谐波和持续的颤音
        wave += 0.5 * np.sin(2 * np.pi * 2 * freq * t)
        wave += 0.4 * np.sin(2 * np.pi * 3 * freq * t)
        wave += 0.3 * np.sin(2 * np.pi * 4 * freq * t)
        wave += 0.15 * np.sin(2 * np.pi * 5 * freq * t)
        wave += 0.08 * np.sin(2 * np.pi * 6 * freq * t)
        
        # 添加弓弦摩擦声的随机调制
        noise_mod = 0.05 * np.random.normal(0, 1, len(t))
        bow_noise = 0.04 * (1 + np.sin(2 * np.pi * freq * t)) * noise_mod
        wave += bow_noise
        
        # 基础ADSR包络
        attack_time = 0.15 * (2-intensity)
        decay_time = 0.1
        sustain_level = 0.9 * intensity
        release_time = 0.25
        base_envelope = adsr_envelope(t, attack_time, decay_time, sustain_level, release_time, duration, 'logarithmic')
        
        # 添加颤音效果
        tremolo_rate = 5.0 + intensity * 2.0  # 颤音速率
        tremolo_depth = 0.15 + 0.1 * intensity  # 颤音深度
        envelope = tremolo_envelope(t, base_envelope, tremolo_rate, tremolo_depth)
        
    elif instrument == "guitar":
        # 吉他音色：丰富的谐波，快速起音，长衰减
        wave += 0.5 * np.sin(2 * np.pi * 2 * freq * t)
        wave += 0.4 * np.sin(2 * np.pi * 3 * freq * t)
        wave += 0.2 * np.sin(2 * np.pi * 4 * freq * t)
        wave += 0.05 * np.sin(2 * np.pi * 5 * freq * t)
        
        # 添加拨弦瞬态特性
        pluck_noise = 0.15 * np.exp(-30 * t) * np.random.normal(0, 1, len(t))
        wave += pluck_noise
        
        # 使用ADSR包络
        attack_time = 0.01  # 快速起音
        decay_time = 0.1
        sustain_level = 0.3 * intensity
        release_time = 0.5
        envelope = adsr_envelope(t, attack_time, decay_time, sustain_level, release_time, duration, 'exponential')
        
    elif instrument == "trumpet":
        # 小号音色：明亮的谐波和持续音量
        wave += 0.8 * np.sin(2 * np.pi * 2 * freq * t)
        wave += 0.6 * np.sin(2 * np.pi * 3 * freq * t)
        wave += 0.4 * np.sin(2 * np.pi * 4 * freq * t)
        wave += 0.3 * np.sin(2 * np.pi * 5 * freq * t)
        wave += 0.2 * np.sin(2 * np.pi * 6 * freq * t)
        wave += 0.1 * np.sin(2 * np.pi * 7 * freq * t)
        
        # 添加轻微的气息噪声
        breath_noise = 0.05 * np.random.normal(0, 1, len(t))
        wave += breath_noise
        
        # 添加典型的铜管乐器起音特性
        attack_time = 0.08 * (2-intensity)
        decay_time = 0.1
        sustain_level = 0.7 + 0.3 * intensity
        release_time = 0.08
        envelope = adsr_envelope(t, attack_time, decay_time, sustain_level, release_time, duration, 'sine')
        
    else:
        # 默认简单包络
        envelope = np.ones_like(t)
    
    # 应用包络
    wave *= envelope
    
    # 应用整体强度
    wave *= intensity
    
    # 防止溢出
    wave = wave / (np.max(np.abs(wave)) + 1e-6)  # 添加小值避免除零
    return np.int16(wave * 32767)

def play_note(freq, duration=0.5, instrument="piano", intensity=0.8, wait=True):
    """播放单个音符
    
    参数:
        freq: 频率 (Hz)
        duration: 持续时间 (秒)
        instrument: 乐器类型
        intensity: 强度参数 (0-1)
        wait: 是否等待音符播放完毕
    """
    samples = generate_instrument_wave(freq=freq, duration=duration, instrument=instrument, intensity=intensity)
    sound = pygame.sndarray.make_sound(samples)
    sound.play()
    if wait:
        # 等待音符播放完毕
        pygame.time.wait(int(duration * 1000))

# 初始化Pygame音频
if not pygame.mixer.get_init():
    pygame.mixer.init(frequency=44100, size=-16, channels=1)

