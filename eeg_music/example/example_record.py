from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader
import argparse

# !!!采集数据前，需要用水沾湿eeg设备!!!
def record_data():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Mindwave 脑波数据读取器')
    parser.add_argument('-p', '--port', default='/dev/ttyACM0',help='串口设备路径，例如COM6(Windows)或/dev/ttyACM0(Linux)')
    parser.add_argument('-b', '--baudrate', type=int, default=57600 , help='波特率，默认57600 ')
    parser.add_argument('-t', '--timeout', type=float, default=1, help='超时设置，默认1秒')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有可用的串口设备')
    parser.add_argument('-d', '--duration', type=int, help='读取持续时间（秒），默认持续读取直到中断')
    parser.add_argument('-n', '--no-save', action='store_true', help='不保存数据到文件')
    parser.add_argument('-e', '--name', default='default', help='被试者的名字')
    parser.add_argument('-m', '--mood', default='default', help='被试者的情绪')
    args = parser.parse_args()
    
    
    # 创建串口读取器实例
    reader = MindwaveSerialReader(
        port=args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
        name=args.name,
        mood=args.mood
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
    record_data()
