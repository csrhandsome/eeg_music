import argparse
import asyncio
from eeg_music.server.WebServer import WebServer
from eeg_music.reader.ArduinoSerialReader import ArduinoSerialReader
from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader

def open_websocket():
    parser = argparse.ArgumentParser(description='WebSocket server for EEG music')
    parser.add_argument('--arduino_port', type=str, default='COM3', help='Arduino port (default: COM3)')
    parser.add_argument('--arduino_baudrate', type=int, default=9600, help='Arduino baudrate (default: 9600)')
    parser.add_argument('--mindwave_port', type=str, default='COM4', help='Mindwave port (default: COM4)')
    parser.add_argument('--mindwave_baudrate', type=int, default=57600, help='Mindwave baudrate (default: 57600)')
    parser.add_argument('--name', type=str, default='default', help='Name for the Mindwave reader')
    args = parser.parse_args()
    try:
        asyncio.run(WebServer(
            ArduinoSerialReader(port=args.arduino_port, baudrate=args.arduino_baudrate),
            MindwaveSerialReader(port=args.mindwave_port, baudrate=args.mindwave_baudrate, name=args.name)
        ).run())
    except KeyboardInterrupt:
        print("\nWebSocket服务器已停止。")
    except Exception as e:
        print(f"\n启动WebSocket服务器时出错: {e}")

if __name__ == "__main__":
    open_websocket()