import asyncio
import websockets
import json
import time
import os
import glob
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
        print("WebSocket服务器已启动")
        print("请用浏览器打开 visualization/welcomepage.html 查看欢迎页面")
        loop.run_until_complete(webserver.run(arduino_reader, mindwave_reader))
    except Exception as e:
        print(f"WebSocket服务器出错: {e}")
    finally:
        loop.close()

class WebServer:
    def __init__(self):
        self.connected_clients = set()
        self.last_data = {}  # 缓存上次发送的数据，避免重复发送
        self.data_changed = False  # 数据是否有变化

    async def register(self, websocket):
        """注册新的客户端连接"""
        self.connected_clients.add(websocket)
        print(f"客户端已连接: {websocket.remote_address}. 总连接数: {len(self.connected_clients)}")
        
        try:
            # 发送欢迎消息
            await websocket.send(json.dumps({"message": "Welcome to the WebSocket server!"}))
            
            # 监听客户端消息
            async for message in websocket:
                await self.handle_client_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosedOK:
            print(f"客户端 {websocket.remote_address} 正常断开连接")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"客户端 {websocket.remote_address} 连接异常断开: {e}")
        except Exception as e:
            print(f"客户端 {websocket.remote_address} 发生错误: {e}")
        finally:
            self.connected_clients.discard(websocket)
            print(f"客户端 {websocket.remote_address} 已移除. 总连接数: {len(self.connected_clients)}")

    async def handle_client_message(self, websocket, message):
        """处理来自客户端的消息 - 只处理歌曲名称"""
        try:
            data = json.loads(message)
            
            # 只处理歌曲名称消息
            if data.get('type') == 'song_name':
                song_name = data.get('data', '').strip()
                
                if song_name:
                    print(f"收到歌曲名称: '{song_name}' 来自 {websocket.remote_address}")
                    
                    # 发送确认消息
                    confirmation = {
                        'type': 'song_name_confirmation',
                        'message': f'歌曲名称 "{song_name}" 已收到',
                        'success': True
                    }
                    await websocket.send(json.dumps(confirmation))
                else:
                    # 歌曲名称为空
                    error_msg = {
                        'type': 'error',
                        'message': '歌曲名称不能为空'
                    }
                    await websocket.send(json.dumps(error_msg))
                    
        except json.JSONDecodeError:
            print(f"收到无效JSON消息 from {websocket.remote_address}: {message}")
        except Exception as e:
            print(f"处理客户端消息时出错 {websocket.remote_address}: {e}")

    async def send_data_periodically(self, arduino_reader, mindwave_reader):
        """优化的数据发送循环"""
        while True:
            # 如果没有客户端连接，降低检查频率
            if not self.connected_clients:
                await asyncio.sleep(0.1)  # 100ms
                continue
            
            # 收集数据
            data_to_send = {}
            data_changed = False
            
            # 获取Arduino数据
            if arduino_reader and arduino_reader.current_data:
                arduino_data = arduino_reader.current_data
                data_to_send.update(arduino_data)
            
            # 获取Mindwave数据
            if mindwave_reader and hasattr(mindwave_reader, 'current_data') and mindwave_reader.current_data:
                mindwave_data = mindwave_reader.current_data
                data_to_send.update(mindwave_data)
            
            # 检查数据是否有变化（简单的变化检测）
            if data_to_send != self.last_data:
                data_changed = True
                self.last_data = data_to_send.copy()
            
            # 只有数据有变化时才发送
            if data_changed and data_to_send:
                data_to_send['timestamp'] = time.time()
                message_json = json.dumps(data_to_send)
                
                # 并发发送给所有客户端
                disconnected_clients = set()
                
                for client in self.connected_clients.copy():
                    try:
                        await client.send(message_json)
                    except websockets.exceptions.ConnectionClosed:
                        disconnected_clients.add(client)
                    except Exception as e:
                        print(f"发送数据到客户端失败: {e}")
                        disconnected_clients.add(client)
                
                # 移除断开的客户端
                self.connected_clients -= disconnected_clients
                
                if disconnected_clients:
                    print(f"移除了 {len(disconnected_clients)} 个断开的客户端")
            
            # 降低发送频率到30Hz，减少CPU占用
            await asyncio.sleep(0.01)  # 约30Hz

    async def create_http_server(self):
        """创建轻量级HTTP服务器,只提供静态文件服务"""
        app = web.Application()
        
        # 添加静态文件服务 - 服务visualization目录
        visualization_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'visualization')
        visualization_path = os.path.abspath(visualization_path)
        
        print(f"静态文件服务路径: {visualization_path}")
        
        # 添加静态文件路由
        app.router.add_static('/', visualization_path, name='static')
        
        # 添加根路径重定向
        async def index_handler(request):
            raise web.HTTPFound('/welcomepage.html')
        
        app.router.add_get('/', index_handler)
        
        # 添加文件列表API
        async def file_list_handler(request):
            try:
                # 获取当前工作目录下的data/music_notes路径
                current_dir = os.getcwd()
                data_dir = os.path.join(current_dir, 'data', 'music_notes')
                
                print(f"查找文件目录: {data_dir}")
                
                if not os.path.exists(data_dir):
                    print(f"目录不存在: {data_dir}")
                    return web.json_response({"error": f"目录不存在: {data_dir}"}, status=404)
                
                # 获取所有CSV文件
                csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
                print(f"找到 {len(csv_files)} 个CSV文件")
                
                file_list = []
                for file_path in csv_files:
                    try:
                        # 获取文件信息
                        file_name = os.path.basename(file_path)
                        file_size = os.path.getsize(file_path)
                        
                        # 格式化文件大小
                        if file_size >= 1024 * 1024:
                            size_str = f"{file_size / (1024 * 1024):.1f}MB"
                        elif file_size >= 1024:
                            size_str = f"{file_size / 1024:.1f}KB"
                        else:
                            size_str = f"{file_size}B"
                        
                        # 计算文件行数（CSV文件）
                        lines = 0
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = sum(1 for _ in f)
                                if lines > 0:
                                    lines -= 1  # 减去标题行
                        except:
                            lines = 0
                        
                        file_list.append({
                            "name": file_name,
                            "size": size_str,
                            "lines": lines
                        })
                        print(f"处理文件: {file_name} - {size_str} - {lines}行")
                    except Exception as e:
                        print(f"处理文件 {file_path} 时出错: {e}")
                        continue
                
                # 按文件名降序排序
                file_list.sort(key=lambda x: x["name"], reverse=True)
                
                return web.json_response({"files": file_list})
                
            except Exception as e:
                print(f"获取文件列表时出错: {e}")
                import traceback
                traceback.print_exc()
                return web.json_response({"error": str(e)}, status=500)
        
        app.router.add_get('/api/files', file_list_handler)
        
        # 简化的CORS支持
        @web.middleware
        async def cors_handler(request, handler):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        
        app.middlewares.append(cors_handler)
        
        return app

    async def run(self, arduino_reader, mindwave_reader):
        """启动WebSocket和HTTP服务器"""
        # 使用0.0.0.0允许外部访问，而不是localhost
        server_address = "0.0.0.0"
        websocket_port = 8765
        http_port = 8766
        
        # 启动数据发送任务
        asyncio.create_task(self.send_data_periodically(arduino_reader, mindwave_reader))

        # 启动HTTP服务器（静态文件服务）
        app = await self.create_http_server()
        runner = web_runner.AppRunner(app)
        await runner.setup()
        site = web_runner.TCPSite(runner, server_address, http_port)
        await site.start()

        print(f"WebSocket服务器启动: ws://{server_address}:{websocket_port}")
        print(f"HTTP服务器启动: http://{server_address}:{http_port}")

        # 启动WebSocket服务器
        async with websockets.serve(self.register, server_address, websocket_port):
            await asyncio.Future()  # 运行直到被中断

