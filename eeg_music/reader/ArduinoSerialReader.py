import serial
import time
import os
import platform
from datetime import datetime
import re
import argparse
import serial.tools.list_ports

class ArduinoSerialReader:
    def __init__(self, port=None, baudrate=9600, timeout=1):
        """初始化串口连接"""
        # 根据操作系统自动选择默认端口
        if port is None:
            if platform.system() == 'Windows':
                self.port = 'COM3'
            else:  # Linux/Mac
                self.port = '/dev/ttyUSB0'  # Linux下Arduino常见端口
        else:
            self.port = port
            
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.data_buffer = []
        
        # 用于存储解析的数据
        self.timestamp = ""
        self.distance = 0
        self.scale = ""
        self.note = 0
        self.frequency = 0
        self.potentiometer = 0
        self.rotary_potentiometer = ""
        self.button_state = 0
        
    def connect(self):
        """建立串口连接"""
        while True:
            try:
                self.serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
                print(f"成功连接到 {self.port}")
                return True
            except Exception as e:
                print(f"连接失败: {str(e)}")
                time.sleep(3)
                continue
            
    def disconnect(self):
        """关闭串口连接"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("串口连接已关闭")
    
    def read_data(self, save_to_file=False, duration=None):
        """读取Arduino数据并解析
        
        参数:
        save_to_file (bool): 是否保存数据到文件
        duration (int): 读取时间(秒),None表示一直读取直到中断
        """
        if not self.serial or not self.serial.is_open:
            print("未连接到Arduino设备")
            return
            
        try:
            start_time = time.time()
            while True:
                if self.serial.in_waiting:
                    # 读取字节数据
                    raw_line = self.serial.readline()
                    
                    # 尝试以不同编码解码
                    line = None
                    for encoding in ['utf-8', 'latin1', 'cp1252', 'ascii']:
                        try:
                            line = raw_line.decode(encoding).strip()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    # 如果所有编码都失败，则使用latin1（它可以解码所有字节）
                    if line is None:
                        line = raw_line.decode('latin1', errors='replace').strip()
                    
                    if line:
                        self._parse_data(line)
                        print(f"时间戳: {self.timestamp}, 距离: {self.distance} cm, 音阶: {self.scale}, 音符: {self.note}, 频率: {self.frequency} Hz, 电位器: {self.potentiometer}, 旋转电位器: {self.rotary_potentiometer}, 按钮状态: {self.button_state}")
                
                # 如果设置了持续时间，检查是否达到
                if duration is not None:
                    if (time.time() - start_time) >= duration:
                        break
                    
                time.sleep(0.01)  # 短暂休眠以避免CPU占用过高
                
        except KeyboardInterrupt:
            print("\n停止读取数据")
        except Exception as e:
            print(f"读取数据时出错: {str(e)}")
        finally:
            pass

    # arduino的代码逻辑是一行一行的打印出来，所以需要_parse_data方法来解析数据
    def _parse_data(self, line):
        """解析Arduino传来的数据行
        
        示例格式:
        Distance: 34.79 cm, Scale: C Major, Note: 5, Base Frequency: 440.00 Hz, Pot1 Voltage: 2.55 V, Pot2 Voltage: 3.25 V, Toggle State: 1
        """
        try:
            # 检查是否是数据行（包含Distance关键字）
            if "Distance:" in line:
                # 提取距离
                distance_match = re.search(r"Distance:\s+([\d.]+)\s+cm", line)
                if distance_match:
                    self.distance = float(distance_match.group(1))
                    
                # 提取音阶
                scale_match = re.search(r"Scale:\s+([^,]+),", line)
                if scale_match:
                    self.scale = scale_match.group(1).strip()
                    
                # 提取音符
                note_match = re.search(r"Note:\s+(\d+)", line)
                if note_match:
                    self.note = int(note_match.group(1))
                    
                # 提取调整后的频率
                freq_match = re.search(r"Base Frequency:\s+([\d.]+)", line)
                if freq_match:
                    self.frequency = float(freq_match.group(1))
                    
                # 提取电位器电压（Arduino发送的是"Pot1 Voltage"）
                potentiometer_match = re.search(r"Pot1 Voltage:\s+([\d.]+)", line)
                if potentiometer_match:
                    self.potentiometer = float(potentiometer_match.group(1))
                    
                # 提取旋转电位器电压（Arduino发送的是"Pot2 Voltage"）
                rotary_pot_match = re.search(r"Pot2 Voltage:\s+([\d.]+)", line)
                if rotary_pot_match:
                    self.rotary_potentiometer = rotary_pot_match.group(1)
                    
                # 提取按钮状态（Arduino发送的是"Toggle State"）
                button_match = re.search(r"Toggle State:\s+(\d+)", line)
                if button_match:
                    self.button_state = int(button_match.group(1))
                
                # 更新时间戳
                self.timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
        except Exception as e:
            print(f"解析数据时出错: {str(e)}")
    
    @property
    def current_data(self):
        """获取当前的数据
        
        返回:
            dict: 包含当前读取的所有传感器数据
        """
        return {
            'distance': self.distance,
            'scale': self.scale,
            'note': self.note,
            'freq': self.frequency,
            'potentiometer': self.potentiometer,
            'rotary_potentiometer': self.rotary_potentiometer,
            'button_state': self.button_state,
            # 为了向后兼容，保留voltage字段，映射到potentiometer
            'voltage': self.potentiometer
        }

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
    parser = argparse.ArgumentParser(description='Arduino 串口数据读取器')
    parser.add_argument('-p', '--port', help='串口设备路径,例如COM3(Windows)或/dev/ttyUSB0(Linux)')
    parser.add_argument('-b', '--baudrate', type=int, default=9600, help='波特率,默认9600')
    parser.add_argument('-t', '--timeout', type=float, default=1, help='超时设置,默认1秒')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有可用的串口设备')
    parser.add_argument('-d', '--duration', type=int, help='读取持续时间（秒）,默认持续读取直到中断')
    args = parser.parse_args()
    
    # 如果用户请求列出设备，则显示设备列表后退出
    if args.list:
        list_available_ports()
        return
    
    # 创建串口读取器实例
    reader = ArduinoSerialReader(
        port=args.port,
        baudrate=args.baudrate,
        timeout=args.timeout
    )
    
    # 尝试连接串口
    if reader.connect():
        try:
            # 开始读取数据
            reader.read_data(
                save_to_file=False,
                duration=args.duration
            )
        finally:
            # 确保正确关闭串口
            reader.disconnect()
    
if __name__ == "__main__":
    main() 