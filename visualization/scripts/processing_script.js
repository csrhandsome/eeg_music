function goBack() {
    window.location.href = 'welcomepage.html';
}

function switchToMusicGame() {
    window.location.href = 'music_game_p5.html';
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
    
    // 发送录制歌曲名称到Socket.IO服务器
    if (window.traditionalVisualization && window.traditionalVisualization.socket && window.traditionalVisualization.socket.connected) {
        const message = {
            type: 'recording_song_name',
            data: songName,
            timestamp: Date.now()
        };
        window.traditionalVisualization.socket.emit('message', message);
        
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
        alert('Socket.IO连接未建立,请稍后再试！');
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

let songInputVisible = false;

// 显示歌曲输入面板
function showSongInputPanel() {
    const modalEl = document.querySelector('.song-input-modal');
    const overlayEl = document.querySelector('.song-input-overlay');
    
    if (!modalEl || !overlayEl) {
        console.error('找不到输入面板或遮罩元素');
        return;
    }
    
    songInputVisible = true;
    
    // 显示面板
    overlayEl.classList.add('show');
    modalEl.classList.add('show');
    
    // 聚焦到输入框
    setTimeout(() => {
        const input = document.getElementById('song-name-input');
        if (input) input.focus();
    }, 300);
    
    // 禁用背景滚动
    document.body.style.overflow = 'hidden';
}

// 关闭歌曲输入面板
function closeSongInputModal() {
    if (songInputVisible) {
        songInputVisible = false;
        
        const modalEl = document.querySelector('.song-input-modal');
        const overlayEl = document.querySelector('.song-input-overlay');
        
        if (modalEl) modalEl.classList.remove('show');
        if (overlayEl) overlayEl.classList.remove('show');
        
        // 恢复背景滚动
        document.body.style.overflow = 'auto';
    }
}

// 发送歌曲名称
function sendSongName() {
    const input = document.getElementById('song-name-input');
    const songName = input.value.trim();
    
    if (!songName) {
        alert('请输入歌曲名称！');
        input.focus();
        return;
    }
    
    // 发送到Socket.IO服务器
    if (window.traditionalVisualization && window.traditionalVisualization.socket && window.traditionalVisualization.socket.connected) {
        const message = {
            type: 'song_name',
            data: songName,
            timestamp: Date.now()
        };
        window.traditionalVisualization.socket.emit('message', message);
        
        // 清空输入框并关闭面板
        input.value = '';
        closeSongInputModal();
        
        // 显示成功提示
        alert('歌曲名称已发送: ' + songName);
        console.log('已发送歌曲名称:', songName);
    } else {
        alert('Socket.IO连接未建立,请稍后再试！');
    }
}

// 键盘事件支持
document.addEventListener('DOMContentLoaded', function() {
    const songInput = document.getElementById('song-name-input');
    if (songInput) {
        songInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendSongName();
            }
        });
    }
});

// ESC键关闭输入面板
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && songInputVisible) {
        closeSongInputModal();
    }
}); 