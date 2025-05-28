// 音游可视化系统 - P5.js卡通2D版本
class MusicGameVisualizationP5 {
    constructor() {
        this.socket = null;
        this.noteBlocks = [];
        this.floatingEmotions = [];
        this.backgroundStars = [];
        this.clouds = [];
        
        // 游戏参数
        this.noteCount = 10; // 十个音符
        this.noteBlockWidth = 80;
        this.noteBlockHeight = 50;
        this.noteBlockSpacing = 10;
        this.svgDuration = 4000; // SVG飘动持续时间(ms)
        this.svgSize = 60;
        
        // 重连计时器
        this.reconnectTimer = null;
        this.RECONNECT_INTERVAL = 3000; // 重连间隔3秒
        
        // 防止重复触发的时间间隔
        this.lastTriggerTime = {};
        this.TRIGGER_COOLDOWN = 500; // 500ms冷却时间
        
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
        this.mindwaveData = {
            attention: 0,
            meditation: 0,
            rawValue: 0,
            delta: 0,
            theta: 0,
            lowAlpha: 0,
            highAlpha: 0,
            lowBeta: 0,
            highBeta: 0,
            lowGamma: 0,
            midGamma: 0,
            poorSignal: 0,
        };
        // 音阶频率数据 - 与Arduino保持一致，扩展到完整的音符范围
        this.scaleFrequencies = {
            "C Major": [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25],
            "G Major": [392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 739.99, 783.99, 880.00, 987.77],
            "D Major": [293.66, 329.63, 369.99, 392.00, 440.00, 493.88, 554.37, 587.33, 659.25, 739.99],
            "E Minor": [329.63, 369.99, 392.00, 440.00, 493.88, 523.25, 587.33, 659.25, 739.99, 783.99],
            "A Minor": [440.00, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, 1046.50]
        };
        
        // 音符名称映射 - do, re, mi, fa, sol, la, si, do#, re#, mi#
        this.noteNames = ['do', 're', 'mi', 'fa', 'sol', 'la', 'si', 'do#', 're#', 'mi#'];
        
        // 情绪PNG映射 - 只存储路径，不在构造函数中加载
        this.emotionPNGs = {
            0: 'assets/emotion/happy.png',    // 快乐
            1: 'assets/emotion/sad.png',      // 悲伤  
            2: 'assets/emotion/anger.png',    // 愤怒
            3: 'assets/emotion/peace.png'     // 平静
        };
        
        this.emotionNames = {
            0: '快乐',
            1: '悲伤', 
            2: '愤怒',
            3: '平静'
        };
        
        // 音符块颜色 - 白色为主
        this.noteBlockColor = [255, 255, 255];
        this.noteBlockActiveColor = [255, 255, 100]; // 激活时的颜色
        
        // 预加载情绪SVG图像
        this.emotionImages = {};
        
        // 背景装饰
        this.rainbowColors = [
            [255, 99, 132], [255, 159, 64], [255, 206, 86], 
            [75, 192, 192], [54, 162, 235], [153, 102, 255]
        ];
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.createNoteBlocks();
        this.createBackgroundElements();
        // 注意：SVG图像将在P5.js的preload阶段加载
    }
    
    
    createNoteBlocks() {
        this.noteBlocks = [];
        
        // 根据屏幕大小调整音符块参数
        const isMobile = window.innerWidth <= 768;
        const isLandscape = window.innerWidth > window.innerHeight;
        
        if (isMobile) {
            this.noteBlockWidth = isLandscape ? 60 : 70;
            this.noteBlockHeight = isLandscape ? 50 : 60; // 增加高度
            this.noteBlockSpacing = 0; // 贴在一起，间距为0
        } else {
            this.noteBlockWidth = 80;
            this.noteBlockHeight = 70; // 增加高度
            this.noteBlockSpacing = 0; // 贴在一起，间距为0
        }
        
        // 计算右侧音符块位置
        const containerHeight = window.innerHeight;
        const totalHeight = this.noteCount * this.noteBlockHeight + (this.noteCount - 1) * this.noteBlockSpacing;
        const startY = (containerHeight - totalHeight) / 2;
        const rightX = window.innerWidth - this.noteBlockWidth - 20; // 修复：距离右边20px
        
        for (let i = 0; i < this.noteCount; i++) {
            // 计算y坐标：从下往上排列，所以最高音符在最上面,对于html坐标的最上面
            const y = startY + (this.noteCount - 1 - i) * (this.noteBlockHeight + this.noteBlockSpacing);
            this.noteBlocks.push({
                x: rightX,
                y: y,
                width: this.noteBlockWidth,
                height: this.noteBlockHeight,
                noteName: this.noteNames[i],
                noteIndex: i,
                active: false,
                activationTime: 0,
                glow: 0
            });
        }
    }
    
    createBackgroundElements() {
        // 创建背景星星
        this.backgroundStars = [];
        for (let i = 0; i < 20; i++) {
            this.backgroundStars.push({
                x: random(-400, 400),
                y: random(-300, 300),
                size: random(2, 6),
                twinkle: random(0, TWO_PI),
                speed: random(0.02, 0.05)
            });
        }
    }
    
    // 根据当前音阶和频率映射到音符索引
    mapFrequencyToNote(frequency, currentScale) {
        const scaleFreqs = this.scaleFrequencies[currentScale];
        if (!scaleFreqs) return 0; // 默认音符0
        
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
        
        return noteIndex;
    }
    
    // 创建飘动的情绪SVG
    createFloatingEmotion(noteIndex, frequency) {
        if (noteIndex < 0 || noteIndex >= this.noteBlocks.length) return;
        
        // 防止重复触发：检查冷却时间
        const currentTime = millis();
        const lastTime = this.lastTriggerTime[noteIndex] || 0;
        if (currentTime - lastTime < this.TRIGGER_COOLDOWN) {
            return; // 还在冷却期，不创建新的SVG
        }
        this.lastTriggerTime[noteIndex] = currentTime;
        
        const noteBlock = this.noteBlocks[noteIndex];
        const currentEmotion = this.mindwaveData.mood || 0;
        
        // 根据频率调整SVG大小
        const sizeScale = map(constrain(frequency, 200, 1800), 200, 1800, 0.8, 1.3);
        const size = this.svgSize * sizeScale;
        
        const floatingEmotion = {
            noteIndex: noteIndex,
            // 从音符块位置开始
            x: noteBlock.x + noteBlock.width / 2,
            y: noteBlock.y + noteBlock.height / 2,
            size: size,
            frequency: frequency,
            startTime: millis(),
            targetX: -size, // 飘到屏幕左边外
            rotation: 0,
            rotationSpeed: random(-0.02, 0.02),
            active: true,
            emotion: currentEmotion,
            // 固定波浪形飘动路径参数
            waveAmplitude: 30, // 固定波浪幅度
            waveFrequency: 0.01, // 固定波浪频率
            initialY: noteBlock.y + noteBlock.height / 2, // 记录初始Y位置
            wavePhase: 0 // 波浪相位
        };
        
        this.floatingEmotions.push(floatingEmotion);
        
        // 激活对应的音符块 - 只是简单的过渡效果
        noteBlock.active = true;
        noteBlock.activationTime = millis();
        noteBlock.glow = 255;
        
        console.log(`创建飘动情绪: 音符${noteIndex}, 情绪${currentEmotion}, 位置(${floatingEmotion.x}, ${floatingEmotion.y})`);
    }
    
    // 绘制右侧音符块
    drawNoteBlocks() {
        for (let i = 0; i < this.noteBlocks.length; i++) {
            const block = this.noteBlocks[i];
            
            // 更新动画效果
            if (block.glow > 0) {
                block.glow *= 0.95; // 发光衰减
            }
            
            // 修复：简化激活动画效果，像钢琴按键一样
            let scaleEffect = 1.0;
            let yOffset = 0;
            if (block.active) {
                const elapsed = millis() - block.activationTime;
                if (elapsed < 300) { // 激活动画持续300ms
                    // 简单的按下效果
                    const progress = elapsed / 300;
                    yOffset = sin(progress * PI) * 2; // 轻微下压效果
                    scaleEffect = 1.0 + sin(progress * PI) * 0.03; // 轻微缩放
                } else {
                    block.active = false;
                }
            }
            
            push();
            translate(block.x + block.width/2, block.y + block.height/2 + yOffset);
            scale(scaleEffect);
            
            // 绘制主体 - 透明的音符块
            if (block.active) {
                // 激活时稍微可见
                fill(255, 255, 255, 100);
            } else {
                // 平时完全透明
                fill(255, 255, 255, 100);
            }
            stroke(255, 255, 255, 100);
            strokeWeight(2);
            rect(-block.width/2, -block.height/2, block.width, block.height, 8);
            
            // 绘制发光效果 - 根据当前情绪设置颜色
            if (block.glow > 0) {
                const currentEmotion = this.mindwaveData.mood || 0;
                let glowColor;
                
                switch(currentEmotion) {
                    case 0: // happy - fcc68f
                        glowColor = [252, 198, 143];
                        break;
                    case 1: // sad - cee9f5  
                        glowColor = [206, 233, 245];
                        break;
                    case 2: // anger - FDA598
                        glowColor = [253, 165, 152];
                        break;
                    case 3: // peace - e1d6f5
                        glowColor = [225, 214, 245];
                        break;
                    default:
                        glowColor = [255, 255, 100]; // 默认黄色
                }
                
                drawingContext.shadowColor = `rgba(${glowColor[0]}, ${glowColor[1]}, ${glowColor[2]}, ${block.glow/255})`;
                drawingContext.shadowBlur = 15;
                fill(glowColor[0], glowColor[1], glowColor[2], block.glow);
                stroke(glowColor[0], glowColor[1], glowColor[2], block.glow);
                strokeWeight(4);
                rect(-block.width/2, -block.height/2, block.width, block.height, 8);
                drawingContext.shadowBlur = 0;
            }
            
            // 绘制音符名称
            fill(0,0,0);
            noStroke();
            textAlign(CENTER, CENTER);
            textSize(14);
            textStyle(BOLD);
            text(block.noteName.toUpperCase(), 0, 0);
            
            pop();
        }
    }
    
    // 更新飘动的情绪SVG
    updateFloatingEmotions() {
        for (let i = this.floatingEmotions.length - 1; i >= 0; i--) {
            const emotion = this.floatingEmotions[i];
            if (!emotion.active) {
                this.floatingEmotions.splice(i, 1);
                continue;
            }
            
            const elapsed = millis() - emotion.startTime;
            const progress = elapsed / this.svgDuration;
            
            // 检查是否应该移除
            if (progress >= 1.0 || emotion.x <= emotion.targetX) {
                emotion.active = false;
                this.floatingEmotions.splice(i, 1);
                console.log(`移除飘动情绪: 索引${i}`);
                continue;
            }
            
            // 水平移动：从音符块位置到屏幕左边
            const startX = this.noteBlocks[emotion.noteIndex].x + this.noteBlocks[emotion.noteIndex].width / 2;
            emotion.x = lerp(startX, emotion.targetX, progress);
            
            // 固定波浪形飘动路径
            const waveOffset = sin(emotion.x * emotion.waveFrequency) * emotion.waveAmplitude;
            emotion.y = emotion.initialY + waveOffset;
            
            // 更新旋转
            emotion.rotation += emotion.rotationSpeed;
            
            // 边界检查，防止飘出屏幕上下边界
            emotion.y = constrain(emotion.y, emotion.size/2, height - emotion.size/2);
        }
    }
    
    // 绘制飘动的情绪SVG
    drawFloatingEmotions() {
        for (const emotion of this.floatingEmotions) {
            if (!emotion.active) continue;
            
            push();
            translate(emotion.x, emotion.y);
            rotate(emotion.rotation);
            
            // 获取对应的图像
            const imageToDraw = this.emotionImages[emotion.emotion];
            
            // 检查图像是否已加载且有效
            if (this.emotionImagesLoaded && imageToDraw && typeof imageToDraw === 'object' && imageToDraw.width > 0) {
                // 显示PNG图像
                try {
                    imageMode(CENTER);
                    image(imageToDraw, 0, 0, emotion.size, emotion.size);
                } catch (error) {
                    console.error('绘制情绪图像时出错:', error);
                    // 如果绘制失败，显示备用图形
                    this.drawFallbackEmotion(emotion);
                }
            } else {
                // 如果PNG未加载或加载失败，显示简单的几何图形作为备用
                this.drawFallbackEmotion(emotion);
            }
            
            pop();
        }
    }
    
    // 绘制备用情绪图形的辅助方法
    drawFallbackEmotion(emotion) {
        fill(255, 255, 255, 200);
        stroke(100);
        strokeWeight(2);
        const symbolSize = emotion.size;
        switch(emotion.emotion) {
            case 0: // 快乐
                // 画一个简单的笑脸
                ellipse(0, 0, symbolSize);
                fill(0);
                noStroke();
                ellipse(-symbolSize*0.15, -symbolSize*0.1, symbolSize*0.08);
                ellipse(symbolSize*0.15, -symbolSize*0.1, symbolSize*0.08);
                stroke(0);
                strokeWeight(2);
                noFill();
                arc(0, symbolSize*0.05, symbolSize*0.3, symbolSize*0.2, 0, PI);
                break;
            case 1: // 悲伤
                // 画一个哭脸
                ellipse(0, 0, symbolSize);
                fill(0);
                noStroke();
                ellipse(-symbolSize*0.15, -symbolSize*0.1, symbolSize*0.08);
                ellipse(symbolSize*0.15, -symbolSize*0.1, symbolSize*0.08);
                stroke(0);
                strokeWeight(2);
                noFill();
                arc(0, symbolSize*0.15, symbolSize*0.3, symbolSize*0.2, PI, TWO_PI);
                break;
            case 2: // 愤怒
                // 画一个愤怒符号
                fill(255, 100, 100);
                ellipse(0, 0, symbolSize);
                fill(0);
                noStroke();
                rect(-symbolSize*0.2, -symbolSize*0.05, symbolSize*0.4, symbolSize*0.1);
                rect(-symbolSize*0.05, -symbolSize*0.2, symbolSize*0.1, symbolSize*0.4);
                break;
            case 3: // 平静
                // 画一个平静符号
                fill(150, 255, 150);
                ellipse(0, 0, symbolSize);
                fill(0);
                noStroke();
                ellipse(-symbolSize*0.15, -symbolSize*0.1, symbolSize*0.08);
                ellipse(symbolSize*0.15, -symbolSize*0.1, symbolSize*0.08);
                ellipse(0, symbolSize*0.05, symbolSize*0.15, symbolSize*0.08);
                break;
        }
    }
    
    // 绘制背景装饰
    drawBackground() {
        // 更新云朵位置
        // for (let cloud of this.clouds) {
        //     cloud.x += cloud.speed;
        //     if (cloud.x > width/2 + 100) {
        //         cloud.x = -width/2 - 100;
        //     }
        // }
        
        // // 绘制云朵
        // for (let cloud of this.clouds) {
        //     push();
        //     translate(cloud.x, cloud.y);
        //     fill(255, 255, 255, cloud.opacity);
        //     noStroke();
            
        //     // 简单的云朵形状
        //     ellipse(0, 0, cloud.size);
        //     ellipse(-cloud.size * 0.3, 0, cloud.size * 0.7);
        //     ellipse(cloud.size * 0.3, 0, cloud.size * 0.7);
        //     ellipse(0, -cloud.size * 0.3, cloud.size * 0.8);
            
        //     pop();
        // }
        
        // 绘制背景星星
        // for (let star of this.backgroundStars) {
        //     star.twinkle += star.speed;
            
        //     push();
        //     translate(star.x, star.y);
            
        //     const brightness = (sin(star.twinkle) + 1) * 0.5;
        //     fill(255, 255, 200, brightness * 200);
        //     noStroke();
            
        //     // 简单的星星形状
        //     beginShape();
        //     for (let i = 0; i < 10; i++) {
        //         const angle = (i / 10) * TWO_PI;
        //         const radius = (i % 2 === 0) ? star.size : star.size * 0.4;
        //         const x = cos(angle) * radius;
        //         const y = sin(angle) * radius;
        //         vertex(x, y);
        //     }
        //     endShape(CLOSE);
            
        //     pop();
        // }
    }
    
    // 处理Arduino数据
    processArduinoData(data) {
        this.arduinoData = { ...this.arduinoData, ...data };
        
        // 如果有有效的频率和音阶数据，创建飘动情绪和音符
        if (data.freq && data.freq > 100 && data.scale) {
            const noteIndex = this.mapFrequencyToNote(data.freq, data.scale);       
            // 创建飘动的情绪图像
            this.createFloatingEmotion(noteIndex, data.freq);
        }
    }
    
    // WebSocket设置 
    // 从Websocket里面收集arduino和mindwave的数据
    setupWebSocket() {
        // 动态获取服务器地址
        const hostname = window.location.hostname;
        const socketUrl = `ws://${hostname}:8765`;
        
        console.log(`尝试连接到WebSocket服务器: ${socketUrl}`);
        
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
            const statusElement = document.getElementById('status');
            if (statusElement) {
                statusElement.textContent = '已连接!';
                statusElement.style.color = 'lime';
            }
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
                
                // 更新Arduino数据
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


                // 更新Mindwave数据
                if (data.attention !== undefined) {
                    this.mindwaveData.attention = data.attention;
                }
                if (data.meditation !== undefined) {
                    this.mindwaveData.meditation = data.meditation;
                }
                if (data.rawValue !== undefined) {
                    this.mindwaveData.rawValue = data.rawValue;
                }
                if (data.delta !== undefined) {
                    this.mindwaveData.delta = data.delta;
                }
                if (data.theta !== undefined) {
                    this.mindwaveData.theta = data.theta;
                }
                if (data.lowAlpha !== undefined) {
                    this.mindwaveData.lowAlpha = data.lowAlpha;
                }
                if (data.highAlpha !== undefined) {
                    this.mindwaveData.highAlpha = data.highAlpha;
                }
                if (data.lowBeta !== undefined) {
                    this.mindwaveData.lowBeta = data.lowBeta;
                }   
                if (data.highBeta !== undefined) {
                    this.mindwaveData.highBeta = data.highBeta;
                }
                if (data.lowGamma !== undefined) {
                    this.mindwaveData.lowGamma = data.lowGamma;
                }
                if (data.midGamma !== undefined) {
                    this.mindwaveData.midGamma = data.midGamma;
                }
                if (data.poorSignal !== undefined) {
                    this.mindwaveData.poorSignal = data.poorSignal;
                }
                if (data.blinkStrength !== undefined) {
                    this.mindwaveData.blinkStrength = data.blinkStrength;
                }
                if (data.mood !== undefined) {
                    this.mindwaveData.mood = data.mood;
                }
                // 刚开始mindwave没有打开
                if (data.mood == undefined) {
                    this.mindwaveData.mood = 0;
                }
                
                // 更新情绪状态显示
                const emotionElement = document.getElementById('mobile-emotion-data');
                if (emotionElement && this.mindwaveData.mood !== undefined) {
                    const emotionName = this.emotionNames[this.mindwaveData.mood] || '平静';
                    emotionElement.textContent = `心情:${emotionName}`;
                }
                
                // 处理音游逻辑
                if (data.freq && data.freq > 100 && data.scale) {
                    this.processArduinoData(data);
                } 
            } catch (error) {
                console.error('解析JSON数据错误:', error);
            }
        };
        
        // 连接关闭时触发
        this.socket.onclose = (event) => {
            const statusElement = document.getElementById('status');
            if (statusElement) {
                if (event.wasClean) {
                    console.log(`[close] 音游连接已关闭, 代码=${event.code} 原因=${event.reason}`);
                    statusElement.textContent = `断开连接: ${event.reason || '连接关闭'}`;
                } else {
                    console.error('[close] 音游连接中断');
                    statusElement.textContent = '连接中断，正在尝试重连...';
                }
                statusElement.style.color = 'red';
            }
            
            // 设置自动重连
            this.reconnectTimer = setTimeout(() => {
                console.log("尝试重新连接音游WebSocket...");
                this.setupWebSocket();
            }, this.RECONNECT_INTERVAL);
        };
        
        // 发生错误时触发
        this.socket.onerror = (error) => {
            console.error(`[error] 音游WebSocket错误: ${error.message}`);
            const statusElement = document.getElementById('status');
            if (statusElement) {
                statusElement.textContent = `WebSocket错误,正在尝试重连...`;
                statusElement.style.color = 'red';
            }
        };
    }
    
    // 重置游戏
    reset() {
        this.floatingEmotions = [];
        // 重置所有音符块状态
        for (let block of this.noteBlocks) {
            block.active = false;
            block.glow = 0;
        }
        console.log('游戏已重置');
    }
    
    // 清理资源
    destroy() {
        if (this.socket) {
            this.socket.close();
        }
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
    }
}

// P5.js 全局变量
let musicGame;
let emotionImages = {}; // 全局情绪图像对象
let imagesLoaded = false; // 图像加载状态

// 手动加载图像的函数 - 使用async/await
async function loadEmotionImagesManually() {
    console.log('开始异步加载情绪图像');
    const emotions = ['happy', 'sad', 'anger', 'peace'];
    
    for (let index = 0; index < emotions.length; index++) {
        const emotion = emotions[index];
        try {
            console.log(`开始加载情绪图像: ${emotion}`);
            emotionImages[index] = await loadImage(`assets/emotion/${emotion}.png`);
            console.log(`✓ 情绪图像 ${emotion} 加载成功: ${emotionImages[index].width}x${emotionImages[index].height}`);
        } catch (error) {
            console.error(`✗ 情绪图像 ${emotion} 加载失败:`, error);
            emotionImages[index] = null;
        }
    }
    
    imagesLoaded = true;
    console.log('所有情绪图像加载完成');
}

// P5.js setup函数
async function setup() {
    console.log('setup函数开始执行');
    
    // 创建全屏2D画布
    let canvas = createCanvas(windowWidth, windowHeight);
    canvas.parent('p5-canvas-container');
    
    // 在P5.js 2.x中，直接在setup中加载图像
    await loadEmotionImagesManually();
    
    // 验证图像加载状态
    console.log('=== 图像加载状态验证 ===');
    for (let i = 0; i < 4; i++) {
        const img = emotionImages[i];
        console.log(`图像 ${i}:`, {
            exists: !!img,
            type: typeof img,
            width: img ? img.width : 'N/A',
            height: img ? img.height : 'N/A',
            isPromise: img instanceof Promise,
            constructor: img ? img.constructor.name : 'N/A'
        });
    }
    
    // 初始化音游系统
    musicGame = new MusicGameVisualizationP5();
    
    // 将加载的图像传递给musicGame
    musicGame.emotionImages = emotionImages;
    musicGame.emotionImagesLoaded = imagesLoaded;
    
    // 设置全局变量以便HTML访问
    window.musicGame = musicGame;
    
    console.log('P5.js 卡通音游可视化初始化完成');
}

// P5.js draw函数
function draw() {
    // 清除画布，使其透明，让HTML背景显示
    clear();
    
    // 移动坐标系到中心
    push();
    translate(width/2, height/2);
    
    if (musicGame) {
        // 绘制背景装饰
        musicGame.drawBackground();
    }
    
    pop();
    
    // 在屏幕坐标系中绘制游戏元素
    if (musicGame) {
        // 更新游戏状态
        musicGame.updateFloatingEmotions();
        
        // 绘制飘动的情绪SVG（在屏幕坐标系中）
        musicGame.drawFloatingEmotions();
        
        // 绘制右侧音符块（在屏幕坐标系中）
        musicGame.drawNoteBlocks();
    }
}

// 窗口大小改变时调整画布
function windowResized() {
    // 全屏响应式调整
    resizeCanvas(windowWidth, windowHeight);
    
    // 重新创建音符块以适应新的屏幕尺寸
    if (musicGame) {
        musicGame.createNoteBlocks();
    }
}

// 页面卸载时清理资源
window.addEventListener('beforeunload', function() {
    if (musicGame) {
        musicGame.destroy();
    }
}); 