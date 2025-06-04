// AI音乐生成页面专用JavaScript
// 基于record.html的文件名输入处理方式，适配AI提示功能

// AI生成状态管理
let aiGenerationActive = false;

// 生成音乐函数
function generateMusic() {
    const promptInput = document.getElementById('ai-prompt-input');
    const prompt = promptInput.value.trim();
    
    if (!prompt) {
        alert('请输入音乐生成提示！');
        promptInput.focus();
        return;
    }
    
    if (aiGenerationActive) {
        alert('AI正在生成中，请稍候...');
        return;
    }
    
    // 设置生成状态
    aiGenerationActive = true;
    
    // 显示加载状态
    showAILoadingModal();
    
    // 发送AI提示到Socket.IO服务器
    if (window.musicGame && window.musicGame.socket && window.musicGame.socket.connected) {
        const message = {
            type: 'ai_music_prompt',
            data: prompt,
            timestamp: Date.now()
        };
        window.musicGame.socket.emit('message', message);
        console.log('已发送AI音乐生成提示:', prompt);
        
        // 关闭提示输入模态框
        closePromptModal();
        
        // 清空输入框
        promptInput.value = '';
        
    } else {
        // 连接失败处理
        aiGenerationActive = false;
        hideAILoadingModal();
        alert('Socket.IO连接未建立，请稍后再试！');
        console.warn('Socket.IO连接未建立，无法发送AI提示');
    }
}

// 取消提示输入
function cancelPrompt() {
    closePromptModal();
    // 清空输入框
    document.getElementById('ai-prompt-input').value = '';
    console.log('取消AI音乐生成');
}

// 显示提示输入模态框
function showPromptModal() {
    const modal = document.getElementById('ai-prompt-modal');
    if (modal) {
        modal.classList.add('show');
        // 聚焦到输入框
        setTimeout(() => {
            const input = document.getElementById('ai-prompt-input');
            if (input) {
                input.focus();
            }
        }, 100);
    }
}

// 关闭提示输入模态框
function closePromptModal() {
    const modal = document.getElementById('ai-prompt-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// 显示AI加载状态模态框
function showAILoadingModal() {
    const modal = document.getElementById('ai-loading-modal');
    if (modal) {
        modal.classList.add('show');
    }
}

// 隐藏AI加载状态模态框
function hideAILoadingModal() {
    const modal = document.getElementById('ai-loading-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// 显示生成成功模态框
function showGenerationSuccessModal() {
    const modal = document.getElementById('generation-success-modal');
    if (modal) {
        modal.classList.add('show');
        // 3秒后自动关闭
        setTimeout(() => {
            closeGenerationSuccessModal();
        }, 3000);
    }
}

// 关闭生成成功模态框
function closeGenerationSuccessModal() {
    const modal = document.getElementById('generation-success-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// 处理AI音乐生成响应
function handleAIMusicResponse(data) {
    console.log('[ai_generate] 收到AI音乐生成响应:', data);
    
    // 隐藏加载状态
    hideAILoadingModal();
    
    // 重置生成状态
    aiGenerationActive = false;
    
    if (data.success) {
        console.log(`AI音乐生成成功，生成了 ${data.notes_count} 个音符`);
        
        // 显示成功提示
        showGenerationSuccessModal();
        
        // 如果有生成的音乐数据，可以在这里处理
        if (data.music_data) {
            console.log('生成的音乐数据:', data.music_data);
        }
        
        if (data.filename) {
            console.log('音乐已保存为:', data.filename);
        }
        
    } else {
        // 生成失败
        alert(`AI音乐生成失败: ${data.message || '未知错误'}`);
        console.error('AI音乐生成失败:', data);
    }
}

// 处理AI生成错误
function handleAIGenerationError(errorMessage) {
    console.error('[ai_generate] AI生成错误:', errorMessage);
    
    // 隐藏加载状态
    hideAILoadingModal();
    
    // 重置生成状态
    aiGenerationActive = false;
    
    // 显示错误提示
    alert(`AI音乐生成失败: ${errorMessage}`);
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('[ai_generate] AI音乐生成页面初始化');
    
    // AI提示输入框回车键支持
    const promptInput = document.getElementById('ai-prompt-input');
    if (promptInput) {
        promptInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                generateMusic();
            }
        });
    }
    
    // 监听键盘快捷键（空格键显示输入框）
    document.addEventListener('keydown', function(e) {
        // 空格键显示AI提示输入框
        if (e.code === 'Space' && e.target === document.body) {
            e.preventDefault();
            showPromptModal();
        }
        
        // ESC键关闭模态框
        if (e.key === 'Escape') {
            closePromptModal();
            hideAILoadingModal();
            closeGenerationSuccessModal();
        }
    });
    
    // 等待音游系统初始化完成后，监听AI相关的Socket.IO事件
    setTimeout(() => {
        if (window.musicGame && window.musicGame.socket) {
            // 监听AI音乐生成确认消息
            window.musicGame.socket.on('ai_music_confirmation', handleAIMusicResponse);
            
            // 监听AI生成错误消息
            window.musicGame.socket.on('ai_generation_error', function(data) {
                handleAIGenerationError(data.message || '未知错误');
            });
            
            console.log('[ai_generate] AI音乐生成Socket.IO事件监听器已设置');
        } else {
            console.warn('[ai_generate] 音游系统未初始化，无法设置Socket.IO监听器');
        }
    }, 1000); // 等待1秒确保音游系统初始化完成
    
    // 自动显示提示输入框
    setTimeout(() => {
        showPromptModal();
    }, 500);
});

// 添加点击页面显示输入框的功能（可选）
document.addEventListener('click', function(e) {
    // 点击空白区域显示输入框
    if (e.target === document.body || e.target.id === 'p5-canvas-container') {
        showPromptModal();
    }
});

// 返回主页函数
function goToPlay() {
    window.location.href = 'music_game_p5.html';
}

console.log('[ai_generate] AI音乐生成脚本已加载'); 