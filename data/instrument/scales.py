"""
存储不同乐器的音阶信息
包含各种常见音阶的频率值和相关工具函数
"""

import numpy as np

# 定义基本常量
# 中央C (C4) 的频率
C4 = 261.63

# 半音阶比例 (相邻半音之间的频率比)
SEMITONE_RATIO = 2**(1/12)  # 约为1.059463

# 各种常见的音阶定义
# C大调自然音阶 (C, D, E, F, G, A, B)
C_MAJOR_SCALE = {
    'C4': C4,
    'D4': C4 * SEMITONE_RATIO**2,
    'E4': C4 * SEMITONE_RATIO**4,
    'F4': C4 * SEMITONE_RATIO**5,
    'G4': C4 * SEMITONE_RATIO**7,
    'A4': C4 * SEMITONE_RATIO**9,
    'B4': C4 * SEMITONE_RATIO**11,
    'C5': C4 * 2,
}

# A小调自然音阶 (A, B, C, D, E, F, G)
A_MINOR_SCALE = {
    'A3': C4 * SEMITONE_RATIO**(-3),
    'B3': C4 * SEMITONE_RATIO**(-1),
    'C4': C4,
    'D4': C4 * SEMITONE_RATIO**2,
    'E4': C4 * SEMITONE_RATIO**4,
    'F4': C4 * SEMITONE_RATIO**5,
    'G4': C4 * SEMITONE_RATIO**7,
    'A4': C4 * SEMITONE_RATIO**9,
}

# 五声音阶 (C, D, E, G, A) - 中国传统音阶
PENTATONIC_SCALE = {
    'C4': C4,
    'D4': C4 * SEMITONE_RATIO**2,
    'E4': C4 * SEMITONE_RATIO**4,
    'G4': C4 * SEMITONE_RATIO**7,
    'A4': C4 * SEMITONE_RATIO**9,
    'C5': C4 * 2,
}

# 不同八度的音阶生成
def generate_scale_octaves(base_scale, octave_range=3, base_octave=4):
    """
    从基础音阶生成多个八度的完整音阶
    
    参数:
        base_scale: 基础音阶字典
        octave_range: 需要生成的八度数量
        base_octave: 基础音阶的八度
        
    返回:
        扩展后的多八度音阶字典
    """
    full_scale = {}
    # 提取没有八度信息的音符名称
    base_notes = {}
    for note, freq in base_scale.items():
        note_name = note[:-1]  # 移除最后一个字符(八度数字)
        octave = int(note[-1])
        base_notes[note_name] = {'freq': freq, 'octave': octave}
    
    # 生成多个八度
    for octave_offset in range(-octave_range//2, octave_range//2 + 1):
        target_octave = base_octave + octave_offset
        for note_name, data in base_notes.items():
            # 计算频率偏移 (每增加一个八度，频率翻倍)
            octave_diff = target_octave - data['octave']
            new_freq = data['freq'] * (2 ** octave_diff)
            full_scale[f"{note_name}{target_octave}"] = new_freq
    
    return full_scale

# 为不同乐器生成最适合的音阶
# 钢琴 - 使用较宽的音域
PIANO_SCALE = generate_scale_octaves(C_MAJOR_SCALE, octave_range=5, base_octave=4)

# 小提琴 - 主要使用中高音域
VIOLIN_SCALE = generate_scale_octaves(A_MINOR_SCALE, octave_range=3, base_octave=4)

# 长笛 - 使用中高音域
FLUTE_SCALE = generate_scale_octaves(C_MAJOR_SCALE, octave_range=3, base_octave=5)

# 吉他 - 使用中低音域
GUITAR_SCALE = generate_scale_octaves(C_MAJOR_SCALE, octave_range=3, base_octave=3)

# 小号 - 使用中音域
TRUMPET_SCALE = generate_scale_octaves(C_MAJOR_SCALE, octave_range=2, base_octave=4)

# 传统五声音阶 - 适合所有乐器
TRADITIONAL_SCALE = generate_scale_octaves(PENTATONIC_SCALE, octave_range=4, base_octave=4)

# 乐器音阶字典 - 用于根据乐器名称获取对应音阶
INSTRUMENT_SCALES = {
    'piano': PIANO_SCALE,
    'violin': VIOLIN_SCALE,
    'flute': FLUTE_SCALE,
    'guitar': GUITAR_SCALE,
    'trumpet': TRUMPET_SCALE,
}

def get_closest_note(frequency, instrument='piano', scale_type='default'):
    """
    根据给定频率找到最接近的音符
    
    参数:
        frequency: 目标频率
        instrument: 乐器名称
        scale_type: 音阶类型 ('default'使用乐器默认音阶, 'pentatonic'使用五声音阶)
        
    返回:
        最接近的音符频率
    """
    if scale_type == 'pentatonic':
        scale = TRADITIONAL_SCALE
    else:
        scale = INSTRUMENT_SCALES.get(instrument, PIANO_SCALE)
    
    # 查找最接近的音符
    closest_freq = None
    min_diff = float('inf')
    
    for note_freq in scale.values():
        diff = abs(frequency - note_freq)
        if diff < min_diff:
            min_diff = diff
            closest_freq = note_freq
    
    return closest_freq

def map_value_to_note(value, min_value, max_value, instrument='piano', scale_type='default'):
    """
    将传感器值映射到音阶中的某个音符
    
    参数:
        value: 传感器读数
        min_value: 传感器最小值
        max_value: 传感器最大值
        instrument: 乐器名称
        scale_type: 音阶类型
        
    返回:
        对应的音符频率
    """
    if scale_type == 'pentatonic':
        scale = TRADITIONAL_SCALE
    else:
        scale = INSTRUMENT_SCALES.get(instrument, PIANO_SCALE)
    
    # 将传感器值规范化为0-1之间
    normalized = (value - min_value) / (max_value - min_value)
    normalized = max(0, min(normalized, 1))  # 确保在0-1范围内
    
    # 将0-1映射到音阶索引
    note_freqs = list(scale.values())
    note_freqs.sort()  # 确保频率从低到高排序
    
    index = int(normalized * (len(note_freqs) - 1))
    return note_freqs[index] 