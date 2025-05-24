// WebSocket连接
let socket;
let statusDisplay;
let arduinoDataDisplay;

// p5.js相关变量
let stars = [];
let arduinoData = {
    distance: 0,
    scale: "",
    note: 0,
    frequency: 0,
    potentiometer: 0,
    rotary_potentiometer: "",
    button_state: 0,
    voltage: 0,  // 向后兼容字段
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
    potentiometer: [],
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

// 传统可视化系统类 - 使用 p5.js 实现3D可视化
class TraditionalVisualization {
    constructor() {
        this.socket = null;
        this.statusDisplay = null;
        this.arduinoDataDisplay = null;
        this.toggleVisualModeButton = null;
        
        // 可视化模式
        this.visualMode = 0; // 0: 圆形可视化, 1: 波形线, 2: 3D网格
        
        // Arduino数据
        this.arduinoData = {
            distance: 0,
            scale: "",
            note: 0,
            frequency: 0,
            potentiometer: 0,
            rotary_potentiometer: "",
            button_state: 0,
            voltage: 0,  // 向后兼容字段
            timestamp: 0
        };
        
        // 3D可视化元素
        this.stars = [];
        
        // 数据历史记录，用于创建波形效果
        this.dataHistory = {
            distance: [],
            frequency: [],
            voltage: [],
            potentiometer: [],
            maxHistoryLength: 100
        };
        
        // 用于动画效果
        this.animationPhase = 0;
        
        // 重连计时器
        this.reconnectTimer = null;
        this.RECONNECT_INTERVAL = 3000; // 重连间隔3秒
        
        // 用于显示数据更新的指示器
        this.lastDataUpdateTime = 0;
        this.dataUpdateIndicator = false;
        
        this.init();
    }
    
    init() {
        this.setupP5Canvas();
        this.setupDOM();
        this.setupWebSocket();
    }
    
    setupP5Canvas() {
        // 创建画布
        createCanvas(windowWidth, windowHeight, WEBGL);
        colorMode(HSB);
    }
    
    setupDOM() {
        // 获取DOM元素
        this.statusDisplay = document.getElementById('status');
        this.arduinoDataDisplay = document.getElementById('arduino-data');
        this.toggleVisualModeButton = document.getElementById('toggle-visual-mode');
        
        // 设置事件监听器
        if (this.toggleVisualModeButton) {
            this.toggleVisualModeButton.addEventListener('click', () => {
                this.visualMode = (this.visualMode + 1) % 3;
                this.toggleVisualModeButton.textContent = `切换可视化模式 (${['圆形可视化', '波形线', '3D网格'][this.visualMode]})`;
            });
            
            this.toggleVisualModeButton.textContent = `切换可视化模式 (${['圆形可视化', '波形线', '3D网格'][this.visualMode]})`;
        }
    }
    
    // p5.js的绘制函数，每帧调用
    draw() {
        background(0);
        orbitControl();
        
        // 更新动画相位
        this.animationPhase += 0.02;
        
        // 3D旋转和调整
        rotateX(PI/3);
        
        // 根据当前可视化模式绘制不同效果
        switch(this.visualMode) {
            case 0:
                this.drawCircularVisualization(); // 圆形可视化
                break;
            case 1:
                this.drawWaveformVisualization(); // 波形线
                break;
            case 2:
                this.draw3DGridVisualization(); // 3D网格
                break;
        }
        
        // 绘制星星效果
        this.updateStars();
        
        // 显示数据更新指示器
        this.drawDataUpdateIndicator();
    }
    
    // 绘制圆形可视化效果，完全基于Arduino数据
    drawCircularVisualization() {
        let r = width * 0.3;
        let segments = 50;
        
        for (let i = 0; i < segments; i++) {
            let a = map(i, 0, segments, 0, TWO_PI);
            
            // 使用距离和频率数据来计算高度
            let distanceFactor = map(this.arduinoData.distance, 0, 60, 0.5, 4);
            let frequencyFactor = map(this.arduinoData.frequency, 100, 1000, 0.5, 4);
            
            // 创建动态高度变化
            let dynamicHeight = 50 + 30 * sin(a * 3 + this.animationPhase);
            let finalHeight = dynamicHeight * distanceFactor * frequencyFactor;
            
            let x = r * cos(a);
            let y = r * sin(a);
            
            push();
            translate(x, y, finalHeight/2);
            rotateX(PI/2);
            
            // 颜色映射：根据Arduino的电位器值调整颜色
            let potentiometerRate = map(this.arduinoData.potentiometer, 0, 5, 0, 1);
            let c1 = color(150, 200, 200);
            let c2 = color(200, 100, 160);
            let col = lerpColor(c1, c2, potentiometerRate);
            
            stroke(col);
            fill(col);
            cylinder(10, 5 + finalHeight);
            pop();
        }
    }
    
    // 更新数据历史
    updateDataHistory() {
        // 添加当前数据到历史记录开头
        this.dataHistory.distance.unshift(this.arduinoData.distance);
        this.dataHistory.frequency.unshift(this.arduinoData.frequency);
        this.dataHistory.voltage.unshift(this.arduinoData.voltage);
        this.dataHistory.potentiometer.unshift(this.arduinoData.potentiometer);
        
        // 限制历史记录长度
        if (this.dataHistory.distance.length > this.dataHistory.maxHistoryLength) {
            this.dataHistory.distance.pop();
        }
        if (this.dataHistory.frequency.length > this.dataHistory.maxHistoryLength) {
            this.dataHistory.frequency.pop();
        }
        if (this.dataHistory.voltage.length > this.dataHistory.maxHistoryLength) {
            this.dataHistory.voltage.pop();
        }
        if (this.dataHistory.potentiometer.length > this.dataHistory.maxHistoryLength) {
            this.dataHistory.potentiometer.pop();
        }
    }
    
    // 绘制波形可视化效果，基于Arduino数据历史
    drawWaveformVisualization() {
        // 更新数据历史记录
        this.updateDataHistory();
        
        push();
        translate(-width/2, 0, 0);
        
        // 绘制距离波形
        beginShape();
        noFill();
        for (let i = 0; i < this.dataHistory.distance.length; i++) {
            let x = map(i, 0, this.dataHistory.distance.length, 0, width);
            let y = map(this.dataHistory.distance[i], 0, 100, 100, -100);
            
            // 颜色渐变
            let hue = map(i, 0, this.dataHistory.distance.length, 0, 120);
            stroke(hue, 100, 100);
            vertex(x, y, 0);
        }
        endShape();
        
        // 绘制频率波形
        beginShape();
        for (let i = 0; i < this.dataHistory.frequency.length; i++) {
            let x = map(i, 0, this.dataHistory.frequency.length, 0, width);
            let y = map(this.dataHistory.frequency[i], 0, 1000, 0, -200);
            
            // 颜色渐变
            let hue = map(i, 0, this.dataHistory.frequency.length, 120, 240);
            stroke(hue, 100, 100);
            vertex(x, y, 0);
        }
        endShape();
        
        // 绘制电位器波形
        beginShape();
        for (let i = 0; i < this.dataHistory.potentiometer.length; i++) {
            let x = map(i, 0, this.dataHistory.potentiometer.length, 0, width);
            let y = map(this.dataHistory.potentiometer[i], 0, 5, -200, -300);
            
            // 颜色渐变
            let hue = map(i, 0, this.dataHistory.potentiometer.length, 240, 360);
            stroke(hue, 100, 100);
            vertex(x, y, 0);
        }
        endShape();
        
        pop();
    }
    
    // 绘制3D网格可视化效果，基于Arduino数据
    draw3DGridVisualization() {
        let gridSize = 12;
        let cellSize = 30;
        
        push();
        translate(-gridSize * cellSize / 2, -gridSize * cellSize / 2, 0);
        
        for (let i = 0; i < gridSize; i++) {
            for (let j = 0; j < gridSize; j++) {
                // 创建动态高度基于距离、位置和动画相位
                let distanceFactor = map(this.arduinoData.distance, 0, 100, 0.5, 2);
                let frequencyComponent = 0;
                
                if (this.arduinoData.frequency > 0) {
                    frequencyComponent = map(this.arduinoData.frequency, 200, 800, 10, 50);
                }
                
                let animComponent = 20 * sin((i + j) * 0.3 + this.animationPhase);
                let h = (30 + frequencyComponent + animComponent) * distanceFactor;
                
                let x = i * cellSize;
                let y = j * cellSize;
                
                push();
                translate(x, y, h/2);
                
                // 颜色映射基于电位器值和位置
                let hue = map(i + j, 0, gridSize * 2, 0, 360);
                let sat = map(this.arduinoData.potentiometer, 0, 5, 50, 100);
                let bri = map(this.arduinoData.distance, 0, 50, 50, 100);
                
                fill(hue, sat, bri);
                box(cellSize * 0.8, cellSize * 0.8, h);
                pop();
            }
        }
        pop();
    }
    
    // 更新星星位置
    updateStars() {
        for (let i = 0; i < this.stars.length; i+=8) {
            if (this.stars[i]) {
                this.stars[i].move();
                this.stars[i].show();
                
                // 移除已经超出范围的星星
                if (this.stars[i].z > 500 || this.stars[i].life <= 0) {
                    this.stars.splice(i, 1);
                    i--;
                }
            }
        }
    }
    
    // 根据Arduino数据创建新的星星
    createStarsBasedOnData() {
        // 根据传感器变化创建星星，即使数据值很小也创建
        if (this.arduinoData.distance > 0 || this.arduinoData.potentiometer > 0) {
            // 根据频率决定创建星星的数量，如果没有频率数据，则使用默认值
            let baseNumStars = this.arduinoData.frequency > 0 ? 
                map(this.arduinoData.frequency, 200, 800, 1, 5) : 2;
            
            // 根据距离增加星星数量
            let distanceFactor = this.arduinoData.distance > 0 ? 
                map(this.arduinoData.distance, 0, 100, 1, 2) : 1;
                
            let numStars = baseNumStars * distanceFactor;
            numStars = constrain(numStars, 1, 10);
            
            for (let i = 0; i < numStars; i++) {
                let x = random(-width/2, width/2);
                let y = random(-height/2, height/2);
                let z = -300;
                
                // 颜色映射：根据Arduino的电位器值调整颜色，如果没有电位器数据使用随机色相
                let hueValue = this.arduinoData.potentiometer > 0 ? 
                    map(this.arduinoData.potentiometer, 0, 5, 0, 360) : 
                    random(0, 360);
                
                let starColor = color(hueValue, 100, 100);
                
                // 增加星星的生命值和速度变化
                let life = random(300, 700);
                let speedZ = random(2, 5) + (this.arduinoData.frequency / 1000);
                
                this.stars.push(new Star(x, y, z, starColor, life, speedZ));
            }
        }
    }
    
    // 设置WebSocket连接
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
            console.log('[open] WebSocket连接已建立');
            this.statusDisplay.textContent = '已连接!';
            this.statusDisplay.style.color = 'lime';
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
                    this.arduinoData.voltage = data.potentiometer; // 向后兼容
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
                if (data.voltage !== undefined) {
                    this.arduinoData.voltage = data.voltage;
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
                this.arduinoDataDisplay.textContent = formattedData;
                
                // 记录数据更新时间并切换指示器状态
                this.lastDataUpdateTime = millis();
                this.dataUpdateIndicator = !this.dataUpdateIndicator;
                
                // 根据数据创建新的星星
                this.createStarsBasedOnData();
                
            } catch (error) {
                console.error('解析JSON数据错误:', error);
            }
        };
        
        // 连接关闭时触发
        this.socket.onclose = (event) => {
            if (event.wasClean) {
                console.log(`[close] 连接已关闭, 代码=${event.code} 原因=${event.reason}`);
                this.statusDisplay.textContent = `断开连接: ${event.reason || '连接关闭'}`;
            } else {
                console.error('[close] 连接中断');
                this.statusDisplay.textContent = '连接中断，正在尝试重连...';
            }
            this.statusDisplay.style.color = 'red';
            
            // 设置自动重连
            this.reconnectTimer = setTimeout(() => {
                console.log("尝试重新连接...");
                this.setupWebSocket();
            }, this.RECONNECT_INTERVAL);
        };
        
        // 发生错误时触发
        this.socket.onerror = (error) => {
            console.error(`[error] ${error.message}`);
            this.statusDisplay.textContent = `WebSocket错误,正在尝试重连...`;
            this.statusDisplay.style.color = 'red';
        };
    }
    
    // 绘制数据更新指示器
    drawDataUpdateIndicator() {
        // 检查是否有最近的数据更新
        let currentTime = millis();
        let timeSinceLastUpdate = currentTime - this.lastDataUpdateTime;
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
    onWindowResized() {
        resizeCanvas(windowWidth, windowHeight);
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

// 全局变量
let traditionalVisualization = null;

// p5.js需要的全局函数
function preload() {
    // 不需要预加载音频文件，将使用实时生成的音频
}

function setup() {
    traditionalVisualization = new TraditionalVisualization();
}

function draw() {
    if (traditionalVisualization) {
        traditionalVisualization.draw();
    }
}

function windowResized() {
    if (traditionalVisualization) {
        traditionalVisualization.onWindowResized();
    }
}

// 导出到全局作用域
window.TraditionalVisualization = TraditionalVisualization;
window.traditionalVisualization = traditionalVisualization; 