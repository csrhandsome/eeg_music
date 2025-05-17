import asyncio
import websockets
import json
import random
import time
import argparse
from eeg_music.reader.ArduinoSerialReader import ArduinoSerialReader
from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader

# WebSocket服务器运行函数（在单独线程中运行）
def run_webserver_thread(arduino_reader, mindwave_reader=None):
    """在单独线程中运行WebSocket服务器的函数"""
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 创建WebServer实例
    webserver = WebServer(arduino_reader=arduino_reader, mindwave_reader=mindwave_reader)
    
    # 运行WebSocket服务器
    try:
        print("WebSocket服务器已启动,请用浏览器打开 visualization/arduino_visualization.html 查看实时可视化")
        loop.run_until_complete(webserver.run())
    except Exception as e:
        print(f"WebSocket服务器出错: {e}")
    finally:
        loop.close()

class WebServer:
    # 存储所有连接的客户端
    def __init__(self, arduino_reader=None, mindwave_reader=None):
        self.connected_clients = set()
        self.arduino_reader = arduino_reader
        self.mindwave_reader = mindwave_reader

    async def register(self, websocket):
        """注册新的客户端连接"""
        self.connected_clients.add(websocket)
        print(f"New client connected: {websocket.remote_address}. Total clients: {len(self.connected_clients)}")
        try:
            # 保持连接打开，等待客户端可能发送的消息（如果需要）
            # 或者在这里发送一个欢迎消息
            await websocket.send(json.dumps({"message": "Welcome to the WebSocket server!"}))
            async for message in websocket: # 如果你期望客户端发送消息
                print(f"Received message from {websocket.remote_address}: {message}")
                # 你可以在这里处理来自客户端的消息
        except websockets.exceptions.ConnectionClosedOK:
            print(f"Client {websocket.remote_address} disconnected gracefully.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Client {websocket.remote_address} disconnected with error: {e}")
        finally:
            self.connected_clients.remove(websocket)
            print(f"Client {websocket.remote_address} removed. Total clients: {len(self.connected_clients)}")

    async def send_data_periodically(self):
        """定期向所有连接的客户端发送模拟数据"""
        while True:
            data_to_send = {}
            if self.connected_clients: # 只有当有客户端连接时才发送
                # 模拟实时数据
                if self.arduino_reader or self.mindwave_reader:
                    if self.arduino_reader :
                        # 在play里面调用的时候不需要重新读了，play的程序里面已经读了，我.current_data就行
                        # self.arduino_reader.read_data(
                        #     save_to_file=False,
                        #     duration=None
                        # )
                        # arudino_reader在readdata的时候会调用_parse_data()
                        arduino_data = self.arduino_reader.current_data
                        if arduino_data:
                            data_to_send.update(arduino_data)
                    if self.mindwave_reader :
                        self.mindwave_reader.read_data(
                            save_to_file=False,
                            duration=None
                        )
                        mindwave_data = self.mindwave_reader.current_data
                        if mindwave_data:
                            data_to_send.update(mindwave_data)
                data_to_send['timestamp'] = time.time()
                message_json = json.dumps(data_to_send)

                # 使用 asyncio.gather 并发发送给所有客户端
                # 同时捕获发送过程中可能发生的连接断开异常
                tasks = [client.send(message_json) for client in self.connected_clients]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        # 从set中移除发生错误的客户端可能比较复杂，因为set是无序的
                        # 更好的做法是在 register 的 finally 块中处理移除
                        print(f"Error sending to a client: {result}. Client might have disconnected.")
                        # 你可能需要一个更健壮的机制来处理发送失败的客户端

                # print(f"Sent data to {len(self.connected_clients)} clients: {data_to_send}")

            await asyncio.sleep(0.01)  # 每0.01秒发送一次数据

    async def run(self):
        # 启动 WebSocket 服务器
        # 第一个参数是连接处理函数 (handler)
        # 第二个参数是主机名，'localhost' 或 '0.0.0.0' (0.0.0.0 表示监听所有可用网络接口)
        # 第三个参数是端口号
        server_address = "localhost"
        server_port = 8765 # 你可以选择一个未被占用的端口
        
        # 创建一个任务来定期发送数据
        asyncio.create_task(self.send_data_periodically())

        print(f"Starting WebSocket server on ws://{server_address}:{server_port}")
        async with websockets.serve(self.register, server_address, server_port):
            await asyncio.Future()  # 运行直到被中断 (例如 Ctrl+C)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='WebSocket server for EEG music')
    parser.add_argument('--arduino_port', type=str, default='COM3', help='Arduino port (default: COM3)')
    parser.add_argument('--arduino_baudrate', type=int, default=9600, help='Arduino baudrate (default: 9600)')
    parser.add_argument('--mindwave_port', type=str, default='COM4', help='Mindwave port (default: COM4)')
    parser.add_argument('--mindwave_baudrate', type=int, default=57600, help='Mindwave baudrate (default: 57600)')
    parser.add_argument('--name', type=str, default='default', help='Name for the Mindwave reader')
    args = parser.parse_args()
    try:
        asyncio.run(WebServer(
            arduino_reader=ArduinoSerialReader(
                port=args.arduino_port, 
                baudrate=args.arduino_baudrate
            ),
            mindwave_reader=MindwaveSerialReader(
                port=args.mindwave_port, 
                baudrate=args.mindwave_baudrate, 
                name=args.name
            )
        ).run())
    except KeyboardInterrupt:
        print("\nWebSocket服务器已停止。")
    except Exception as e:
        print(f"\n启动WebSocket服务器时出错: {e}")