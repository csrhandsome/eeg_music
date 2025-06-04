// Socket.IO连接
let historySocket = null;

// 初始化Socket.IO连接
function initializeSocket() {
    try {
        // 动态获取服务器地址
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const hostname = window.location.hostname;
        const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
        const socketUrl = `${protocol}//${hostname}:${port}`;
        
        console.log(`[history] 尝试连接到Socket.IO服务器: ${socketUrl}`);
        
        historySocket = io(socketUrl, {
            transports: ['websocket', 'polling'],
            timeout: 20000,
            forceNew: true
        });
        
        historySocket.on('connect', () => {
            console.log('[history] Socket.IO连接成功');
        });
        
        historySocket.on('disconnect', () => {
            console.log('[history] Socket.IO连接断开');
        });
        
        historySocket.on('connect_error', (error) => {
            console.error(`[history] Socket.IO连接错误: ${error.message}`);
        });
        
        // 监听文件选择确认消息
        historySocket.on('file_selection_confirmation', (data) => {
            console.log('[history] 收到文件选择确认:', data);
            if (data.success) {
                // 可以在这里添加UI反馈，比如高亮选中的文件
                console.log(`文件 "${data.selected_file}" 选择成功，开始回放`);
                showPlaybackStatus('正在回放: ' + data.selected_file);
                
                // 隐藏文件列表
                hideFileList();
            }
        });
        
        // 监听文件信息消息
        historySocket.on('file_info', (data) => {
            console.log('[history] 收到文件信息:', data);
            if (data.exists) {
                console.log(`文件信息 - 大小: ${data.size}字节, 行数: ${data.lines}`);
            } else {
                console.warn(`文件不存在: ${data.filename}`);
            }
        });
        
        // 监听回放结束消息
        historySocket.on('playback_finished', (data) => {
            console.log('[history] 收到回放结束消息:', data);
            showPlaybackStatus('回放完成');
            
            // 重新显示文件列表
            showFileList();
            
            // 清除播放状态
            clearPlayingStatus();
            
            setTimeout(() => {
                hidePlaybackStatus();
            }, 3000);
        });
        
        // 监听实时数据消息（用于可视化）
        historySocket.on('message', (data) => {
            // 如果存在音游可视化实例，转发数据给它处理
            if (window.musicGame && data.playback_mode) {
                // 处理回放数据，触发可视化效果
                window.musicGame.processArduinoData(data);
            }
        });
        
        // 监听错误消息
        historySocket.on('error', (data) => {
            console.error('[history] 收到错误消息:', data.message);
        });
        
        return historySocket;
    } catch (error) {
        console.error('[history] Socket.IO初始化失败:', error);
        return null;
    }
}

// 显示回放状态
function showPlaybackStatus(message) {
    // 创建或更新状态显示元素
    let statusElement = document.getElementById('playback-status');
    if (!statusElement) {
        statusElement = document.createElement('div');
        statusElement.id = 'playback-status';
        statusElement.style.cssText = `
            position: fixed;
            top: 70px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            z-index: 1001;
            font-size: 14px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        `;
        document.body.appendChild(statusElement);
    }
    statusElement.textContent = message;
    statusElement.style.display = 'block';
}

// 隐藏回放状态
function hidePlaybackStatus() {
    const statusElement = document.getElementById('playback-status');
    if (statusElement) {
        statusElement.style.display = 'none';
    }
}

// 隐藏文件列表
function hideFileList() {
    const historyContainer = document.querySelector('.history-container');
    if (historyContainer) {
        historyContainer.style.display = 'none';
        historyContainer.style.transition = 'all 0.3s ease';
    }
}

// 显示文件列表
function showFileList() {
    const historyContainer = document.querySelector('.history-container');
    if (historyContainer) {
        historyContainer.style.display = 'flex';
        historyContainer.style.transition = 'all 0.3s ease';
    }
}

// 从服务器获取文件列表
async function fetchFileList() {
    try {
        // 尝试从当前服务器的API获取文件列表
        const response = await fetch('/api/files');
        
        if (!response.ok) {
            throw new Error(`API请求失败: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        return data.files || [];
    } catch (error) {
        console.error('获取文件列表失败:', error);
        // 如果API请求失败，返回空数组
        return [];
    }
}

// 加载文件列表
async function loadFileList() {
    const fileListContainer = document.getElementById('file-list');
    
    // 显示加载状态
    fileListContainer.innerHTML = `
        <div class="file-list-content">
            <div style="text-align: center; color: #7f8c8d; padding: 20px;">
                正在加载文件列表...
            </div>
        </div>
    `;
    
    // 从服务器获取文件列表
    const musicNotesFiles = await fetchFileList();
    
    if (musicNotesFiles.length === 0) {
        fileListContainer.innerHTML = `
            <div class="file-list-content">
                <div style="text-align: center; color: #7f8c8d; padding: 20px;">
                    暂无音乐记录文件
                </div>
            </div>
        `;
        return;
    }
    
    // 按文件名（时间戳）降序排序
    const sortedFiles = musicNotesFiles.sort((a, b) => b.name.localeCompare(a.name));
    
    const fileListHTML = sortedFiles.map(file => `
        <div class="file-item" onclick="selectFile('${file.name}')">
            <div class="file-name">${file.name}</div>
            <div class="file-info">
                <div class="file-size">${file.size}</div>
                <div class="file-lines">${file.lines}</div>
            </div>
        </div>
    `).join('');
    
    fileListContainer.innerHTML = `<div class="file-list-content">${fileListHTML}</div>`;
}

// 选择文件
function selectFile(fileName) {
    console.log('选择了文件:', fileName);
    
    // 移除之前选中的高亮
    const previousSelected = document.querySelector('.file-item.selected');
    if (previousSelected) {
        previousSelected.classList.remove('selected');
    }
    
    // 高亮当前选中的文件
    const fileItems = document.querySelectorAll('.file-item');
    fileItems.forEach(item => {
        const fileNameElement = item.querySelector('.file-name');
        if (fileNameElement && fileNameElement.textContent === fileName) {
            item.classList.add('selected');
            // 添加播放中的状态
            item.classList.add('playing');
        }
    });
    
    // 发送文件点击事件到Socket.IO服务器
    if (historySocket && historySocket.connected) {
        const message = {
            type: 'file_selected',
            data: fileName,
            timestamp: Date.now()
        };
        historySocket.emit('message', message);
        console.log('已发送文件选择事件到后端:', fileName);
    } else {
        console.warn('Socket.IO连接未建立，无法发送文件选择事件');
        // 尝试重新连接
        if (!historySocket) {
            historySocket = initializeSocket();
        }
    }
}

// 清除所有文件的播放状态
function clearPlayingStatus() {
    const playingItems = document.querySelectorAll('.file-item.playing');
    playingItems.forEach(item => {
        item.classList.remove('playing');
        item.classList.remove('selected');
    });
}

// 页面加载完成后初始化文件列表
document.addEventListener('DOMContentLoaded', function() {
    // 初始化Socket.IO连接
    historySocket = initializeSocket();
    
    // 加载文件列表
    loadFileList();
}); 