// 音游可视化系统 - 使用 D3.js 实现4轨道下落动画
class MusicGameVisualization {
    constructor() {
        this.socket = null;
        this.gameContainer = null;
        this.svg = null;
        this.tracks = [];
        this.trackWidth = 80;
        this.trackHeight = 600;
        this.trackSpacing = 20;
        this.dropDuration = 2000; // 下落动画持续时间(ms)
        this.dropObjectSize = 40;
        
        // 重连计时器
        this.reconnectTimer = null;
        this.RECONNECT_INTERVAL = 3000; // 重连间隔3秒
        
        // Arduino数据
        this.arduinoData = {
            distance: 0,
            scale: "",
            note: 0,
            frequency: 0,
            potentiometer: 0,
            rotary_potentiometer: "",
            button_state: 0,
            timestamp: 0
        };
        
        // 音阶频率数据 - 与Arduino保持一致
        this.scaleFrequencies = {
            "C Major": [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, 1046.50],
            "G Major": [392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 739.99, 783.99, 880.00, 987.77, 1046.50, 1174.66, 1318.51, 1479.98, 1567.98],
            "D Major": [293.66, 329.63, 369.99, 392.00, 440.00, 493.88, 554.37, 587.33, 659.25, 739.99, 783.99, 880.00, 987.77, 1108.73, 1174.66],
            "E Minor": [329.63, 369.99, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 739.99, 783.99, 880.00, 987.77, 1046.50, 1174.66, 1318.51],
            "A Minor": [440.00, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, 1046.50, 1174.66, 1318.51, 1396.91, 1567.98, 1760.00]
        };
        
        // 下落物图片配置 - 可自定义
        this.dropImages = {
            track1: "🎵", // 轨道1使用音符emoji作为默认
            track2: "🎶",
            track3: "🎼",
            track4: "♪"
        };
        
        this.init();
    }
    
    init() {
        this.setupGameContainer();
        this.setupWebSocket();
        this.createTracks();
        this.setupEventListeners();
    }
    
    setupGameContainer() {
        // 创建游戏容器 - 调整位置以适应横屏
        this.gameContainer = d3.select("body")
            .append("div")
            .attr("id", "music-game-container")
            .style("position", "absolute")
            .style("top", "40%")
            .style("left", "40%")
            .style("transform", "translate(-50%, -50%) perspective(800px) rotateX(15deg)")
            .style("z-index", "10")
            .style("pointer-events", "none");
        
        // 创建SVG画布 - 调整尺寸和样式
        const totalWidth = (this.trackWidth + this.trackSpacing) * 4 - this.trackSpacing;
        this.svg = this.gameContainer
            .append("svg")
            .attr("width", totalWidth)
            .attr("height", this.trackHeight)
            .style("background", "rgba(0, 0, 0, 0.4)")
            .style("border", "2px solid rgba(255, 255, 255, 0.4)")
            .style("border-radius", "15px")
            .style("box-shadow", "0 15px 35px rgba(0, 0, 0, 0.3)");
    }
    
    createTracks() {
        const trackColors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA726"];
        
        // 定义轨道的3D透视参数
        const perspectiveOffset = 15; // 纵深偏移量
        const trackDepthSpacing = 8; // 轨道深度间距
        
        for (let i = 0; i < 4; i++) {
            const x = i * (this.trackWidth + this.trackSpacing);
            const depthOffset = i * trackDepthSpacing; // 每个轨道的深度偏移
            
            // 创建轨道背景
            const track = this.svg.append("g")
                .attr("class", `track track-${i + 1}`)
                .attr("transform", `translate(${x}, 0)`);
            
            // 定义3D轨道的四个顶点（梯形效果）
            const topWidth = this.trackWidth - depthOffset;
            const bottomWidth = this.trackWidth;
            const sideOffset = depthOffset / 2;
            
            // 轨道背景 - 使用多边形创建透视效果
            const trackPath = `M ${sideOffset} ${perspectiveOffset + depthOffset} 
                              L ${topWidth + sideOffset} ${perspectiveOffset + depthOffset}
                              L ${bottomWidth} ${this.trackHeight}
                              L 0 ${this.trackHeight} Z`;
            
            track.append("path")
                .attr("d", trackPath)
                .attr("fill", trackColors[i])
                .attr("opacity", 0.25)
                .attr("stroke", trackColors[i])
                .attr("stroke-width", 2);
            
            // 轨道侧边阴影效果
            const shadowPath = `M 0 ${perspectiveOffset + depthOffset}
                               L ${sideOffset} ${perspectiveOffset + depthOffset}
                               L 0 ${this.trackHeight} Z`;
            
            track.append("path")
                .attr("d", shadowPath)
                .attr("fill", trackColors[i])
                .attr("opacity", 0.15);
            
            // 轨道标签
            track.append("text")
                .attr("x", this.trackWidth / 2)
                .attr("y", 25 + depthOffset)
                .attr("text-anchor", "middle")
                .attr("fill", "white")
                .attr("font-size", "12px")
                .attr("font-weight", "bold")
                .attr("text-shadow", "0 0 5px rgba(0,0,0,0.8)")
                .text(`轨道${i + 1}`);
            
            // 底部目标区域 - 梯形设计
            const targetPath = `M ${sideOffset + 5} ${this.trackHeight - 60}
                               L ${topWidth + sideOffset - 5} ${this.trackHeight - 60}
                               L ${bottomWidth - 5} ${this.trackHeight - 10}
                               L 5 ${this.trackHeight - 10} Z`;
            
            track.append("path")
                .attr("class", "target-area")
                .attr("d", targetPath)
                .attr("fill", trackColors[i])
                .attr("opacity", 0.6)
                .attr("stroke", trackColors[i])
                .attr("stroke-width", 2);
            
            // 轨道中央引导线
            for (let j = 1; j < 6; j++) {
                const lineY = (this.trackHeight / 6) * j + perspectiveOffset + depthOffset;
                const lineTopX = sideOffset + (topWidth / 6) * j;
                const lineBottomX = (bottomWidth / 6) * j;
                
                track.append("line")
                    .attr("x1", lineTopX)
                    .attr("y1", lineY)
                    .attr("x2", lineBottomX)
                    .attr("y2", this.trackHeight - 10)
                    .attr("stroke", trackColors[i])
                    .attr("stroke-width", 1)
                    .attr("opacity", 0.3)
                    .attr("stroke-dasharray", "3,3");
            }
            
            this.tracks.push({
                element: track,
                color: trackColors[i],
                x: x,
                depthOffset: depthOffset,
                topWidth: topWidth,
                bottomWidth: bottomWidth,
                sideOffset: sideOffset
            });
        }
    }
    
    // 根据当前音阶和频率映射到轨道
    mapFrequencyToTrack(frequency, currentScale) {
        const scaleFreqs = this.scaleFrequencies[currentScale];
        if (!scaleFreqs) return 0; // 默认轨道0
        
        // 找到最接近的音符
        let minDiff = Infinity;
        let noteIndex = 0;
        
        for (let i = 0; i < scaleFreqs.length; i++) {
            const diff = Math.abs(frequency - scaleFreqs[i]);
            if (diff < minDiff) {
                minDiff = diff;
                noteIndex = i;
            }
        }
        
        // 将15个音符映射到4个轨道
        // 策略：按音高范围分组
        if (noteIndex < 4) return 0;      // 低音区 -> 轨道1
        else if (noteIndex < 8) return 1; // 中低音区 -> 轨道2  
        else if (noteIndex < 12) return 2; // 中高音区 -> 轨道3
        else return 3;                     // 高音区 -> 轨道4
    }
    
    // 创建下落物动画
    createDropObject(trackIndex, frequency) {
        const track = this.tracks[trackIndex];
        if (!track) return;
        
        // 计算起始和结束位置（适应透视轨道）
        const startX = track.sideOffset + track.topWidth / 2;
        const endX = track.bottomWidth / 2;
        const perspectiveOffset = 15;
        const startY = perspectiveOffset + track.depthOffset;
        
        const dropGroup = track.element.append("g")
            .attr("class", "drop-object")
            .attr("transform", `translate(${startX}, ${startY})`);
        
        // 根据频率调整下落物大小和颜色强度
        const sizeScale = d3.scaleLinear()
            .domain([200, 1800])
            .range([0.6, 1.0])
            .clamp(true);
        
        const initialSize = this.dropObjectSize * 0.8 * sizeScale(frequency);
        const finalSize = this.dropObjectSize * sizeScale(frequency);
        
        // 创建下落物 - 使用圆形和文字
        const circle = dropGroup.append("circle")
            .attr("r", initialSize / 2)
            .attr("fill", track.color)
            .attr("opacity", 0.9)
            .attr("stroke", "white")
            .attr("stroke-width", 2)
            .attr("filter", "drop-shadow(0 2px 4px rgba(0,0,0,0.3))");
        
        // 添加图标/文字
        const text = dropGroup.append("text")
            .attr("text-anchor", "middle")
            .attr("dy", "0.35em")
            .attr("fill", "white")
            .attr("font-size", `${initialSize * 0.6}px`)
            .attr("font-weight", "bold")
            .attr("text-shadow", "0 0 3px rgba(0,0,0,0.8)")
            .text(this.dropImages[`track${trackIndex + 1}`]);
        
        // 下落动画 - 沿着透视轨道移动
        dropGroup.transition()
            .duration(this.dropDuration)
            .ease(d3.easeQuadIn)
            .attr("transform", `translate(${endX}, ${this.trackHeight - 30})`)
            .on("end", () => {
                // 到达底部时的效果
                this.createHitEffect(trackIndex);
                dropGroup.remove();
            });
        
        // 大小变化动画（透视效果）
        circle.transition()
            .duration(this.dropDuration)
            .ease(d3.easeQuadIn)
            .attr("r", finalSize / 2);
        
        // 文字大小变化
        text.transition()
            .duration(this.dropDuration)
            .ease(d3.easeQuadIn)
            .attr("font-size", `${finalSize * 0.6}px`);
        
        // 添加旋转动画
        circle.transition()
            .duration(this.dropDuration)
            .ease(d3.easeLinear)
            .attrTween("transform", () => {
                return (t) => `rotate(${t * 720})`;
            });
    }
    
    // 创建击中效果
    createHitEffect(trackIndex) {
        const track = this.tracks[trackIndex];
        
        // 在目标区域中心创建爆炸效果
        const hitX = track.bottomWidth / 2;
        const hitY = this.trackHeight - 30;
        
        const effectGroup = track.element.append("g")
            .attr("class", "hit-effect")
            .attr("transform", `translate(${hitX}, ${hitY})`);
        
        // 创建多个粒子
        for (let i = 0; i < 12; i++) {
            const angle = (i / 12) * Math.PI * 2;
            const distance = 25;
            const dx = Math.cos(angle) * distance;
            const dy = Math.sin(angle) * distance;
            
            effectGroup.append("circle")
                .attr("r", 2)
                .attr("fill", track.color)
                .attr("opacity", 1)
                .attr("filter", "drop-shadow(0 0 3px rgba(255,255,255,0.8))")
                .transition()
                .duration(600)
                .attr("transform", `translate(${dx}, ${dy})`)
                .attr("opacity", 0)
                .attr("r", 6)
                .on("end", function() {
                    d3.select(this).remove();
                });
        }
        
        // 中心闪光效果
        effectGroup.append("circle")
            .attr("r", 5)
            .attr("fill", "white")
            .attr("opacity", 1)
            .transition()
            .duration(200)
            .attr("r", 20)
            .attr("opacity", 0)
            .on("end", function() {
                d3.select(this).remove();
            });
        
        // 轨道闪烁效果 - 对所有路径元素应用
        track.element.selectAll("path")
            .transition()
            .duration(100)
            .attr("opacity", 0.9)
            .transition()
            .duration(100)
            .attr("opacity", function() {
                return d3.select(this).classed("target-area") ? 0.6 : 0.25;
            });
    }
    
    // 设置图片路径
    setDropImage(trackNumber, imagePath) {
        if (trackNumber >= 1 && trackNumber <= 4) {
            this.dropImages[`track${trackNumber}`] = imagePath;
        }
    }
    
    // 处理Arduino数据
    processArduinoData(data) {
        this.arduinoData = { ...this.arduinoData, ...data };
        
        // 如果有有效的频率和音阶数据，创建下落物
        if (data.freq && data.freq > 100 && data.scale) {
            const trackIndex = this.mapFrequencyToTrack(data.freq, data.scale);
            this.createDropObject(trackIndex, data.freq);
        }
    }
    
    // WebSocket设置 - 与processing.js保持一致的完整处理
    setupWebSocket() {
        const socketUrl = 'ws://localhost:8765';
        
        // 清除旧的重连计时器
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        // 如果已有连接，先关闭
        if (this.socket) {
            this.socket.close();
        }
        
        this.socket = new WebSocket(socketUrl);
        
        // 连接建立时触发
        this.socket.onopen = (event) => {
            console.log('[open] 音游WebSocket连接已建立');
            document.getElementById('status').textContent = '已连接!';
            document.getElementById('status').style.color = 'lime';
        };
        
        // 接收到服务器消息时触发
        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                // 处理欢迎消息
                if (data.message && data.message === "Welcome to the WebSocket server!") {
                    console.log("收到服务器欢迎消息");
                    return;
                }
                
                // 更新Arduino数据 - 修正字段映射
                if (data.distance !== undefined) {
                    this.arduinoData.distance = data.distance;
                }
                if (data.scale !== undefined) {
                    this.arduinoData.scale = data.scale;
                }
                if (data.note !== undefined) {
                    this.arduinoData.note = data.note;
                }
                if (data.freq !== undefined) {  
                    this.arduinoData.frequency = data.freq;
                }
                if (data.potentiometer !== undefined) {
                    this.arduinoData.potentiometer = data.potentiometer;
                }
                if (data.rotary_potentiometer !== undefined) {
                    this.arduinoData.rotary_potentiometer = data.rotary_potentiometer;
                }
                                 if (data.button_state !== undefined) {
                     const oldState = this.arduinoData.button_state;
                     this.arduinoData.button_state = data.button_state;
                     
                     // 通知HTML处理button_state变化
                     if (typeof handleButtonStateChange === 'function') {
                         handleButtonStateChange(data.button_state);
                     }
                 }
                if (data.timestamp !== undefined) {
                    this.arduinoData.timestamp = data.timestamp;
                }
                
                // 更新数据显示 - 显示更多信息
                let formattedData = `
距离: ${this.arduinoData.distance ? this.arduinoData.distance.toFixed(2) : 0}cm
音阶: ${this.arduinoData.scale || 'N/A'}
音符: ${this.arduinoData.note || 0}
频率: ${this.arduinoData.frequency ? this.arduinoData.frequency.toFixed(2) : 0}Hz 
电位器: ${this.arduinoData.potentiometer ? this.arduinoData.potentiometer.toFixed(2) : 0}V
旋转电位器: ${this.arduinoData.rotary_potentiometer || 'N/A'}V
按钮状态: ${this.arduinoData.button_state === 1 ? '录制中' : '未录制'}
`;
                document.getElementById('arduino-data').textContent = formattedData;
                
                // 处理音游逻辑 - 如果有有效的频率和音阶数据，创建下落物
                if (data.freq && data.freq > 100 && data.scale) {
                    this.processArduinoData(data);
                }
                
            } catch (error) {
                console.error('解析JSON数据错误:', error);
            }
        };
        
        // 连接关闭时触发
        this.socket.onclose = (event) => {
            if (event.wasClean) {
                console.log(`[close] 音游连接已关闭, 代码=${event.code} 原因=${event.reason}`);
                document.getElementById('status').textContent = `断开连接: ${event.reason || '连接关闭'}`;
            } else {
                console.error('[close] 音游连接中断');
                document.getElementById('status').textContent = '连接中断，正在尝试重连...';
            }
            document.getElementById('status').style.color = 'red';
            
            // 设置自动重连
            this.reconnectTimer = setTimeout(() => {
                console.log("尝试重新连接音游WebSocket...");
                this.setupWebSocket();
            }, this.RECONNECT_INTERVAL);
        };
        
        // 发生错误时触发
        this.socket.onerror = (error) => {
            console.error(`[error] 音游WebSocket错误: ${error.message}`);
            document.getElementById('status').textContent = `WebSocket错误,正在尝试重连...`;
            document.getElementById('status').style.color = 'red';
        };
    }
    
    // 事件监听器
    setupEventListeners() {
        // 窗口大小改变时调整位置
        window.addEventListener('resize', () => {
            // 可以在这里添加响应式调整逻辑
        });
    }
    
    // 清理资源
    destroy() {
        if (this.socket) {
            this.socket.close();
        }
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        if (this.gameContainer) {
            this.gameContainer.remove();
        }
    }
}

// 全局变量
let musicGame = null;

// 初始化函数
function initMusicGame() {
    if (musicGame) {
        musicGame.destroy();
    }
    musicGame = new MusicGameVisualization();
    return musicGame;
}

// 导出到全局作用域
window.MusicGameVisualization = MusicGameVisualization;
window.initMusicGame = initMusicGame; 