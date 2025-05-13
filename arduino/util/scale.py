
def map_to_frequency(value, min_value=0, max_value=100, min_freq=220, max_freq=880):
    """将传感器值映射到频率范围"""
    # 限制输入值在指定范围内
    value = max(min_value, min(value, max_value))
    # 线性映射
    return min_freq + (value - min_value) * (max_freq - min_freq) / (max_value - min_value)
