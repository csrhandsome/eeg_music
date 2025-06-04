#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EEG音乐系统 - Flask服务器
基于原WebServer.py,使用Flask + Socket.IO替代原生WebSocket,保持接口兼容性
"""

import os
import json
import time
import glob
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from eeg_music.audio.MusicDataRecorder import MusicDataRecorder
from eeg_music.audio.MusicPlayer import MusicPlayer

# 尝试导入DeepseekReader，如果失败则设为None
try:
    from eeg_music.reader.DeepseekReader import DeepseekReader
    DEEPSEEK_AVAILABLE = True
except ImportError as e:
    print(f"警告: DeepseekReader导入失败: {e}")
    DeepseekReader = None
    DEEPSEEK_AVAILABLE = False

# Flask服务器运行函数（在单独线程中运行）
def run_flaskserver_thread(arduino_reader, mindwave_reader=None):
    """在单独线程中运行Flask服务器的函数"""
    # 创建FlaskServer实例
    flaskserver = FlaskServer()
    
    # 设置数据读取器
    flaskserver.set_data_readers(arduino_reader, mindwave_reader)
    
    # 运行Flask服务器
    try:
        print("Flask服务器已启动")
        print("请用浏览器打开 visualization/welcomepage.html 查看欢迎页面")
        flaskserver.run(arduino_reader, mindwave_reader)
    except Exception as e:
        print(f"Flask服务器出错: {e}")

class FlaskServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'eeg_music_secret_key_2025'
        
        # 启用CORS支持
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        
        # 初始化SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # 数据读取器
        self.arduino_reader = None
        self.mindwave_reader = None
        
        # 连接的客户端列表
        self.connected_clients = []
        
        # 数据缓存
        self.last_data = {}
        self.data_changed = False
        
        # 初始化音乐数据记录器
        self.music_recorder = MusicDataRecorder(session_name="default")
        
        # 录制状态管理
        self.recording_state = 'stopped'  # 'stopped', 'recording', 'paused'
        self.recording_action = None
        
        # 添加音乐播放器和回放状态管理
        self.music_player = MusicPlayer(max_sounds=50)
        self.playback_active = False
        self.playback_thread = None
        
        # 初始化DeepseekReader
        if DEEPSEEK_AVAILABLE:
            try:
                self.deepseek_reader = DeepseekReader(session_name="ai_generated")
                self.deepseek_reader.connect()
                print("DeepseekReader初始化成功")
            except Exception as e:
                print(f"DeepseekReader初始化失败: {e}")
                self.deepseek_reader = None
        else:
            self.deepseek_reader = None
        
        # 设置路由
        self.setup_routes()
        self.setup_socketio_events()
        
    def setup_routes(self):
        """设置HTTP路由"""
        
        @self.app.route('/')
        def index():
            """根路径重定向到欢迎页面"""
            return send_from_directory(self.get_visualization_path(), 'welcomepage.html')
        
        @self.app.route('/<path:filename>')
        def static_files(filename):
            """静态文件服务"""
            return send_from_directory(self.get_visualization_path(), filename)
        
        @self.app.route('/data/music_notes/<filename>')
        def music_files(filename):
            """音乐记录文件服务"""
            try:
                data_dir = os.path.join(os.getcwd(), 'data', 'music_notes')
                return send_from_directory(data_dir, filename)
            except Exception as e:
                return jsonify({"error": f"文件不存在: {str(e)}"}), 404
        
        @self.app.route('/api/files')
        def get_file_list():
            """获取音乐记录文件列表API - 与原WebServer兼容"""
            try:
                # 获取当前工作目录下的data/music_notes路径
                current_dir = os.getcwd()
                data_dir = os.path.join(current_dir, 'data', 'music_notes')
                
                print(f"查找文件目录: {data_dir}")
                
                if not os.path.exists(data_dir):
                    print(f"目录不存在: {data_dir}")
                    return jsonify({"error": f"目录不存在: {data_dir}"}), 404
                
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
                
                return jsonify({"files": file_list})
                
            except Exception as e:
                print(f"获取文件列表时出错: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/file/<filename>')
        def get_file_content(filename):
            """获取指定文件的内容"""
            try:
                data_dir = os.path.join(os.getcwd(), 'data', 'music_notes')
                file_path = os.path.join(data_dir, filename)
                
                if not os.path.exists(file_path):
                    return jsonify({"error": "文件不存在"}), 404
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return jsonify({
                    "filename": filename,
                    "content": content,
                    "size": os.path.getsize(file_path),
                    "lines": len(content.splitlines())
                })
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/status')
        def get_server_status():
            """获取服务器状态"""
            return jsonify({
                "status": "running",
                "connected_clients": len(self.connected_clients),
                "arduino_connected": self.arduino_reader is not None,
                "mindwave_connected": self.mindwave_reader is not None,
                "timestamp": time.time()
            })
    
    def setup_socketio_events(self):
        """设置SocketIO事件处理 - 兼容原WebSocket接口"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"客户端已连接: {request.sid}. 总连接数: {len(self.connected_clients) + 1}")
            self.connected_clients.append(request.sid)
            
            # 发送欢迎消息 - 与原WebSocket兼容
            emit('message', {"message": "Welcome to the WebSocket server!"})
            
            # 发送服务器状态
            emit('server_status', {
                "connected_clients": len(self.connected_clients),
                "timestamp": time.time()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"客户端 {request.sid} 已断开连接")
            if request.sid in self.connected_clients:
                self.connected_clients.remove(request.sid)
            print(f"总连接数: {len(self.connected_clients)}")
        
        @self.socketio.on('message')
        def handle_message(data):
            """处理消息格式"""
            try:
                # 处理字符串JSON数据
                if isinstance(data, str):
                    data = json.loads(data)
                
                # 处理歌曲名称消息 - 兼容原接口
                if data.get('type') in ['song_name', 'recording_song_name']:
                    song_name = data.get('data', '').strip()
                    
                    if song_name:
                        print(f"收到歌曲名称: '{song_name}' 来自 {request.sid}")
                        
                        # 更新音乐数据记录器的session_name
                        self.music_recorder.session_name = song_name
                        print(f"已更新MusicDataRecorder的session_name为: '{song_name}'")
                        
                        # 发送确认消息 - 与原WebSocket兼容
                        emit('song_name_confirmation', {
                            'type': 'song_name_confirmation',
                            'message': f'歌曲名称 "{song_name}" 已收到',
                            'success': True,
                            'song_name': song_name
                        })
                    else:
                        # 歌曲名称为空
                        emit('error', {
                            'type': 'error',
                            'message': '歌曲名称不能为空'
                        })
                
                # 处理录制文件名保存消息
                elif data.get('type') == 'save_filename':
                    filename = data.get('data', '').strip()
                    
                    if filename:
                        print(f"收到录制文件名: '{filename}' 来自 {request.sid}")
                        
                        # 更新音乐数据记录器的session_name
                        self.music_recorder.session_name = filename
                        print(f"已更新MusicDataRecorder的session_name为: '{filename}'")
                        
                        # 这里可以添加保存文件名到数据库或文件的逻辑
                        # 目前只是记录日志，实际保存逻辑可能在其他地方
                        
                        # 发送确认消息
                        emit('filename_confirmation', {
                            'type': 'filename_confirmation',
                            'message': f'录制文件名 "{filename}" 已保存',
                            'success': True,
                            'filename': filename,
                            'timestamp': time.time()
                        })
                    else:
                        # 文件名为空
                        emit('error', {
                            'type': 'error',
                            'message': '录制文件名不能为空'
                        })
                
                # 处理心音轨迹文件选择消息
                elif data.get('type') == 'file_selected':
                    filename = data.get('data', '').strip()
                    
                    if filename:
                        print(f"用户选择了历史文件: '{filename}' 来自 {request.sid}")
                        
                        # 启动文件回放
                        self.start_file_playback(filename)
                        
                        # 发送确认消息
                        emit('file_selection_confirmation', {
                            'type': 'file_selection_confirmation',
                            'message': f'已选择文件 "{filename}"，开始回放',
                            'success': True,
                            'selected_file': filename,
                            'timestamp': time.time()
                        })
                        
                        # 可选：同时发送文件内容
                        try:
                            data_dir = os.path.join(os.getcwd(), 'data', 'music_notes')
                            file_path = os.path.join(data_dir, filename)
                            
                            if os.path.exists(file_path):
                                # 获取文件基本信息（不读取全部内容，避免大文件影响性能）
                                file_size = os.path.getsize(file_path)
                                file_lines = 0
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        file_lines = sum(1 for _ in f)
                                        if file_lines > 0:
                                            file_lines -= 1  # 减去标题行
                                except:
                                    file_lines = 0
                                
                                emit('file_info', {
                                    'type': 'file_info',
                                    'filename': filename,
                                    'size': file_size,
                                    'lines': file_lines,
                                    'exists': True
                                })
                            else:
                                emit('file_info', {
                                    'type': 'file_info',
                                    'filename': filename,
                                    'exists': False,
                                    'error': '文件不存在'
                                })
                        except Exception as e:
                            print(f"获取文件信息时出错: {e}")
                    else:
                        # 文件名为空
                        emit('error', {
                            'type': 'error',
                            'message': '选择的文件名不能为空'
                        })
                
                # 处理录制状态变化消息
                elif data.get('type') == 'recording_state':
                    state_data = data.get('data', {})
                    new_state = state_data.get('state', '').strip()
                    action = state_data.get('action', '')
                    
                    if new_state in ['stopped', 'recording', 'paused']:
                        print(f"收到录制状态变化: '{new_state}' (action: {action}) 来自 {request.sid}")
                        
                        # 更新录制状态
                        self.recording_state = new_state
                        self.recording_action = action
                        
                        # 根据状态执行相应操作
                        if new_state == 'recording' and action in ['start', 'resume', 'cancel_filename_continue']:
                            print("  → 开始/继续录制音符数据")
                        elif new_state == 'paused' and action in ['filename_modal_open', 'stop_button']:
                            print("  → 暂停录制音符数据")
                        elif new_state == 'stopped' and action == 'save_and_finish':
                            print("  → 停止录制并保存文件")
                            # 在这里可以触发保存操作
                            self.music_recorder.save_to_file(auto_save_threshold=0)
                        
                        # 发送确认消息
                        emit('recording_state_confirmation', {
                            'type': 'recording_state_confirmation',
                            'message': f'录制状态已更新为 "{new_state}"',
                            'success': True,
                            'state': new_state,
                            'action': action,
                            'timestamp': time.time()
                        })
                    else:
                        # 无效的录制状态
                        emit('error', {
                            'type': 'error',
                            'message': f'无效的录制状态: {new_state}'
                        })
                
                # 处理AI音乐生成提示消息
                elif data.get('type') == 'ai_music_prompt':
                    prompt = data.get('data', '').strip()
                    
                    if prompt:
                        print(f"收到AI音乐生成提示: '{prompt}' 来自 {request.sid}")
                        
                        # 在单独线程中处理AI生成，避免阻塞
                        ai_thread = threading.Thread(
                            target=self._handle_ai_music_generation,
                            args=(prompt, request.sid),
                            daemon=True
                        )
                        ai_thread.start()
                        
                    else:
                        # 提示为空
                        emit('ai_generation_error', {
                            'type': 'ai_generation_error',
                            'message': 'AI音乐生成提示不能为空'
                        })
                
            except Exception as e:
                print(f"处理消息时出错: {e}")
                emit('error', {'message': f'处理消息时出错: {str(e)}'})
        
        @self.socketio.on('request_files')
        def handle_request_files():
            """处理文件列表请求"""
            try:
                # 重新获取文件列表
                response = self.app.test_client().get('/api/files')
                data = json.loads(response.data)
                emit('file_list', data)
            except Exception as e:
                emit('error', {'message': f'获取文件列表失败: {str(e)}'})
    
    def get_visualization_path(self):
        """获取visualization目录路径"""
        # 从eeg_music/server目录向上两级，然后进入visualization
        visualization_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'visualization')
        visualization_path = os.path.abspath(visualization_path)
        print(f"静态文件服务路径: {visualization_path}")
        return visualization_path
    
    def set_data_readers(self, arduino_reader=None, mindwave_reader=None):
        """设置数据读取器"""
        self.arduino_reader = arduino_reader
        self.mindwave_reader = mindwave_reader
        print(f"数据读取器已设置 - Arduino: {arduino_reader is not None}, Mindwave: {mindwave_reader is not None}")
    
    def get_music_recorder(self):
        """获取音乐数据记录器实例"""
        return self.music_recorder
    
    def update_session_name(self, session_name):
        """更新音乐数据记录器的session_name"""
        if self.music_recorder:
            self.music_recorder.session_name = session_name
            print(f"通过API更新MusicDataRecorder的session_name为: '{session_name}'")
            return True
        return False
    
    def get_recording_state(self):
        """获取当前录制状态"""
        return {
            'state': self.recording_state,
            'action': self.recording_action
        }
    
    def is_recording_active(self):
        """检查是否正在录制"""
        return self.recording_state == 'recording'
    
    def start_data_broadcast(self):
        """启动数据广播线程"""
        def broadcast_data():
            while True:
                try:
                    if not self.connected_clients:
                        time.sleep(0.1)  # 100ms
                        continue
                    
                    # 收集数据
                    data_to_send = {}
                    data_changed = False
                    
                    # 获取Arduino数据
                    if self.arduino_reader and hasattr(self.arduino_reader, 'current_data') and self.arduino_reader.current_data:
                        arduino_data = self.arduino_reader.current_data
                        data_to_send.update(arduino_data)
                    
                    # 获取Mindwave数据
                    if self.mindwave_reader and hasattr(self.mindwave_reader, 'current_data') and self.mindwave_reader.current_data:
                        mindwave_data = self.mindwave_reader.current_data
                        data_to_send.update(mindwave_data)
                    
                    # 检查数据是否有变化（简单的变化检测）
                    if data_to_send != self.last_data:
                        data_changed = True
                        self.last_data = data_to_send.copy()
                    
                    # 只有数据有变化时才发送
                    if data_changed and data_to_send:
                        data_to_send['timestamp'] = time.time()
                        # 使用SocketIO广播EEG数据 - 模拟原WebSocket的onmessage
                        self.socketio.emit('message', data_to_send)
                    
                    # 降低发送频率到30Hz，减少CPU占用 - 与原WebServer一致
                    time.sleep(0.033)  # 约30Hz
                    
                except Exception as e:
                    print(f"数据广播出错: {e}")
                    time.sleep(1)
        
        # 启动数据广播线程
        broadcast_thread = threading.Thread(target=broadcast_data, daemon=True)
        broadcast_thread.start()
        print("数据广播线程已启动")
    
    def run(self, arduino_reader, mindwave_reader):
        """启动Flask服务器 - 兼容原WebServer接口"""
        # 使用与原WebServer相同的端口配置
        server_address = "0.0.0.0"
        http_port = 5500  # 与原WebServer的HTTP端口一致
        
        print(f"Flask服务器启动: http://{server_address}:{http_port}")
        print(f"SocketIO服务器启动: ws://{server_address}:{http_port}")
        
        # 启动数据广播
        self.start_data_broadcast()
        
        # 启动服务器
        self.socketio.run(self.app, host=server_address, port=http_port, debug=False)

    def start_file_playback(self, filename):
        """启动历史文件回放"""
        if self.playback_active:
            print("回放已在进行中，停止当前回放")
            self.stop_file_playback()
        
        data_dir = os.path.join(os.getcwd(), 'data', 'music_notes')
        file_path = os.path.join(data_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return
        
        self.playback_active = True
        
        # 创建回放线程
        self.playback_thread = threading.Thread(
            target=self._playback_worker,
            args=(file_path,),
            daemon=True
        )
        self.playback_thread.start()
        print(f"开始回放文件: {filename}")
    
    def stop_file_playback(self):
        """停止当前回放"""
        self.playback_active = False
        if self.playback_thread and self.playback_thread.is_alive():
            print("等待回放线程结束...")
            # 线程会在检查到playback_active=False时自动退出
    
    def _playback_worker(self, file_path):
        """回放工作线程"""
        def visualization_callback(data):
            """可视化数据回调函数"""
            if not self.playback_active:
                return
            
            # 向所有连接的客户端发送可视化数据
            if self.connected_clients:
                self.socketio.emit('message', data)
        
        try:
            # 使用修改后的play_csv_file方法，传入回调函数
            self.music_player.play_csv_file(file_path, data_callback=visualization_callback)
        except Exception as e:
            print(f"回放过程中出错: {e}")
        finally:
            self.playback_active = False
            print("回放结束")
            
            # 通知前端回放结束
            if self.connected_clients:
                self.socketio.emit('playback_finished', {
                    'type': 'playback_finished',
                    'message': '回放已完成',
                    'timestamp': time.time()
                })

    def _handle_ai_music_generation(self, prompt, client_sid):
        """处理AI音乐生成"""
        try:
            print(f"开始处理AI音乐生成: {prompt}")
            
            # 检查DeepseekReader是否可用
            if not self.deepseek_reader:
                self.socketio.emit('ai_generation_error', {
                    'type': 'ai_generation_error',
                    'message': 'AI音乐生成服务不可用，请检查DeepSeek API配置'
                }, room=client_sid)
                return
            
            # 使用DeepseekReader生成音乐
            music_data = self.deepseek_reader.generate_music_from_prompt(prompt)
            
            if not music_data:
                self.socketio.emit('ai_generation_error', {
                    'type': 'ai_generation_error',
                    'message': 'AI未能生成音乐数据，请尝试修改提示词'
                }, room=client_sid)
                return
            
            print(f"AI生成了 {len(music_data)} 个音符")
            
            # 保存生成的音乐到文件
            filename = self.deepseek_reader.save_to_csv()
            
            # 播放生成的音乐
            self._play_ai_generated_music(music_data)
            
            # 发送可视化数据到前端
            self._send_ai_music_visualization_data(music_data)
            
            # 发送成功响应
            self.socketio.emit('ai_music_confirmation', {
                'type': 'ai_music_confirmation',
                'success': True,
                'message': 'AI音乐生成成功',
                'notes_count': len(music_data),
                'music_data': music_data,
                'filename': filename,
                'prompt': prompt,
                'timestamp': time.time()
            }, room=client_sid)
            
            print(f"AI音乐生成成功，文件保存为: {filename}")
            
        except Exception as e:
            print(f"AI音乐生成处理时出错: {e}")
            import traceback
            traceback.print_exc()
            
            self.socketio.emit('ai_generation_error', {
                'type': 'ai_generation_error',
                'message': f'AI音乐生成处理时出错: {str(e)}'
            }, room=client_sid)
    
    def _play_ai_generated_music(self, music_data):
        """播放AI生成的音乐"""
        try:
            # 在单独线程中播放音乐，避免阻塞
            def play_music():
                for i, note_data in enumerate(music_data):
                    try:
                        freq = note_data['freq']
                        duration = note_data['duration']
                        instrument = note_data['instrument']
                        intensity = note_data['intensity']
                        
                        # 播放音符
                        self.music_player.play_wav_note(
                            freq=freq,
                            duration=duration,
                            instrument=instrument,
                            intensity=intensity,
                            wait=False
                        )
                        
                        # 控制播放间隔
                        if i < len(music_data) - 1:
                            time.sleep(0.1)  # 间隔100ms
                            
                    except Exception as e:
                        print(f"播放音符时出错: {e}")
                        continue
            
            # 启动播放线程
            play_thread = threading.Thread(target=play_music, daemon=True)
            play_thread.start()
            
        except Exception as e:
            print(f"播放AI生成音乐时出错: {e}")
    
    def _send_ai_music_visualization_data(self, music_data):
        """发送AI音乐的可视化数据到前端"""
        try:
            def send_visualization():
                for i, note_data in enumerate(music_data):
                    try:
                        # 构造与Arduino数据兼容的可视化数据包
                        visualization_data = {
                            'freq': note_data['freq'],
                            'scale': 'AI Generated',
                            'note': hash(note_data['note_name']) % 8,  # 简单的音符索引映射
                            'distance': 25.0,  # 固定距离值
                            'potentiometer': note_data['intensity'] * 5.0,  # 强度映射到电位器
                            'rotary_potentiometer': str(note_data['intensity'] * 5.0),
                            'button_state': 0,
                            'timestamp': time.time(),
                            # 标记这是AI生成的数据
                            'ai_generated': True,
                            'note_name': note_data['note_name'],
                            'instrument': note_data['instrument']
                        }
                        
                        # 发送到所有连接的客户端
                        if self.connected_clients:
                            self.socketio.emit('message', visualization_data)
                        
                        # 控制发送间隔
                        if i < len(music_data) - 1:
                            time.sleep(0.1)  # 间隔100ms
                            
                    except Exception as e:
                        print(f"发送可视化数据时出错: {e}")
                        continue
            
            # 启动可视化数据发送线程
            viz_thread = threading.Thread(target=send_visualization, daemon=True)
            viz_thread.start()
            
        except Exception as e:
            print(f"发送AI音乐可视化数据时出错: {e}")

def main():
    """主函数 - 用于测试"""
    server = FlaskServer()
    
    try:
        server.run(None, None)
    except KeyboardInterrupt:
        print("\n✅ Flask服务器已停止")

if __name__ == '__main__':
    main() 