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
        instrument: 乐器类型 ('piano', 'flute', 'violin', 'guitar', 'trumpet', 'guzheng')
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
        # 让谐波强度受intensity影响
        wave += 0.5 * intensity * np.sin(2 * np.pi * 2 * freq * t)
        wave += 0.4 * intensity * np.sin(2 * np.pi * 3 * freq * t)
        wave += 0.2 * intensity * np.sin(2 * np.pi * 4 * freq * t)
        wave += 0.05 * intensity * np.sin(2 * np.pi * 5 * freq * t)
        
        # 添加拨弦瞬态特性，也受intensity影响
        pluck_noise = 0.15 * intensity * np.exp(-30 * t) * np.random.normal(0, 1, len(t))
        wave += pluck_noise
        
        # 使用ADSR包络
        attack_time = 0.01 * (2-intensity)  # intensity影响起音速度
        decay_time = 0.1
        sustain_level = 0.3 * intensity
        release_time = 0.5 * (2-intensity)  # intensity影响释音时间
        envelope = adsr_envelope(t, attack_time, decay_time, sustain_level, release_time, duration, 'exponential')
        
    elif instrument == "trumpet":
        # 小号音色：保持音色特征但音量与钢琴相当
        
        # 计算频率衰减因子，高频时降低音量
        freq_attenuation = 1.0
        if freq > 400:  # 400Hz以上开始衰减
            freq_attenuation = max(0.4, 1.0 - (freq - 400) / 1500)  # 调整衰减曲线
        
        # 大幅降低基础谐波强度，但保持trumpet的音色比例特征
        base_volume = 0.6  # 整体音量降低到60%
        wave += 0.25 * base_volume * freq_attenuation * np.sin(2 * np.pi * 2 * freq * t)   # 第二谐波
        wave += 0.18 * base_volume * freq_attenuation * np.sin(2 * np.pi * 3 * freq * t)   # 第三谐波
        wave += 0.12 * base_volume * freq_attenuation * np.sin(2 * np.pi * 4 * freq * t)   # 第四谐波
        wave += 0.08 * base_volume * freq_attenuation * np.sin(2 * np.pi * 5 * freq * t)   # 第五谐波
        wave += 0.05 * base_volume * freq_attenuation * np.sin(2 * np.pi * 6 * freq * t)   # 第六谐波
        wave += 0.03 * base_volume * freq_attenuation * np.sin(2 * np.pi * 7 * freq * t)   # 第七谐波
        
        # 减少气息噪声
        breath_noise = 0.01 * base_volume * freq_attenuation * np.random.normal(0, 1, len(t))
        wave += breath_noise
        
        # 调整包络，降低整体音量
        attack_time = 0.08 * (2-intensity)
        decay_time = 0.1
        sustain_level = (0.4 + 0.15 * intensity) * base_volume * freq_attenuation  # 大幅降低sustain
        release_time = 0.08
        envelope = adsr_envelope(t, attack_time, decay_time, sustain_level, release_time, duration, 'sine')
        
    elif instrument == "guzheng":
        # 古筝音色：金属弦音质，丰富的泛音，特有的拨弦起音和长衰减
        # 添加丰富的泛音谱，特别强调奇次谐波（古筝特色），受intensity影响
        wave += 0.6 * intensity * np.sin(2 * np.pi * 2 * freq * t)   # 二次泛音
        wave += 0.4 * intensity * np.sin(2 * np.pi * 3 * freq * t)   # 三次泛音（较强）
        wave += 0.25 * intensity * np.sin(2 * np.pi * 4 * freq * t)  # 四次泛音
        wave += 0.3 * intensity * np.sin(2 * np.pi * 5 * freq * t)   # 五次泛音（奇次，较强）
        wave += 0.15 * intensity * np.sin(2 * np.pi * 6 * freq * t)  # 六次泛音
        wave += 0.2 * intensity * np.sin(2 * np.pi * 7 * freq * t)   # 七次泛音（奇次）
        wave += 0.1 * intensity * np.sin(2 * np.pi * 8 * freq * t)   # 八次泛音
        wave += 0.08 * intensity * np.sin(2 * np.pi * 9 * freq * t)  # 九次泛音
        
        # 添加金属弦的特有高频成分（金属质感），也受intensity影响
        metallic_freq1 = freq * 11.7  # 非整数倍泛音，产生金属感
        metallic_freq2 = freq * 13.2
        wave += 0.03 * intensity * np.sin(2 * np.pi * metallic_freq1 * t) * np.exp(-8.0 * t)
        wave += 0.02 * intensity * np.sin(2 * np.pi * metallic_freq2 * t) * np.exp(-10.0 * t)
        
        # 拨弦瞬态特性（比吉他更尖锐），受intensity影响
        pluck_transient = 0.25 * intensity * np.exp(-40 * t) * (
            np.sin(2 * np.pi * freq * 1.8 * t) +  # 轻微的音高偏移
            0.5 * np.random.normal(0, 1, len(t))   # 拨弦噪声
        )
        wave += pluck_transient
        
        # 古筝特有的弦振动调制（弦的松紧变化）
        string_modulation = 0.02 * np.sin(2 * np.pi * 0.8 * t) * np.exp(-2.0 * t)
        modulated_wave = np.sin(2 * np.pi * freq * (t + string_modulation))
        wave = 0.85 * wave + 0.15 * modulated_wave
        
        # 古筝包络：快速起音，缓慢衰减，有轻微的维持
        attack_time = 0.008 * (2-intensity)  # 非常快的起音（拨弦瞬间）
        decay_time = 0.3 + 0.2 * intensity   # 较长的衰减时间
        sustain_level = 0.15 + 0.1 * intensity  # 低持续音量
        release_time = 0.8 + 0.4 * intensity    # 很长的释放时间
        envelope = adsr_envelope(t, attack_time, decay_time, sustain_level, release_time, duration, 'exponential')
        
        # 添加古筝特有的余音效果（高频快速衰减，低频慢衰减）
        frequency_dependent_decay = np.exp(-1.5 * t/duration)  # 整体衰减
        high_freq_decay = np.exp(-6.0 * t/duration)            # 高频快速衰减
        
        # 对不同频率成分应用不同的衰减
        base_wave = wave * 0.7  # 基础成分
        high_freq_components = 0.3 * (
            0.15 * np.sin(2 * np.pi * 6 * freq * t) +
            0.1 * np.sin(2 * np.pi * 7 * freq * t) +
            0.08 * np.sin(2 * np.pi * 8 * freq * t)
        ) * high_freq_decay
        
        wave = base_wave + high_freq_components
        
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



