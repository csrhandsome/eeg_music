let currentMode = 'game'; // 'game' 或 'traditional'

function goBack() {
    window.location.href = 'welcomepage.html';
}

function switchToOriginal() {
    // 3D版本已停用
    alert('3D版本功能已停用，请继续使用当前2D版本');
}

function toggleVisualizationMode() {
    if (currentMode === 'game') {
        // 切换到传统模式
        window.location.href = 'processing.html';
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

// 强制录制模态窗口控制
let currentButtonState = 0;
let isRecordingModalShown = false;

function showRecordingModal() {
    const modal = document.getElementById('recording-modal');
    modal.style.display = 'flex';
    isRecordingModalShown = true;
    
    // 禁用背景交互
    document.body.style.overflow = 'hidden';
    
    // 聚焦到输入框
    setTimeout(() => {
        document.getElementById('recording-song-name').focus();
    }, 300);
}

function closeRecordingModal() {
    // 只有在button_state为0时才能关闭
    if (currentButtonState === 0) {
        const modal = document.getElementById('recording-modal');
        modal.style.display = 'none';
        isRecordingModalShown = false;
        document.body.style.overflow = 'auto';
    }
}

function sendRecordingSongName() {
    const songNameInput = document.getElementById('recording-song-name');
    const songName = songNameInput.value.trim();
    
    if (!songName) {
        alert('录制期间必须输入歌曲名称！');
        songNameInput.focus();
        return;
    }
    
    // 发送录制歌曲名称到WebSocket服务器
    if (window.musicGame && window.musicGame.socket && window.musicGame.socket.readyState === WebSocket.OPEN) {
        const message = {
            type: 'recording_song_name',
            data: songName,
            timestamp: Date.now()
        };
        window.musicGame.socket.send(JSON.stringify(message));
        
        // 清空输入框
        songNameInput.value = '';
        
        // 显示成功提示
        const button = document.getElementById('confirm-recording');
        const originalText = button.textContent;
        button.textContent = '✓ 已保存';
        button.style.background = '#4CAF50';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
        
        console.log('已发送录制歌曲名称:', songName);
    } else {
        alert('WebSocket连接未建立,请稍后再试！');
    }
}

// 监听button_state变化
function handleButtonStateChange(newState) {
    if (newState === 1 && currentButtonState === 0) {
        // 从未录制变为录制状态 - 强制弹出窗口
        showRecordingModal();
    } else if (newState === 0 && currentButtonState === 1) {
        // 从录制变为未录制状态 - 允许关闭窗口
        closeRecordingModal();
    }
    currentButtonState = newState;
}

// 阻止ESC键关闭模态窗口（在录制期间）
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isRecordingModalShown && currentButtonState === 1) {
        e.preventDefault();
        alert('录制期间无法关闭窗口，请输入歌曲名称！');
    }
});

// 录制模态窗口回车键功能
document.addEventListener('DOMContentLoaded', function() {
    const recordingInput = document.getElementById('recording-song-name');
    if (recordingInput) {
        recordingInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendRecordingSongName();
            }
        });
    }
});

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

function toggleMobileInput() {
    const inputEl = document.querySelector('.mobile-input-panel');
    
    if (!inputEl) {
        console.error('找不到输入面板元素');
        return;
    }
    
    mobileInputVisible = !mobileInputVisible;
    
    if (mobileInputVisible) {
        // 显示面板
        inputEl.classList.add('show');
        
        // 聚焦到输入框
        setTimeout(() => {
            const input = document.getElementById('mobile-song-input');
            if (input) input.focus();
        }, 300);
    } else {
        // 隐藏面板
        inputEl.classList.remove('show');
    }
}

function closeMobileInput() {
    if (mobileInputVisible) {
        mobileInputVisible = false;
        
        const inputEl = document.querySelector('.mobile-input-panel');
        
        if (inputEl) inputEl.classList.remove('show');
    }
}

function sendMobileSongName() {
    const input = document.getElementById('mobile-song-input');
    const songName = input.value.trim();
    
    if (!songName) {
        alert('请输入歌曲名称！');
        input.focus();
        return;
    }
    
    // 发送到WebSocket服务器
    if (window.musicGame && window.musicGame.socket && window.musicGame.socket.readyState === WebSocket.OPEN) {
        const message = {
            type: 'song_name',
            data: songName,
            timestamp: Date.now()
        };
        window.musicGame.socket.send(JSON.stringify(message));
        
        // 清空输入框并关闭面板
        input.value = '';
        closeMobileInput();
        
        // 显示成功提示
        alert('歌曲名称已发送: ' + songName);
        console.log('已发送歌曲名称:', songName);
    } else {
        alert('WebSocket连接未建立,请稍后再试！');
    }
}

// 移动端回车键支持和ESC键关闭
document.addEventListener('DOMContentLoaded', function() {
    const mobileInput = document.getElementById('mobile-song-input');
    if (mobileInput) {
        mobileInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMobileSongName();
            }
        });
    }
});

// ESC键关闭输入面板
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && mobileInputVisible) {
        closeMobileInput();
    }
});

function updateMobileStatus() {
    const statusText = document.getElementById('mobile-status-text');
    const arduinoData = document.getElementById('mobile-arduino-data');
    
    if (window.musicGame && window.musicGame.socket) {
        const status = window.musicGame.socket.readyState === WebSocket.OPEN ? '已连接' : '连接中...';
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

// 新增的导航函数
function goToRecord() {
    window.location.href = 'record.html';
}

function goToHistory() {
    window.location.href = 'history.html';
}

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

// 音符弹出框管理
function clearNotePopups() {
    const container = document.getElementById('note-popup-container');
    if (container) {
        // 清除所有现有的弹出框
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }
    }
}

// 手动创建测试音符弹出框（用于调试）
function createTestNotePopup(noteIndex = 0, frequency = 440) {
    if (window.musicGame) {
        const scale = 'C Major';
        window.musicGame.createNotePopup(frequency, scale);
    }
}

// 手动创建测试飘动情绪SVG（用于调试）
function createTestFloatingEmotion(noteIndex = 0, frequency = 440) {
    if (window.musicGame) {
        // 设置测试情绪
        window.musicGame.mindwaveData.mood = Math.floor(Math.random() * 4);
        window.musicGame.createFloatingEmotion(noteIndex, frequency);
        console.log(`创建测试飘动情绪: 音符${noteIndex}, 频率${frequency}Hz, 情绪${window.musicGame.mindwaveData.mood}`);
    }
}

// 测试所有音符块
function testAllNoteBlocks() {
    if (window.musicGame) {
        for (let i = 0; i < 10; i++) {
            setTimeout(() => {
                const frequency = 261.63 + i * 50; // 简单的频率递增
                createTestFloatingEmotion(i, frequency);
            }, i * 500); // 每500ms创建一个
        }
    }
}

// 窗口大小改变时重新计算音符弹出框位置
window.addEventListener('resize', function() {
    // 清除现有弹出框，避免位置错乱
    clearNotePopups();
});

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 确保音符弹出框容器存在
    const container = document.getElementById('note-popup-container');
    if (!container) {
        console.warn('音符弹出框容器未找到');
    }
    
    // 初始化情绪显示
    updateEmotionDisplay(0);
    
    console.log('音符弹出框系统初始化完成');
    
    // 添加键盘快捷键用于测试
    document.addEventListener('keydown', function(e) {
        if (e.key === 't' || e.key === 'T') {
            // 按T键测试单个飘动情绪
            const randomNote = Math.floor(Math.random() * 10);
            const randomFreq = 200 + Math.random() * 1000;
            createTestFloatingEmotion(randomNote, randomFreq);
        } else if (e.key === 'a' || e.key === 'A') {
            // 按A键测试所有音符块
            testAllNoteBlocks();
        }
    });
});