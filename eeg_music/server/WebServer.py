import asyncio
import websockets
import json
import subprocess
import time
import os
from aiohttp import web, web_runner
from eeg_music.reader.ArduinoSerialReader import ArduinoSerialReader
from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader

# WebSocket服务器运行函数（在单独线程中运行）
def run_webserver_thread(arduino_reader, mindwave_reader=None):
    """在单独线程中运行WebSocket服务器的函数"""
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 创建WebServer实例
    webserver = WebServer()
    
    # 运行WebSocket服务器
    try:
        print("WebSocket服务器已启动,请用浏览器打开 visualization/welcomepage.html 查看欢迎页面")
        loop.run_until_complete(webserver.run(arduino_reader, mindwave_reader))
    except Exception as e:
        print(f"WebSocket服务器出错: {e}")
    finally:
        loop.close()

class WebServer:
    # 存储所有连接的客户端
    def __init__(self):
        self.connected_clients = set()
        self.song_records = []  # 存储歌曲记录

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
                # 处理来自客户端的消息
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosedOK:
            print(f"Client {websocket.remote_address} disconnected gracefully.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Client {websocket.remote_address} disconnected with error: {e}")
        finally:
            self.connected_clients.remove(websocket)
            print(f"Client {websocket.remote_address} removed. Total clients: {len(self.connected_clients)}")

    async def handle_client_message(self, websocket, message):
        """处理来自客户端的消息"""
        try:
            data = json.loads(message)
            if data.get('type') == 'song_name':
                song_name = data.get('data', '').strip()
                timestamp = data.get('timestamp', time.time())
                
                if song_name:
                    # 存储歌曲记录
                    song_record = {
                        'song_name': song_name,
                        'timestamp': timestamp,
                        'datetime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp/1000)),
                        'client_address': str(websocket.remote_address)
                    }
                    self.song_records.append(song_record)
                    
                    print(f"收到歌曲名称: {song_name} from {websocket.remote_address}")
                    print(f"当前歌曲记录数量: {len(self.song_records)}")
                    
                    # 向客户端发送确认消息
                    confirmation = {
                        'type': 'song_name_confirmation',
                        'message': f'歌曲名称 "{song_name}" 已成功记录',
                        'success': True
                    }
                    await websocket.send(json.dumps(confirmation))
                    
                    # 这里可以添加更多处理逻辑，比如保存到文件或数据库
                    self.save_song_record(song_record)
                else:
                    error_msg = {
                        'type': 'error',
                        'message': '歌曲名称不能为空'
                    }
                    await websocket.send(json.dumps(error_msg))
                    
        except json.JSONDecodeError:
            print(f"Invalid JSON message from {websocket.remote_address}: {message}")
        except Exception as e:
            print(f"Error handling message from {websocket.remote_address}: {e}")

    def save_song_record(self, record):
        """保存歌曲记录到文件"""
        try:
            # 确保数据目录存在
            os.makedirs('data', exist_ok=True)
            
            # 保存到JSON文件
            filename = 'data/song_records.json'
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_records = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_records = []
            
            existing_records.append(record)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_records, f, ensure_ascii=False, indent=2)
                
            print(f"歌曲记录已保存到: {filename}")
            
        except Exception as e:
            print(f"保存歌曲记录时出错: {e}")

    def get_song_records(self):
        """获取所有歌曲记录"""
        return self.song_records.copy()

    async def send_data_periodically(self, arduino_reader, mindwave_reader):
        """定期向所有连接的客户端发送实时数据"""
        while True:
            data_to_send = {}
            if self.connected_clients: # 只有当有客户端连接时才发送
                # 获取实时数据
                if arduino_reader:
                    arduino_data = arduino_reader.current_data
                    if arduino_data:
                        data_to_send.update(arduino_data)
                
                if mindwave_reader:
                    mindwave_data = mindwave_reader.current_data if hasattr(mindwave_reader, 'current_data') else {}
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
            
    async def handle_run_script(self, request):
        """处理运行脚本的HTTP请求"""
        try:
            data = await request.json()
            script_path = data.get('script', '')
            
            if not script_path:
                return web.json_response({'success': False, 'error': '未指定脚本路径'}, status=400)
            
            # 安全检查：只允许运行scripts目录下的.sh文件
            if not script_path.startswith('scripts/') or not script_path.endswith('.sh'):
                return web.json_response({'success': False, 'error': '只允许运行scripts目录下的.sh文件'}, status=400)
            
            # 检查文件是否存在
            if not os.path.exists(script_path):
                return web.json_response({'success': False, 'error': f'脚本文件不存在: {script_path}'}, status=404)
            
            # 运行脚本
            print(f"正在运行脚本: {script_path}")
            process = subprocess.Popen(['bash', script_path], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            # 不等待脚本完成，直接返回成功
            return web.json_response({
                'success': True, 
                'message': f'脚本 {script_path} 已开始运行',
                'pid': process.pid
            })
            
        except Exception as e:
            print(f"运行脚本时出错: {e}")
            return web.json_response({'success': False, 'error': str(e)}, status=500)

    async def create_http_server(self):
        """创建HTTP服务器用于处理脚本执行请求"""
        app = web.Application()
        app.router.add_post('/run_script', self.handle_run_script)
        
        # 添加CORS支持
        async def cors_handler(request, handler):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        
        app.middlewares.append(cors_handler)
        
        # 处理OPTIONS请求
        async def options_handler(request):
            response = web.Response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        
        app.router.add_route('OPTIONS', '/run_script', options_handler)
        
        return app

    async def run(self, arduino_reader, mindwave_reader):
        # 启动 WebSocket 服务器
        # 第一个参数是连接处理函数 (handler)
        # 第二个参数是主机名，'localhost' 或 '0.0.0.0' (0.0.0.0 表示监听所有可用网络接口)
        # 第三个参数是端口号
        server_address = "localhost"
        websocket_port = 8765 # WebSocket端口
        http_port = 8766 # HTTP端口
        
        # 创建一个任务来定期发送数据
        asyncio.create_task(self.send_data_periodically(arduino_reader, mindwave_reader))

        # 创建HTTP服务器
        app = await self.create_http_server()
        runner = web_runner.AppRunner(app)
        await runner.setup()
        site = web_runner.TCPSite(runner, server_address, http_port)
        await site.start()

        print(f"Starting WebSocket server on ws://{server_address}:{websocket_port}")
        print(f"Starting HTTP server on http://{server_address}:{http_port}")
        async with websockets.serve(self.register, server_address, websocket_port):
            await asyncio.Future()  # 运行直到被中断 (例如 Ctrl+C)

