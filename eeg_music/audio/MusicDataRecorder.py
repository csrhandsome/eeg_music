import csv
import os
import time
from datetime import datetime
import json

class MusicDataRecorder:
    """音符数据记录器,用于记录playnode音符播放数据到文件"""
    
    def __init__(self, session_name="default", save_format="csv"):
        """初始化音符数据记录器
        
        参数:
            session_name (str): 会话名称，用于文件命名
            save_format (str): 保存格式，支持 'csv', 'json'
        """
        self.session_name = session_name
        self.save_format = save_format
        self.note_data_buffer = []
        self.session_start_time = time.time()
        self.session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # 确保目录存在
        self.data_dir = os.path.join('data', 'music_notes')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def record_note(self, freq, duration, instrument="piano", intensity=0.8, 
                   note_name=None, arduino_data=None, mindwave_data=None):
        """记录一个音符的播放数据
        
        参数:
            frequency (float): 音符频率 (Hz)
            duration (float): 持续时间 (秒)
            instrument (str): 乐器类型
            intensity (float): 音量强度 (0-1)
            note_name (str): 音符名称 (如 'C4', 'A3')
            sensor_data (dict): 传感器数据 (可选)
            brain_data (dict): 脑电波数据 (可选)
        """
        current_time = time.time()
        relative_time = current_time - self.session_start_time
        
        note_record = {
            'timestamp': relative_time,
            'freq': freq,
            'duration': duration,
            'instrument': instrument,
            'intensity': intensity,
            'note_name': note_name,
            'session_name': self.session_name
        }
        
        # 添加传感器数据 这个可能已经变成上面的东西了，可能不需要了
        if arduino_data:
            note_record.update(arduino_data)
        
        # 添加脑电波数据
        if mindwave_data:
            note_record.update(mindwave_data)
        
        self.note_data_buffer.append(note_record)
        
        # # 打印记录信息
        # print(f"记录音符: {note_name or '未知'} ({frequency:.2f}Hz), "
        #       f"持续{duration:.2f}s, 乐器:{instrument}")
    
    def save_to_file(self, auto_save_threshold=100):
        """保存数据到文件
        
        参数:
            auto_save_threshold (int): 自动保存的缓冲区大小阈值
        """
        if not self.note_data_buffer:
            return
        
        filename = f"music_notes_{self.session_timestamp}_{self.session_name}"
        
        if self.save_format == "csv":
            self._save_to_csv(filename)
        elif self.save_format == "json":
            self._save_to_json(filename)
        else:
            print(f"不支持的保存格式: {self.save_format}")
            return
        
        # 自动保存后清空缓冲区
        if len(self.note_data_buffer) >= auto_save_threshold:
            self.note_data_buffer = []
    
    def _save_to_csv(self, filename):
        """保存为CSV格式"""
        filepath = os.path.join(self.data_dir, f"{filename}.csv")
        
        try:
            # 获取所有字段名
            all_fields = set()
            for record in self.note_data_buffer:
                all_fields.update(record.keys())
            
            fieldnames = sorted(list(all_fields))
            
            # 检查文件是否存在，决定是否写入头部
            file_exists = os.path.exists(filepath)
            
            with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # 如果文件不存在，写入头部
                if not file_exists:
                    writer.writeheader()
                
                # 写入数据
                for record in self.note_data_buffer:
                    writer.writerow(record)
            
            print(f"音符数据已保存到: {filepath} ({len(self.note_data_buffer)} 条记录)")
            
        except Exception as e:
            print(f"保存CSV文件时出错: {e}")
    
    def _save_to_json(self, filename):
        """保存为JSON格式"""
        filepath = os.path.join(self.data_dir, f"{filename}.json")
        
        try:
            # 如果文件存在，读取现有数据
            existing_data = []
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # 合并新数据
            all_data = existing_data + self.note_data_buffer
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            
            print(f"音符数据已保存到: {filepath} ({len(self.note_data_buffer)} 条新记录)")
            
        except Exception as e:
            print(f"保存JSON文件时出错: {e}")
    
    def finalize_session(self):
        """结束会话，保存所有剩余数据"""
        if self.note_data_buffer:
            self.save_to_file(auto_save_threshold=0)  # 强制保存所有数据
            
        # 保存会话统计信息
        session_info = {
            'session_name': self.session_name,
            'start_time': self.session_start_time,
            'end_time': time.time(),
            'duration': time.time() - self.session_start_time,
            'total_notes': len(self.note_data_buffer),
            'timestamp': self.session_timestamp
        }
        
        # 保存会话信息
        info_filepath = os.path.join(self.data_dir, f"session_info_{self.session_timestamp}_{self.session_name}.json")
        try:
            with open(info_filepath, 'w', encoding='utf-8') as f:
                json.dump(session_info, f, ensure_ascii=False, indent=2)
            print(f"会话信息已保存到: {info_filepath}")
        except Exception as e:
            print(f"保存会话信息时出错: {e}")
    
    def get_session_stats(self):
        """获取当前会话的统计信息"""
        if not self.note_data_buffer:
            return None
        
        # 统计不同乐器使用次数
        instruments = {}
        frequencies = []
        durations = []
        
        for record in self.note_data_buffer:
            instrument = record.get('instrument', 'unknown')
            instruments[instrument] = instruments.get(instrument, 0) + 1
            frequencies.append(record.get('frequency', 0))
            durations.append(record.get('duration', 0))
        
        return {
            'total_notes': len(self.note_data_buffer),
            'session_duration': time.time() - self.session_start_time,
            'instruments_used': instruments,
            'avg_frequency': sum(frequencies) / len(frequencies) if frequencies else 0,
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'frequency_range': (min(frequencies), max(frequencies)) if frequencies else (0, 0),
            'duration_range': (min(durations), max(durations)) if durations else (0, 0)
        } 