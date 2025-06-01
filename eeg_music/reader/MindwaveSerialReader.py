import serial
import time
import json
import os
import platform
import numpy as np
from datetime import datetime
import argparse
import serial.tools.list_ports
from eeg_music.reader.MindwaveSerial import MindwaveSerial

class MindwaveSerialReader:
    def __init__(self, port=None, baudrate=57600, timeout=1, name='default', mood='default'):
        """初始化串口连接"""
        # 根据操作系统自动选择默认端口
        if port is None:
            if platform.system() == 'Windows':
                self.port = 'COM6'
            else:  # Linux/Mac
                self.port = '/dev/ttyACM0'  # Ubuntu下常见USB设备名为/dev/ttyACM0，特别是STM32设备
        else:
            self.port = port
            
        self.baudrate = baudrate
        self.timeout = timeout
        self.neuro = None
        self.data_buffer = []
        self.name = name
        mood_labels = {'happy':0,'sad':1,'angry':2,'peaceful':3}
        self.mood = mood_labels[mood]

    def connect(self):
        """建立串口连接"""
        while True:
            try:
                self.neuro = MindwaveSerial(self.port, self.baudrate)
                self.neuro.start()
                print(f"成功连接到 {self.port}")
                return True
            except Exception as e:
                print(f"连接失败: {str(e)}")
                time.sleep(3)
                continue
            
    def disconnect(self):
        """关闭串口连接"""
        if self.neuro:
            self.neuro.stop()
            print("串口连接已关闭")
            
    def read_data(self, save_to_file=False, duration=None):
        """读取脑波数据并可选择保存到文件
        
        参数:
        save_to_file (bool): 是否保存数据到文件
        duration (int): 读取时间(s) None表示一直读取直到中断
        """
        if not self.neuro:
            print("未连接到脑波设备")
            return
        try:
            start_time = time.time()
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M%f")
            while True:
                # 获取当前的脑波数据
                # 收集所有类型的脑波数据
                t = time.time() - start_time
                brain_data = {
                    'timestamp': t,
                    'attention': self.neuro.attention,
                    'meditation': self.neuro.meditation,
                    'rawValue': self.neuro.rawValue,
                    'delta': self.neuro.delta,
                    'theta': self.neuro.theta,
                    'lowAlpha': self.neuro.lowAlpha,
                    'highAlpha': self.neuro.highAlpha,
                    'lowBeta': self.neuro.lowBeta,
                    'highBeta': self.neuro.highBeta,
                    'lowGamma': self.neuro.lowGamma,
                    'midGamma': self.neuro.midGamma,
                    'poorSignal': self.neuro.poorSignal,
                    'blinkStrength': self.neuro.blinkStrength,
                    'mood': self.mood
                }
                
                print(
                    f"rawValue: {brain_data['rawValue']}, "
                    f"专注度: {brain_data['attention']}, "
                    f"冥想度: {brain_data['meditation']}, "
                    f"信号质量: {brain_data['poorSignal']}, "
                    f"信号强度: {brain_data['blinkStrength']}"
                )
                
                # 保存数据 将attention作为衡量信号的指标
                if save_to_file and brain_data['attention'] > 50:
                    self.data_buffer.append(brain_data)
                    
                    # # 每100条数据保存一次
                    # if len(self.data_buffer) >= 100:
                    #     self.save_data_to_file(timestamp)
                    #     self.data_buffer = []
                
                # 如果设置了持续时间，检查是否达到
                if duration is not None:
                    if (time.time() - start_time) >= duration:
                        self.save_data_to_file(timestamp)
                        self.data_buffer = []
                        break
                
                time.sleep(0.1)  # 帧率只有1hz,但是rawdata的时间很长
                
        except KeyboardInterrupt:
            print("\n停止读取数据")
        finally:
            if save_to_file and self.data_buffer:
                self.save_data_to_file(timestamp)
    
    @property   
    def current_data(self):
        """获取当前的脑波数据"""
        return {
            'attention': self.neuro.attention,
            'meditation': self.neuro.meditation,
            'rawValue': self.neuro.rawValue,
            'delta': self.neuro.delta,
            'theta': self.neuro.theta,
            'lowAlpha': self.neuro.lowAlpha,
            'highAlpha': self.neuro.highAlpha,
            'lowBeta': self.neuro.lowBeta,
            'highBeta': self.neuro.highBeta,
            'lowGamma': self.neuro.lowGamma,
            'midGamma': self.neuro.midGamma,
            'poorSignal': self.neuro.poorSignal,
            'blinkStrength': self.neuro.blinkStrength,
            'mood': self.mood
        }

    def save_data_to_file(self,timestamp):
        """将数据保存到文件"""
        if not self.data_buffer:
            return
            
        filename = f"mindwave_data_{timestamp}_{self.name}_{self.mood}.csv"
        
        try:
            # 确保存在data目录
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # 创建以被试者名字命名的子目录
            subject_dir = os.path.join('data', 'eeg', self.name)
            if not os.path.exists(subject_dir):
                os.makedirs(subject_dir)
                
            filepath = os.path.join(subject_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                # 添加列标题
                f.write("timestamp,attention,meditation,rawValue,delta,theta,lowAlpha,highAlpha,lowBeta,highBeta,lowGamma,midGamma,poorSignal,blinkStrength,mood\n")
                for data in self.data_buffer:
                    f.write(f"{data['timestamp']},{data['attention']},{data['meditation']},{data['rawValue']},{data['delta']},{data['theta']},{data['lowAlpha']},{data['highAlpha']},{data['lowBeta']},{data['highBeta']},{data['lowGamma']},{data['midGamma']},{data['poorSignal']},{data['blinkStrength']},{data['mood']}\n")
            print(f"数据已保存到文件: {filepath}")
        except Exception as e:
            print(f"保存数据时出错: {str(e)}")

def list_available_ports():
    """列出所有可用的串口设备"""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("未找到串口设备")
        return
    
    print("可用的串口设备:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Mindwave 脑波数据读取器')
    parser.add_argument('-p', '--port', default='/dev/ttyACM0',help='串口设备路径，例如COM6(Windows)或/dev/ttyACM0(Linux)')
    parser.add_argument('-b', '--baudrate', type=int, default=57600 , help='波特率，默认57600 ')
    parser.add_argument('-t', '--timeout', type=float, default=1, help='超时设置，默认1秒')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有可用的串口设备')
    parser.add_argument('-d', '--duration', type=int, help='读取持续时间（秒），默认持续读取直到中断')
    parser.add_argument('-n', '--no-save', action='store_true', help='不保存数据到文件')
    parser.add_argument('-e', '--name', default='default', help='被试者的名字')
    args = parser.parse_args()
    
    # 如果用户请求列出设备，则显示设备列表后退出
    if args.list:
        list_available_ports()
        return
    
    # 创建串口读取器实例
    reader = MindwaveSerialReader(
        port=args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
        name=args.name
    )
    
    # 尝试连接串口
    if reader.connect():
        try:
            # 开始读取数据
            reader.read_data(
                save_to_file=not args.no_save,
                duration=args.duration
            )
        finally:
            # 确保正确关闭串口
            reader.disconnect()
    
if __name__ == "__main__":
    main() 