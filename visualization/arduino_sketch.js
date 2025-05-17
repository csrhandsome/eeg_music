// WebSocket连接
let socket;
let statusDisplay;
let arduinoDataDisplay;

// p5.js相关变量
let stars = [];
let arduinoData = {
    distance: 0,
    frequency: 0,
    voltage: 0,
    timestamp: 0
};

// 移除音频相关变量
// let oscillator;
// let soundEnabled = true;
let visualMode = 0; // 0: 圆形可视化, 1: 波形线, 2: 3D网格

// 控制元素
// let toggleSoundButton;
let toggleVisualModeButton;
// let volumeSlider;

// 数据历史记录，用于创建波形效果
let dataHistory = {
    distance: [],
    frequency: [],
    voltage: [],
    maxHistoryLength: 100
};

// 用于动画效果
let animationPhase = 0;

// 重连计时器
let reconnectTimer = null;
const RECONNECT_INTERVAL = 3000; // 重连间隔3秒

// 用于显示数据更新的指示器
let lastDataUpdateTime = 0;
let dataUpdateIndicator = false;

// p5.js的预加载函数
function preload() {
    // 不需要预加载音频文件，将使用实时生成的音频
}

// p5.js的初始化函数
function setup() {
    // 创建画布
    createCanvas(windowWidth, windowHeight, WEBGL);
    colorMode(HSB);
    
    // 获取DOM元素
    statusDisplay = document.getElementById('status');
    arduinoDataDisplay = document.getElementById('arduino-data');
    // toggleSoundButton = document.getElementById('toggle-sound');
    toggleVisualModeButton = document.getElementById('toggle-visual-mode');
    // volumeSlider = document.getElementById('volume-slider');
    
    // 移除音频控制按钮事件
    /*
    toggleSoundButton.addEventListener('click', function() {
        soundEnabled = !soundEnabled;
        if (soundEnabled) {
            oscillator.start();
            this.textContent = "声音开/关 (开启)";
        } else {
            oscillator.stop();
            this.textContent = "声音开/关 (关闭)";
        }
    });
    */
    
    toggleVisualModeButton.addEventListener('click', function() {
        visualMode = (visualMode + 1) % 3;
        this.textContent = `切换可视化模式 (${['圆形可视化', '波形线', '3D网格'][visualMode]})`;
    });
    
    /*
    volumeSlider.addEventListener('input', function() {
        oscillator.amp(parseFloat(this.value));
    });
    */
    
    // 设置WebSocket连接
    setupWebSocket();
    
    // 移除音频相关设置
    /*
    // 设置音频分析和处理
    fft = new p5.FFT();
    
    // 创建一个振荡器用于生成声音
    oscillator = new p5.Oscillator('sine');
    oscillator.amp(0.5); // 设置音量
    oscillator.start();
    oscillator.freq(440); // 默认频率为A4（440Hz）
    
    // 设置按钮初始文本
    toggleSoundButton.textContent = "声音开/关 (开启)";
    */
    
    toggleVisualModeButton.textContent = `切换可视化模式 (${['圆形可视化', '波形线', '3D网格'][visualMode]})`;
}

// p5.js的绘制函数，每帧调用
function draw() {
    background(0);
    orbitControl();
    
    // 更新动画相位
    animationPhase += 0.02;
    
    // 3D旋转和调整
    rotateX(PI/3);
    
    // 根据当前可视化模式绘制不同效果
    switch(visualMode) {
        case 0:
            drawCircularVisualization(); // 圆形可视化
            break;
        case 1:
            drawWaveformVisualization(); // 波形线
            break;
        case 2:
            draw3DGridVisualization(); // 3D网格
            break;
    }
    
    // 绘制星星效果
    updateStars();
    
    // 显示数据更新指示器
    drawDataUpdateIndicator();
}

// 绘制圆形可视化效果，完全基于Arduino数据
function drawCircularVisualization() {
    let r = width * 0.3;
    let segments = 50;
    
    for (let i = 0; i < segments; i++) {
        let a = map(i, 0, segments, 0, TWO_PI);
        
        // 使用距离和频率数据来计算高度
        let distanceFactor = map(arduinoData.distance, 0, 100, 0.5, 2);
        let frequencyFactor = map(arduinoData.frequency, 200, 800, 0.5, 2);
        
        // 创建动态高度变化
        let dynamicHeight = 50 + 30 * sin(a * 3 + animationPhase);
        let finalHeight = dynamicHeight * distanceFactor * frequencyFactor;
        
        let x = r * cos(a);
        let y = r * sin(a);
        
        push();
        translate(x, y, finalHeight/2);
        rotateX(PI/2);
        
        // 颜色映射：根据Arduino的电压值调整颜色
        let voltageRate = map(arduinoData.voltage, 0, 5, 0, 1);
        let c1 = color(150, 200, 200);
        let c2 = color(200, 100, 160);
        let col = lerpColor(c1, c2, voltageRate);
        
        stroke(col);
        fill(col);
        cylinder(10, 5 + finalHeight);
        pop();
    }
}

// 更新数据历史
function updateDataHistory() {
    // 添加当前数据到历史记录开头
    dataHistory.distance.unshift(arduinoData.distance);
    dataHistory.frequency.unshift(arduinoData.frequency);
    dataHistory.voltage.unshift(arduinoData.voltage);
    
    // 限制历史记录长度
    if (dataHistory.distance.length > dataHistory.maxHistoryLength) {
        dataHistory.distance.pop();
    }
    if (dataHistory.frequency.length > dataHistory.maxHistoryLength) {
        dataHistory.frequency.pop();
    }
    if (dataHistory.voltage.length > dataHistory.maxHistoryLength) {
        dataHistory.voltage.pop();
    }
}

// 绘制波形可视化效果，基于Arduino数据历史
function drawWaveformVisualization() {
    // 更新数据历史记录
    updateDataHistory();
    
    push();
    translate(-width/2, 0, 0);
    
    // 绘制距离波形
    beginShape();
    noFill();
    for (let i = 0; i < dataHistory.distance.length; i++) {
        let x = map(i, 0, dataHistory.distance.length, 0, width);
        let y = map(dataHistory.distance[i], 0, 100, 100, -100);
        
        // 颜色渐变
        let hue = map(i, 0, dataHistory.distance.length, 0, 120);
        stroke(hue, 100, 100);
        vertex(x, y, 0);
    }
    endShape();
    
    // 绘制频率波形
    beginShape();
    for (let i = 0; i < dataHistory.frequency.length; i++) {
        let x = map(i, 0, dataHistory.frequency.length, 0, width);
        let y = map(dataHistory.frequency[i], 0, 1000, 0, -200);
        
        // 颜色渐变
        let hue = map(i, 0, dataHistory.frequency.length, 120, 240);
        stroke(hue, 100, 100);
        vertex(x, y, 0);
    }
    endShape();
    
    // 绘制电压波形
    beginShape();
    for (let i = 0; i < dataHistory.voltage.length; i++) {
        let x = map(i, 0, dataHistory.voltage.length, 0, width);
        let y = map(dataHistory.voltage[i], 0, 5, -200, -300);
        
        // 颜色渐变
        let hue = map(i, 0, dataHistory.voltage.length, 240, 360);
        stroke(hue, 100, 100);
        vertex(x, y, 0);
    }
    endShape();
    
    pop();
}

// 绘制3D网格可视化效果，基于Arduino数据
function draw3DGridVisualization() {
    let gridSize = 12;
    let cellSize = 30;
    
    push();
    translate(-gridSize * cellSize / 2, -gridSize * cellSize / 2, 0);
    
    for (let i = 0; i < gridSize; i++) {
        for (let j = 0; j < gridSize; j++) {
            // 创建动态高度基于距离、位置和动画相位
            let distanceFactor = map(arduinoData.distance, 0, 100, 0.5, 2);
            let frequencyComponent = 0;
            
            if (arduinoData.frequency > 0) {
                frequencyComponent = map(arduinoData.frequency, 200, 800, 10, 50);
            }
            
            let animComponent = 20 * sin((i + j) * 0.3 + animationPhase);
            let h = (30 + frequencyComponent + animComponent) * distanceFactor;
            
            let x = i * cellSize;
            let y = j * cellSize;
            
            push();
            translate(x, y, h/2);
            
            // 颜色映射基于电压和位置
            let hue = map(i + j, 0, gridSize * 2, 0, 360);
            let sat = map(arduinoData.voltage, 0, 5, 50, 100);
            let bri = map(arduinoData.distance, 0, 50, 50, 100);
            
            fill(hue, sat, bri);
            box(cellSize * 0.8, cellSize * 0.8, h);
            pop();
        }
    }
    pop();
}

// 更新星星位置
function updateStars() {
    for (let i = 0; i < stars.length; i+=8) {
        stars[i].move();
        stars[i].show();
        
        // 移除已经超出范围的星星
        if (stars[i].z > 500 || stars[i].life <= 0) {
            stars.splice(i, 1);
            i--;
        }
    }
}

// 根据Arduino数据创建新的星星
function createStarsBasedOnData() {
    // 根据传感器变化创建星星，即使数据值很小也创建
    if (arduinoData.distance > 0 || arduinoData.voltage > 0) {
        // 根据频率决定创建星星的数量，如果没有频率数据，则使用默认值
        let baseNumStars = arduinoData.frequency > 0 ? 
            map(arduinoData.frequency, 200, 800, 1, 5) : 2;
        
        // 根据距离增加星星数量
        let distanceFactor = arduinoData.distance > 0 ? 
            map(arduinoData.distance, 0, 100, 1, 2) : 1;
            
        let numStars = baseNumStars * distanceFactor;
        numStars = constrain(numStars, 1, 10);
        
        for (let i = 0; i < numStars; i++) {
            let x = random(-width/2, width/2);
            let y = random(-height/2, height/2);
            let z = -300;
            
            // 颜色映射：根据Arduino的电压值调整颜色，如果没有电压数据使用随机色相
            let hueValue = arduinoData.voltage > 0 ? 
                map(arduinoData.voltage, 0, 5, 0, 360) : 
                random(0, 360);
            
            let starColor = color(hueValue, 100, 100);
            
            // 增加星星的生命值和速度变化
            let life = random(300, 700);
            let speedZ = random(2, 5) + (arduinoData.frequency / 1000);
            
            stars.push(new Star(x, y, z, starColor, life, speedZ));
        }
    }
}

// 定义Star类
class Star {
    constructor(x, y, z, col, life = 500, speedZ = null) {
        this.x = x;
        this.y = y;
        this.z = z;
        this.col = col;
        this.life = life || 500;
        this.speedX = random(-0.3, 0.3);
        this.speedY = random(-0.3, 0.3);
        this.speedZ = speedZ || (0.05 + (z-5)/15);
    }
    
    move() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.z += this.speedZ;
        this.life -= 1;
    }
    
    show() {
        push();
        let a = map(this.life, 0, 500, 0, 1);
        stroke(hue(this.col), saturation(this.col), brightness(this.col), a * 255);
        strokeWeight(1.5);
        point(this.x, this.y, this.z);
        pop();
    }
}

// 设置WebSocket连接
function setupWebSocket() {
    const socketUrl = 'ws://localhost:8765';
    
    // 清除旧的重连计时器
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
    
    // 如果已有连接，先关闭
    if (socket) {
        socket.close();
    }
    
    socket = new WebSocket(socketUrl);
    
    // 连接建立时触发
    socket.onopen = function(event) {
        console.log('[open] WebSocket连接已建立');
        statusDisplay.textContent = '已连接!';
        statusDisplay.style.color = 'lime';
    };
    
    // 接收到服务器消息时触发
    socket.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            // 处理欢迎消息
            if (data.message && data.message === "Welcome to the WebSocket server!") {
                console.log("收到服务器欢迎消息");
                return;
            }
            
            // 更新Arduino数据
            if (data.distance !== undefined) {
                arduinoData.distance = data.distance;
            }
            if (data.frequency !== undefined) {
                arduinoData.frequency = data.frequency;
            }
            if (data.voltage !== undefined) {
                arduinoData.voltage = data.voltage;
            }
            if (data.timestamp !== undefined) {
                arduinoData.timestamp = data.timestamp;
            }
            
            // 更新数据显示
            let formattedData = `
距离: ${arduinoData.distance ? arduinoData.distance.toFixed(2) : 0}cm
频率: ${arduinoData.frequency ? arduinoData.frequency.toFixed(2) : 0}Hz 
电压: ${arduinoData.voltage ? arduinoData.voltage.toFixed(2) : 0}V
`;
            arduinoDataDisplay.textContent = formattedData;
            
            // 记录数据更新时间并切换指示器状态
            lastDataUpdateTime = millis();
            dataUpdateIndicator = !dataUpdateIndicator;
            
            // 根据数据创建新的星星
            createStarsBasedOnData();
            
        } catch (error) {
            console.error('解析JSON数据错误:', error);
        }
    };
    
    // 连接关闭时触发
    socket.onclose = function(event) {
        if (event.wasClean) {
            console.log(`[close] 连接已关闭, 代码=${event.code} 原因=${event.reason}`);
            statusDisplay.textContent = `断开连接: ${event.reason || '连接关闭'}`;
        } else {
            console.error('[close] 连接中断');
            statusDisplay.textContent = '连接中断，正在尝试重连...';
        }
        statusDisplay.style.color = 'red';
        
        // 设置自动重连
        reconnectTimer = setTimeout(function() {
            console.log("尝试重新连接...");
            setupWebSocket();
        }, RECONNECT_INTERVAL);
    };
    
    // 发生错误时触发
    socket.onerror = function(error) {
        console.error(`[error] ${error.message}`);
        statusDisplay.textContent = `WebSocket错误，正在尝试重连...`;
        statusDisplay.style.color = 'red';
    };
}

// 绘制数据更新指示器
function drawDataUpdateIndicator() {
    // 检查是否有最近的数据更新
    let currentTime = millis();
    let timeSinceLastUpdate = currentTime - lastDataUpdateTime;
    let isRecentUpdate = timeSinceLastUpdate < 1000; // 1秒内的更新视为最近
    
    // 绘制指示器
    push();
    translate(width/2 - 40, -height/2 + 40, 0);
    noStroke();
    
    if (isRecentUpdate) {
        // 如果有最近更新，显示闪烁的绿色指示器
        fill(0, 255, 0, 150 + 100 * sin(currentTime * 0.01));
    } else {
        // 如果长时间没有更新，显示红色指示器
        fill(255, 0, 0, 150);
    }
    
    sphere(10);
    pop();
}

// 窗口大小改变时，调整画布大小
function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
} 