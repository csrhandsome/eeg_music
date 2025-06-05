let currentMode = 'game'; // 'game' 或 'traditional'

// 录制页面相关变量
let recordTimerInterval;
let recordStartTime;
let isRecording = false;

function goBack() {
    window.location.href = 'welcomepage.html';
}

function switchToOriginal() {
    // 3D版本已停用
    alert('3D版本功能已停用,请继续使用当前2D版本');
}

function toggleVisualizationMode() {
    if (currentMode === 'game') {
        // 传统模式暂时不可用
        alert('传统可视化模式暂时不可用，请继续使用当前2D音游模式');
    }
}

function resetGame() {
    if (window.musicGame) {
        window.musicGame.reset();
    } else {
        alert('游戏尚未初始化，无法重置');
    }
}

// 侧边面板切换功能
function toggleSidePanel(panelId) {
    const panel = document.getElementById(panelId);
    panel.classList.toggle('expanded');
}

// 按钮检测和弹出窗口相关组件已删除

// ==================== 录制页面专用功能 ====================

// 录制状态管理
let recordingState = 'stopped'; // 'stopped', 'recording', 'paused'
let pausedByStop = false; // 标记是否是通过停止按钮暂停的
let totalElapsedTime = 0; // 累计录制时间（毫秒）
let lastStartTime = 0; // 最近一次开始录制的时间

// 发送录制状态到后端
function sendRecordingState(state, action = null) {
    if (window.musicGame && window.musicGame.socket && window.musicGame.socket.connected) {
        const message = {
            type: 'recording_state',
            data: {
                state: state,
                action: action,
                timestamp: Date.now()
            }
        };
        window.musicGame.socket.emit('message', message);
        console.log(`已发送录制状态到后端: ${state} (action: ${action})`);
    } else {
        console.warn('Socket.IO连接未建立，无法发送录制状态');
    }
}

// 更新录制计时器显示
function updateRecordTimer() {
    if (isRecording && lastStartTime) {
        const currentElapsed = totalElapsedTime + (Date.now() - lastStartTime);
        const hours = Math.floor(currentElapsed / 3600000);
        const minutes = Math.floor((currentElapsed % 3600000) / 60000);
        const seconds = Math.floor((currentElapsed % 60000) / 1000);
        
        document.getElementById('timer-display').textContent = 
            `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// 暂停录制并更新累计时间
function pauseRecording() {
    if (isRecording && lastStartTime) {
        totalElapsedTime += (Date.now() - lastStartTime);
        isRecording = false;
        clearInterval(recordTimerInterval);
    }
}

// 继续录制
function resumeRecording() {
    isRecording = true;
    lastStartTime = Date.now();
    recordTimerInterval = setInterval(updateRecordTimer, 1000);
}

// 显示暂停遮罩
function showPauseOverlay() {
    const modal = document.getElementById('success-modal');
    const title = modal.querySelector('.success-title');
    const subtitle = modal.querySelector('.success-subtitle');
    
    title.textContent = '录制已暂停';
    subtitle.textContent = '点击继续按钮恢复录制';
    modal.classList.add('show');
}

// 隐藏暂停遮罩
function hidePauseOverlay() {
    document.getElementById('success-modal').classList.remove('show');
}

// 显示保存成功提示
function showSuccessMessage() {
    const modal = document.getElementById('success-modal');
    const title = modal.querySelector('.success-title');
    const subtitle = modal.querySelector('.success-subtitle');
    
    title.textContent = '保存成功！';
    subtitle.textContent = '请在心音轨迹中查看';
    modal.classList.add('show');
}

// 退出录制
function quitRecord() {
    if (isRecording) {
        stopRecord();
    }
    // 返回主页
    window.location.href = 'music_game_p5.html';
}

// 开始录制按钮逻辑
function startRecord() {
    if (recordingState === 'stopped') {
        // 第一次点击：开始录制和计时
        recordingState = 'recording';
        totalElapsedTime = 0;
        lastStartTime = Date.now();
        resumeRecording();
        
        // 发送开始录制状态到后端
        sendRecordingState('recording', 'start');
        
        console.log('开始录制');
    } else if (recordingState === 'recording') {
        // 第二次点击：暂停计时并弹出文件名输入
        recordingState = 'paused';
        pauseRecording();
        
        // 发送暂停录制状态到后端（因为弹出文件名窗口）
        sendRecordingState('paused', 'filename_modal_open');
        
        document.getElementById('filename-modal').classList.add('show');
        console.log('录制暂停，等待输入文件名');
    }
}

// 停止录制按钮逻辑
function stopRecord() {
    const stopButton = document.querySelector('.record-controls-bottom button:nth-child(3)');
    const stopImg = stopButton.querySelector('img');
    
    if (recordingState === 'recording' && !pausedByStop) {
        // 点击停止：暂停录制并显示遮罩，切换图标
        pausedByStop = true;
        pauseRecording();
        
        // 发送暂停录制状态到后端
        sendRecordingState('paused', 'stop_button');
        
        showPauseOverlay();
        stopImg.src = 'assets/start_play.png';
        stopImg.alt = '继续录制';
        stopButton.title = '继续录制';
        console.log('录制已暂停');
    } else if (pausedByStop) {
        // 再次点击：继续录制，隐藏遮罩，恢复图标
        pausedByStop = false;
        hidePauseOverlay();
        resumeRecording();
        
        // 发送继续录制状态到后端
        sendRecordingState('recording', 'resume');
        
        stopImg.src = 'assets/stop.svg';
        stopImg.alt = '停止录制';
        stopButton.title = '停止录制';
        console.log('录制继续');
    }
}

// 确认文件名
function confirmFilename() {
    const filename = document.getElementById('filename-input').value.trim();
    if (filename) {
        // 发送文件名到Socket.IO服务器
        if (window.musicGame && window.musicGame.socket && window.musicGame.socket.connected) {
            const message = {
                type: 'save_filename',
                data: filename,
                timestamp: Date.now()
            };
            window.musicGame.socket.emit('message', message);
            console.log('已发送录制文件名:', filename);
        } else {
            console.warn('Socket.IO连接未建立，无法发送文件名');
        }
        
        // 发送结束录制状态到后端
        sendRecordingState('stopped', 'save_and_finish');
        
        document.getElementById('filename-modal').classList.remove('show');
        // 显示成功提示模态框
        showSuccessMessage();
        // 1.5秒后自动关闭成功提示框
        setTimeout(() => {
            closeSuccessModal();
        }, 1500);
        
        // 重置录制状态
        recordingState = 'stopped';
        totalElapsedTime = 0;
        lastStartTime = 0;
        pausedByStop = false;
        const timerDisplay = document.getElementById('timer-display');
        if (timerDisplay) {
            timerDisplay.textContent = '00:00:00';
        }
        console.log('录制已保存，文件名：', filename);
    } else {
        alert('请输入文件名');
    }
}

// 关闭成功提示模态框
function closeSuccessModal() {
    document.getElementById('success-modal').classList.remove('show');
    // 清空文件名输入框
    document.getElementById('filename-input').value = '';
}

// 取消文件名输入
function cancelFilename() {
    document.getElementById('filename-modal').classList.remove('show');
    document.getElementById('filename-input').value = '';
    
    // 如果当前是暂停状态，恢复录制
    if (recordingState === 'paused') {
        recordingState = 'recording';
        resumeRecording();
        
        // 发送继续录制状态到后端
        sendRecordingState('recording', 'cancel_filename_continue');
        
        console.log('取消文件名输入，继续录制');
    }
}

// ==================== 通用导航功能 ====================

function goToRecord() {
    window.location.href = 'record.html';
}

function goToHistory() {
    window.location.href = 'history.html';
}

function goToPlay() {
    window.location.href = 'music_game_p5.html';
}

function goToWelcomepage() {
    window.location.href = 'welcomepage.html';
}

function goToAiGenerate() {
    window.location.href = 'ai_generate.html';
}

// ==================== 移动端输入面板功能 ====================

// 移动端专用函数
let mobileStatusVisible = false;
let mobileInputVisible = false;

function toggleMobileStatus() {
    const statusEl = document.querySelector('.mobile-status-center');
    if (!statusEl) {
        console.error('找不到 .mobile-status-center 元素');
        return;
    }
    mobileStatusVisible = !mobileStatusVisible;
    statusEl.style.display = mobileStatusVisible ? 'block' : 'none';
}

function sendMobileSongName() {
    const input = document.getElementById('mobile-song-input');
    const songName = input.value.trim();
    
    if (!songName) {
        alert('请输入歌曲名称！');
        input.focus();
        return;
    }
    
    // 发送到Socket.IO服务器
    if (window.musicGame && window.musicGame.socket && window.musicGame.socket.connected) {
        const message = {
            type: 'song_name',
            data: songName,
            timestamp: Date.now()
        };
        window.musicGame.socket.emit('message', message);
        
        // 清空输入框并关闭面板
        input.value = '';
        closeMobileInput();
        
        // 显示成功提示
        alert('歌曲名称已发送: ' + songName);
        console.log('已发送歌曲名称:', songName);
    } else {
        alert('Socket.IO连接未建立,请稍后再试！');
    }
}

function updateMobileStatus() {
    const statusText = document.getElementById('mobile-status-text');
    const arduinoData = document.getElementById('mobile-arduino-data');
    
    if (window.musicGame && window.musicGame.socket) {
        const status = window.musicGame.socket.connected ? '已连接' : '连接中...';
        if (statusText) statusText.textContent = status;
        
        const data = window.musicGame.arduinoData;
        if (arduinoData && data) {
            arduinoData.textContent = `音符:${data.note} 频率:${data.frequency.toFixed(1)}Hz`;
        }
    }
}

// 检测移动端并显示轨道信息
function detectMobile() {
    const isMobile = window.innerWidth <= 768;
    const trackInfo = document.querySelector('.mobile-track-info');
    
    if (trackInfo) trackInfo.style.display = isMobile ? 'flex' : 'none';
    
    // 更新状态显示
    if (isMobile && window.musicGame) {
        updateMobileStatus();
    }
}

// 窗口大小变化时重新检测
window.addEventListener('resize', detectMobile);

// 页面加载时检测
window.addEventListener('load', function() {
    detectMobile();
    // 定期更新移动端状态
    setInterval(updateMobileStatus, 1000);
});

// 情绪状态管理
function updateEmotionDisplay(emotion) {
    const emotionElement = document.getElementById('mobile-emotion-data');
    if (emotionElement) {
        const emotionNames = {
            0: '快乐',
            1: '悲伤', 
            2: '愤怒',
            3: '平静'
        };
        const emotionName = emotionNames[emotion] || '平静';
        emotionElement.textContent = `心情:${emotionName}`;
    }
}


// 窗口大小改变时重新计算音符弹出框位置
window.addEventListener('resize', function() {
    // 由于使用P5.js绘制音符块，窗口调整会自动重新计算位置
});

// ==================== 事件监听器设置 ====================

// 阻止ESC键关闭模态窗口（在录制期间）
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isRecordingModalShown && currentButtonState === 1) {
        e.preventDefault();
        alert('录制期间无法关闭窗口，请输入歌曲名称！');
    }
    
    // ESC键关闭输入面板
    if (e.key === 'Escape' && mobileInputVisible) {
        closeMobileInput();
    }
});

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 录制模态窗口回车键功能
    const recordingInput = document.getElementById('recording-song-name');
    if (recordingInput) {
        recordingInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendRecordingSongName();
            }
        });
    }
    
    // 移动端输入框回车键支持
    const mobileInput = document.getElementById('mobile-song-input');
    if (mobileInput) {
        mobileInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMobileSongName();
            }
        });
    }
    
    // 文件名输入框回车键支持（录制页面）
    const filenameInput = document.getElementById('filename-input');
    if (filenameInput) {
        filenameInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                confirmFilename();
            }
        });
    }
    
    // 初始化录制计时器显示（录制页面）
    const timerDisplay = document.getElementById('timer-display');
    if (timerDisplay) {
        timerDisplay.textContent = '00:00:00';
    }
    
    // 初始化情绪显示
    updateEmotionDisplay(0);
    
    console.log('音游系统初始化完成 - 使用P5.js飘动情绪显示');
    
});