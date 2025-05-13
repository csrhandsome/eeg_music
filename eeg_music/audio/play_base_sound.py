import pygame
import numpy as np

def play_note(base_file, target_freq):
    # 加载基础采样（如C4.wav）
    base_sound = pygame.mixer.Sound(base_file)
    base_samples = pygame.sndarray.samples(base_sound)
    sample_rate = 44100
    
    # 计算原始频率（假设采样是C4=261.63Hz）
    base_freq = 261.63
    speed_factor = target_freq / base_freq
    
    # 变速（通过插值调整采样长度）
    old_length = len(base_samples)
    new_length = int(old_length / speed_factor)
    new_samples = np.interp(
        np.linspace(0, old_length, new_length),
        np.arange(old_length),
        base_samples
    )
    
    # 播放
    sound = pygame.sndarray.make_sound(new_samples.astype(np.int16))
    sound.play()
    pygame.time.wait(int(sound.get_length() * 1000))

