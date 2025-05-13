import numpy as np

def adsr_envelope(t, attack_time, decay_time, sustain_level, release_time, duration=1.0, curve_type='linear'):
    """创建一个ADSR包络
    
    参数:
        t: 时间轴数组
        attack_time: 起音时间
        decay_time: 衰减时间
        sustain_level: 持续音量级别 (0到1)
        release_time: 释音时间
        duration: 总持续时间
        curve_type: 曲线类型 ('linear', 'exponential', 'logarithmic', 'sine')
    
    返回:
        envelope: 包络数组
    """
    envelope = np.zeros_like(t)
    total_time = duration

    # 根据曲线类型选择转换函数
    if curve_type == 'exponential':
        # 指数曲线，更符合自然乐器衰减特性
        curve_func = lambda x: 1 - np.exp(-5 * x)
        inv_curve_func = lambda x: np.exp(-5 * (1 - x)) 
    elif curve_type == 'logarithmic':
        # 对数曲线，起音快，衰减慢
        curve_func = lambda x: np.log(x * 9 + 1) / np.log(10)
        inv_curve_func = lambda x: (np.power(10, x) - 1) / 9
    elif curve_type == 'sine':
        # 正弦曲线，更平滑的过渡
        curve_func = lambda x: np.sin(x * np.pi/2)
        inv_curve_func = lambda x: np.sin((1-x) * np.pi/2)
    else:  # 'linear'
        # 线性曲线
        curve_func = lambda x: x
        inv_curve_func = lambda x: 1 - x

    # Attack
    attack_mask = t <= attack_time
    if np.any(attack_mask) and attack_time > 0:
        # 应用选定的曲线类型
        envelope[attack_mask] = curve_func(t[attack_mask] / attack_time)

    # Decay
    decay_mask = (t > attack_time) & (t <= attack_time + decay_time)
    if np.any(decay_mask) and decay_time > 0:
        # 从1衰减到sustain_level
        decay_progress = (t[decay_mask] - attack_time) / decay_time
        envelope[decay_mask] = 1.0 - (1.0 - sustain_level) * curve_func(decay_progress)

    # Sustain
    sustain_mask = (t > attack_time + decay_time) & (t <= total_time - release_time)
    envelope[sustain_mask] = sustain_level

    # Release
    release_mask = (t > total_time - release_time) & (t <= total_time)
    if np.any(release_mask) and release_time > 0:
        release_progress = (t[release_mask] - (total_time - release_time)) / release_time
        envelope[release_mask] = sustain_level * (1.0 - curve_func(release_progress))

    # 确保包络值在0到1之间
    envelope = np.clip(envelope, 0, 1)
    
    return envelope

def piano_envelope(t, duration=1.0, attack_speed=5.0, decay_speed=2.0):
    """创建一个特别为钢琴优化的包络
    
    参数:
        t: 时间轴数组
        duration: 音符持续时间
        attack_speed: 起音速度参数 (越大起音越快)
        decay_speed: 衰减速度参数 (越大衰减越快)
        
    返回:
        envelope: 钢琴专用包络
    """
    # 钢琴的包络主要是快速的起音和缓慢的指数衰减
    attack_part = 1 - np.exp(-attack_speed * t)
    
    # 使用更自然的双重衰减模式，模拟钢琴弦的振动特性
    initial_decay = np.exp(-decay_speed * t)
    secondary_decay = np.exp(-decay_speed * 0.3 * t)  # 更慢的第二阶段衰减
    decay_part = 0.7 * initial_decay + 0.3 * secondary_decay
    
    # 组合起音和衰减
    envelope = attack_part * decay_part
    
    # 在持续时间结束前使用更长、更平滑的淡出效果
    fade_end = 0.25  # 增加淡出时间
    end_mask = t > (duration - fade_end)
    if np.any(end_mask) and fade_end > 0:
        fade_factor = (1 - (t[end_mask] - (duration - fade_end)) / fade_end) ** 2  # 使用平方函数使淡出更平滑
        envelope[end_mask] *= np.clip(fade_factor, 0, 1)
        
    return envelope

def tremolo_envelope(t, base_envelope, rate=5.0, depth=0.3):
    """在基础包络上添加颤音效果
    
    参数:
        t: 时间轴数组
        base_envelope: 基础包络
        rate: 颤音频率 (Hz)
        depth: 颤音深度 (0到1)
        
    返回:
        envelope: 带颤音的包络
    """
    # 创建颤音调制
    tremolo = 1.0 - depth * 0.5 * (1 + np.sin(2 * np.pi * rate * t))
    
    # 应用到基础包络
    modulated_envelope = base_envelope * tremolo
    
    return modulated_envelope

