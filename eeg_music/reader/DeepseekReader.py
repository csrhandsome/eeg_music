import time
import json
import re
import random
from datetime import datetime
from openai import OpenAI

class DeepseekReader:
    """
    DeepSeek AI Reader - 通过AI对话生成音乐数据
    可以发送消息给DeepSeek AI并接收符合音乐格式的响应
    """
    
    def __init__(self, api_key="sk-eb0ed891cd094d738204216a561fcd6d", session_name="ai_music"):
        """
        初始化DeepSeek读取器
        
        参数:
            api_key: DeepSeek API密钥
            session_name: 会话名称
        """
        self.api_key = api_key
        self.session_name = session_name
        self.client = OpenAI(
            api_key=api_key, 
            base_url="https://api.deepseek.com"
        )
        
        # 音乐数据相关
        self.music_data_buffer = []
        self.session_start_time = time.time()
        
        # 当前音乐状态
        self.current_data = {
            'duration': 0.8,
            'freq': 440.0,
            'instrument': 'piano',
            'intensity': 0.8,
            'note_name': '',
            'session_name': session_name,
            'timestamp': 0.0
        }
        
        # 预定义的音符频率映射
        self.note_frequencies = {
            'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13,
            'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00,
            'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88,
            'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25,
            'E5': 659.25, 'F5': 698.46, 'F#5': 739.99, 'G5': 783.99,
            'G#5': 830.61, 'A5': 880.00, 'A#5': 932.33, 'B5': 987.77
        }
        
        # 乐器选项
        self.instruments = ['piano', 'flute', 'violin', 'guitar', 'trumpet']
        
        print(f"DeepSeek Reader 初始化完成，会话名称: {session_name}")
    
    def connect(self):
        """
        测试与DeepSeek API的连接
        """
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",# "deepseek-reasoner"为R1模型
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Hello, are you ready?"},
                ],
                stream=False
            )
            print("DeepSeek API 连接成功")
            return True
        except Exception as e:
            print(f"连接DeepSeek API失败: {e}")
            return False
    
    def send_message(self, user_message):
        """
        发送消息给DeepSeek AI，请求生成音乐数据
        
        参数:
            user_message: 用户消息
            music_style: 音乐风格 (peaceful, energetic, melancholic, joyful)
            tempo: 节奏 (slow, medium, fast)
        
        返回:
            AI的响应文本
        """
        try:
            # 构建系统提示，要求AI生成音乐数据
            system_prompt = f"""你是一个专业的音乐生成助手。用户会给你描述或要求，你需要根据内容生成一个完整的音乐片段。

重要要求：
1. 必须生成至少100个音符的完整序列，创造一个有意义的音乐片段
2. 音符之间要有音乐逻辑性，形成旋律线条
3. 根据用户描述的情感或风格调整音符选择
4. 每个音符包含以下信息：
   - 音符名称 (C4, C#4, D4, D#4, E4, F4, F#4, G4, G#4, A4, A#4, B4, C5, C#5, D5, D#5, E5, F5, F#5, G5, G#5, A5, A#5, B5等)
   - 持续时间 (0.3-2.0秒之间的小数,钢琴在0.8左右,弦乐器在1.5左右,管乐器在1.0左右)
   - 乐器 (piano, flute, violin, guitar, trumpet之一)
   - 强度 (0.1-1.0之间的小数)
   - 时间戳 (从0.0开始，表示该音符开始播放的时间点，单位为秒)

时间戳说明：
- 时间戳决定了音符在音乐中的播放时间点，是音乐节奏的关键
- 时间戳的间隔通常为0.3-0.6秒,根据情绪而定，悲伤的可能间隔更长，欢快的可能间隔更短

输出格式要求：
- 必须使用以下严格格式，每行一个音符
- NOTE: [音符名称] [持续时间] [乐器] [强度] [时间戳]

请生成一个完整的音乐片段示例(至少100个音符):
NOTE: C4 0.8 piano 0.8 0.0
NOTE: D4 0.6 piano 0.7 0.9
NOTE: E4 0.8 piano 0.8 1.6
NOTE: F4 1.0 violin 0.6 2.5
NOTE: G4 0.7 violin 0.7 3.6
NOTE: A4 0.9 violin 0.8 4.4
NOTE: G4 0.5 piano 0.6 5.4
NOTE: F4 0.8 piano 0.7 6.0
NOTE: E4 1.2 flute 0.5 6.9
NOTE: D4 0.6 flute 0.6 8.2
NOTE: C4 1.0 piano 0.8 8.9
NOTE: E4 0.7 guitar 0.7 10.0
NOTE: G4 0.8 guitar 0.8 10.8
NOTE: C5 1.1 violin 0.9 11.7
NOTE: B4 0.6 violin 0.7 12.9
NOTE: A4 0.8 piano 0.8 13.6
NOTE: G4 0.9 piano 0.7 14.5
NOTE: F4 0.7 flute 0.6 15.5
NOTE: E4 0.8 flute 0.7 16.3
NOTE: D4 1.0 piano 0.8 17.2
NOTE: C4 1.5 piano 0.9 18.3

现在，根据用户的具体描述生成一个类似长度或更长的音符序列，确保音乐的连贯性和表现力。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False
            )
            
            ai_response = response.choices[0].message.content
            print(f"DeepSeek响应: {ai_response}")
            
            return ai_response
            
        except Exception as e:
            print(f"发送消息失败: {e}")
            return None
    
    def receive_message(self, ai_response):
        """
        解析DeepSeek AI的响应并生成音乐数据
        
        参数:
            ai_response: AI的响应文本
            
        返回:
            解析出的音乐数据列表
        """
        if not ai_response:
            return []
        
        music_data = []
        current_time = time.time() - self.session_start_time
        
        # 使用正则表达式提取NOTE行
        note_pattern = r'NOTE:\s*([A-G][#b]?\d+)\s+([\d.]+)\s+(\w+)\s+([\d.]+)\s+([\d.]+)'
        matches = re.findall(note_pattern, ai_response, re.IGNORECASE)
        
        if not matches:
            # 如果没有找到格式化的NOTE，尝试从文本中推断音乐
            print("未找到标准格式，尝试智能解析...")
            music_data = self._intelligent_parse(ai_response, current_time)
        else:
            # 解析标准格式的音符
            for i, (note_name, duration, instrument, intensity, timestamp) in enumerate(matches):
                try:
                    # 验证并转换数据
                    duration = float(duration)
                    intensity = float(intensity)
                    timestamp = float(timestamp)
                    
                    # 确保数值在合理范围内
                    duration = max(0.1, min(3.0, duration))
                    intensity = max(0.1, min(1.0, intensity))
                    timestamp = max(0.0, timestamp)  # 时间戳不能为负
                    
                    # 验证乐器
                    if instrument.lower() not in self.instruments:
                        instrument = 'piano'
                    else:
                        instrument = instrument.lower()
                    
                    # 获取频率
                    freq = self.note_frequencies.get(note_name.upper(), 440.0)
                    
                    # 创建音乐数据记录（使用AI生成的时间戳）
                    music_record = {
                        'duration': duration,
                        'freq': freq,
                        'instrument': instrument,
                        'intensity': intensity,
                        'note_name': note_name.upper(),
                        'session_name': self.session_name,
                        'timestamp': current_time + timestamp  # 加上当前会话的基准时间
                    }
                    
                    music_data.append(music_record)
                    
                except (ValueError, KeyError) as e:
                    print(f"解析音符数据失败: {e}")
                    continue
        
        # 更新当前数据为最后一个音符
        if music_data:
            self.current_data = music_data[-1].copy()
            self.music_data_buffer.extend(music_data)
        
        print(f"解析出 {len(music_data)} 个音符")
        return music_data
    
    def _intelligent_parse(self, text, current_time):
        """
        智能解析非标准格式的AI响应
        """
        music_data = []
        
        # 分析文本情感和内容，生成相应音符
        text_lower = text.lower()
        
        # 根据关键词判断情感和风格
        if any(word in text_lower for word in ['happy', 'joy', 'bright', 'cheerful']):
            notes = ['C4', 'E4', 'G4', 'C5']
            base_intensity = 0.8
        elif any(word in text_lower for word in ['sad', 'melancholy', 'dark', 'somber']):
            notes = ['A4', 'C4', 'F4', 'A4']
            base_intensity = 0.5
        elif any(word in text_lower for word in ['energetic', 'fast', 'intense', 'powerful']):
            notes = ['G4', 'B4', 'D5', 'G5']
            base_intensity = 0.9
        else:
            # 默认平和的音符
            notes = ['C4', 'D4', 'E4', 'F4', 'G4']
            base_intensity = 0.7
        
        # 生成3-5个音符
        num_notes = random.randint(3, 5)
        for i in range(num_notes):
            note_name = random.choice(notes)
            freq = self.note_frequencies.get(note_name, 440.0)
            duration = random.uniform(0.5, 1.5)
            intensity = base_intensity + random.uniform(-0.2, 0.2)
            intensity = max(0.1, min(1.0, intensity))
            
            music_record = {
                'duration': duration,
                'freq': freq,
                'instrument': random.choice(self.instruments),
                'intensity': intensity,
                'note_name': note_name,
                'session_name': self.session_name,
                'timestamp': current_time + i * 0.2
            }
            
            music_data.append(music_record)
        
        return music_data
    
    def generate_music_from_prompt(self, prompt):
        """
        根据提示生成音乐数据的完整流程
        
        参数:
            prompt: 音乐生成提示
            style: 音乐风格
            tempo: 节奏
            
        返回:
            生成的音乐数据列表
        """
        print(f"根据提示生成音乐: {prompt}")
        
        # 发送消息
        ai_response = self.send_message(prompt)
        
        if ai_response:
            # 解析响应
            return self.receive_message(ai_response)
        else:
            return []
    
    def get_session_data(self):
        """
        获取当前会话的所有音乐数据
        """
        return self.music_data_buffer.copy()
    
    def clear_session_data(self):
        """
        清空会话数据
        """
        self.music_data_buffer = []
        self.session_start_time = time.time()
        print("会话数据已清空")
    
    def save_to_csv(self, filename=None):
        """
        将生成的音乐数据保存到CSV文件
        """
        if not self.music_data_buffer:
            print("没有数据可保存")
            return
        
        if filename is None:
            filename = f"ai_music_{self.session_name}.csv"
        
        try:
            import os
            import csv
            
            # 确保目录存在
            data_dir = 'data/music_notes'
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            filepath = os.path.join(data_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['duration', 'freq', 'instrument', 'intensity', 'note_name', 'session_name', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in self.music_data_buffer:
                    writer.writerow(record)
            
            print(f"音乐数据已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"保存文件失败: {e}")
            return None


def main():
    """测试DeepseekReader"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek AI 音乐生成器测试')
    parser.add_argument('-p', '--prompt', default='Generate a peaceful melody', help='音乐生成提示')
    parser.add_argument('--save', action='store_true', help='保存生成的音乐数据到CSV文件')
    
    args = parser.parse_args()
    
    # 创建DeepSeek读取器
    reader = DeepseekReader()
    
    # 测试连接
    if not reader.connect():
        print("无法连接到DeepSeek API")
        return
    
    # 生成音乐
    music_data = reader.generate_music_from_prompt(args.prompt)
    
    if music_data:
        print(f"\n生成了 {len(music_data)} 个音符:")
        for i, note in enumerate(music_data, 1):
            print(f"{i}. {note['note_name']} - 频率: {note['freq']:.2f}Hz, 持续: {note['duration']:.2f}s, 乐器: {note['instrument']}, 强度: {note['intensity']:.2f}")
        
        # 保存到文件
        if args.save:
            reader.save_to_csv()
    else:
        print("未能生成音乐数据")


if __name__ == "__main__":
    main()
