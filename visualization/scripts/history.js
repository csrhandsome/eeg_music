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
    // 这里可以添加文件选择后的处理逻辑，比如播放该文件的音乐记录
}

// 页面加载完成后初始化文件列表
document.addEventListener('DOMContentLoaded', function() {
    loadFileList();
}); 