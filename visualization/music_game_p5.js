// 音游可视化系统 - P5.js卡通2D版本
class MusicGameVisualizationP5 {
    constructor() {
        this.socket = null;
        this.tracks = [];
        this.dropObjects = [];
        this.hitEffects = [];
        this.backgroundStars = [];
        this.clouds = [];
        
        // 游戏参数
        this.trackCount = 4;
        this.trackWidth = 120;
        this.trackHeight = 600;
        this.trackSpacing = 30;
        this.dropDuration = 3000; // 下落动画持续时间(ms)
        this.dropObjectSize = 50;
        this.gameStartY = -250;
        
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
        
        // 卡通风格轨道颜色 - 更明亮更饱和
        this.trackColors = [
            [255, 99, 132],   // 粉红色 
            [75, 192, 192],   // 青绿色
            [54, 162, 235],   // 蓝色
            [255, 206, 86]    // 黄色
        ];
        
        // 卡通下落物形状和颜色
        this.dropShapes = [
            { type: 'star', color: [255, 223, 0] },      // 金色星星
            { type: 'heart', color: [255, 105, 180] },   // 粉色爱心
            { type: 'diamond', color: [138, 43, 226] },  // 紫色钻石
            { type: 'flower', color: [50, 205, 50] }     // 绿色花朵
        ];
        
        // 背景装饰
        this.rainbowColors = [
            [255, 99, 132], [255, 159, 64], [255, 206, 86], 
            [75, 192, 192], [54, 162, 235], [153, 102, 255]
        ];
        
        this.init();
    }
    
    init() {
        this.setupWebSocket();
        this.createTracks();
        this.createBackgroundElements();
    }
    
    createTracks() {
        this.tracks = [];
        
        // 根据屏幕大小调整轨道参数
        const isMobile = window.innerWidth <= 768;
        const isLandscape = window.innerWidth > window.innerHeight;
        
        if (isMobile) {
            this.trackWidth = isLandscape ? 80 : 90;
            this.trackHeight = isLandscape ? 400 : 500;
            this.trackSpacing = isLandscape ? 15 : 20;
            this.gameStartY = isLandscape ? -180 : -220;
        } else {
            this.trackWidth = 120;
            this.trackHeight = 600;
            this.trackSpacing = 30;
            this.gameStartY = -250;
        }
        
        for (let i = 0; i < this.trackCount; i++) {
            // 居中计算轨道位置
            const totalWidth = this.trackCount * this.trackWidth + (this.trackCount - 1) * this.trackSpacing;
            const startX = -totalWidth / 2 + this.trackWidth / 2;
            const x = startX + i * (this.trackWidth + this.trackSpacing);
            
            this.tracks.push({
                x: x,
                y: this.gameStartY,
                width: this.trackWidth,
                height: this.trackHeight,
                color: this.trackColors[i],
                shape: this.dropShapes[i],
                bounce: 0, // 用于弹跳动画
                glow: 0    // 用于发光效果
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
        
        // 创建云朵
        this.clouds = [];
        for (let i = 0; i < 5; i++) {
            this.clouds.push({
                x: random(-500, 500),
                y: random(-200, -100),
                size: random(40, 80),
                speed: random(0.3, 0.8),
                opacity: random(100, 200)
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
        if (noteIndex < 4) return 0;      // 低音区 -> 轨道1
        else if (noteIndex < 8) return 1; // 中低音区 -> 轨道2  
        else if (noteIndex < 12) return 2; // 中高音区 -> 轨道3
        else return 3;                     // 高音区 -> 轨道4
    }
    
    // 创建下落物
    createDropObject(trackIndex, frequency) {
        if (trackIndex < 0 || trackIndex >= this.tracks.length) return;
        
        const track = this.tracks[trackIndex];
        
        // 根据频率调整下落物大小
        const sizeScale = map(constrain(frequency, 200, 1800), 200, 1800, 0.7, 1.2);
        const size = this.dropObjectSize * sizeScale;
        
        const dropObject = {
            trackIndex: trackIndex,
            x: track.x,
            y: track.y - 20,
            size: size,
            frequency: frequency,
            startTime: millis(),
            targetY: track.y + track.height - 50,
            rotation: 0,
            bounce: 0,
            trail: [], // 拖尾效果
            active: true,
            shape: track.shape
        };
        
        this.dropObjects.push(dropObject);
        
        // 轨道发光效果
        track.glow = 255;
    }
    
    // 创建击中效果
    createHitEffect(trackIndex) {
        if (trackIndex < 0 || trackIndex >= this.tracks.length) return;
        
        const track = this.tracks[trackIndex];
        
        // 创建卡通爆炸粒子效果
        const particles = [];
        for (let i = 0; i < 15; i++) {
            const angle = (i / 15) * TWO_PI;
            const speed = random(3, 8);
            particles.push({
                x: track.x,
                y: track.y + track.height - 50,
                vx: cos(angle) * speed,
                vy: sin(angle) * speed - random(1, 3), // 向上飞溅
                life: 1.0,
                size: random(4, 12),
                color: [...this.rainbowColors[i % this.rainbowColors.length]],
                rotation: random(0, TWO_PI),
                rotationSpeed: random(-0.2, 0.2)
            });
        }
        
        // 添加爱心粒子
        for (let i = 0; i < 5; i++) {
            const angle = random(0, TWO_PI);
            const speed = random(2, 5);
            particles.push({
                x: track.x,
                y: track.y + track.height - 50,
                vx: cos(angle) * speed,
                vy: sin(angle) * speed - random(2, 4),
                life: 1.0,
                size: random(8, 16),
                color: [255, 105, 180],
                type: 'heart',
                rotation: 0,
                rotationSpeed: random(-0.1, 0.1)
            });
        }
        
        const effect = {
            particles: particles,
            startTime: millis(),
            duration: 800,
            trackIndex: trackIndex,
            active: true
        };
        
        this.hitEffects.push(effect);
        
        // 轨道弹跳效果
        track.bounce = 20;
    }
    
    // 绘制轨道 - 卡通2D风格
    drawTracks() {
        for (let i = 0; i < this.tracks.length; i++) {
            const track = this.tracks[i];
            
            // 更新动画效果
            if (track.bounce > 0) {
                track.bounce *= 0.9; // 弹跳衰减
            }
            if (track.glow > 0) {
                track.glow *= 0.95; // 发光衰减
            }
            
            push();
            translate(track.x, track.y + track.bounce);
            
            // 3D纵深透视变换 - 根据屏幕大小调整
            const isMobile = window.innerWidth <= 768;
            const perspectiveAngle = isMobile ? -20 : -15; // 移动端更大的倾斜角度
            const scaleTop = isMobile ? 0.6 : 0.7; // 移动端更强的透视效果
            const scaleBottom = 1.0; // 底部缩放比例
            
            // 绘制3D轨道阴影 - 增强纵深感
            fill(0, 0, 0, 80);
            noStroke();
            this.drawPerspectiveRect(-track.width/2 + 5, 5, track.width, track.height, 
                                     scaleTop, scaleBottom, perspectiveAngle, 15);
            
            // 绘制主轨道 - 3D透视矩形
            fill(track.color[0], track.color[1], track.color[2], 140);
            stroke(255);
            strokeWeight(3);
            this.drawPerspectiveRect(-track.width/2, 0, track.width, track.height, 
                                     scaleTop, scaleBottom, perspectiveAngle, 15);
            
            // 绘制发光效果
            if (track.glow > 0) {
                drawingContext.shadowColor = `rgba(${track.color[0]}, ${track.color[1]}, ${track.color[2]}, ${track.glow/255})`;
                drawingContext.shadowBlur = 25;
                stroke(track.color[0], track.color[1], track.color[2], track.glow);
                strokeWeight(6);
                noFill();
                this.drawPerspectiveRect(-track.width/2, 0, track.width, track.height, 
                                         scaleTop, scaleBottom, perspectiveAngle, 15);
                drawingContext.shadowBlur = 0;
            }
            
            // 绘制3D轨道内部装饰条纹 - 透视线条
            stroke(255, 255, 255, 120);
            strokeWeight(2);
            for (let j = 1; j < 4; j++) {
                const stripeY = (track.height / 4) * j;
                const progress = j / 4;
                const currentScale = lerp(scaleTop, scaleBottom, progress);
                const currentWidth = track.width * currentScale;
                const offsetY = sin(radians(perspectiveAngle)) * stripeY * 0.3;
                
                line(-currentWidth/2 + 10, stripeY + offsetY, 
                     currentWidth/2 - 10, stripeY + offsetY);
            }
            
            // 绘制轨道标签 - 可爱字体
            fill(255);
            stroke(track.color[0], track.color[1], track.color[2]);
            strokeWeight(2);
            textAlign(CENTER, CENTER);
            textSize(16);
            textStyle(BOLD);
            text(`♪${i + 1}`, 0, -30);
            
            // 绘制底部目标区域 - 3D彩虹效果
            const targetY = track.height - 70;
            const targetHeight = 50;
            
            // 3D彩虹渐变效果
            for (let k = 0; k < 6; k++) {
                const rainbowColor = this.rainbowColors[k];
                fill(rainbowColor[0], rainbowColor[1], rainbowColor[2], 170);
                noStroke();
                const segmentHeight = targetHeight / 6;
                const segmentY = targetY + k * segmentHeight;
                const progress = (segmentY - targetY) / targetHeight;
                const currentScale = lerp(scaleTop, scaleBottom, (targetY + progress * targetHeight) / track.height);
                const currentWidth = (track.width - 10) * currentScale;
                const offsetY = sin(radians(perspectiveAngle)) * segmentY * 0.3;
                
                this.drawPerspectiveSegment(-currentWidth/2, segmentY + offsetY, 
                                           currentWidth, segmentHeight, progress, 5);
            }
            
            // 3D目标区域边框
            noFill();
            stroke(255);
            strokeWeight(4);
            const targetProgress = targetY / track.height;
            const targetScale = lerp(scaleTop, scaleBottom, targetProgress);
            const targetWidth = (track.width - 10) * targetScale;
            const targetOffsetY = sin(radians(perspectiveAngle)) * targetY * 0.3;
            
            this.drawPerspectiveRect(-targetWidth/2, targetY + targetOffsetY, 
                                     targetWidth, targetHeight, 
                                     scaleTop, scaleBottom, perspectiveAngle, 10);
            
            // 目标区域文字 - 3D效果
            fill(255);
            stroke(0);
            strokeWeight(2);
            textAlign(CENTER, CENTER);
            textSize(14);
            textStyle(BOLD);
            text("TARGET", 0, targetY + targetHeight/2 + targetOffsetY);
            
            pop();
        }
    }
    
    // 绘制透视矩形的辅助方法
    drawPerspectiveRect(x, y, w, h, scaleTop, scaleBottom, angle, cornerRadius) {
        const topWidth = w * scaleTop;
        const bottomWidth = w * scaleBottom;
        const angleOffset = sin(radians(angle)) * h * 0.3;
        
        beginShape();
        // 顶部边
        vertex(x + (w - topWidth) / 2, y);
        vertex(x + (w + topWidth) / 2, y);
        // 右边
        vertex(x + (w + bottomWidth) / 2, y + h + angleOffset);
        // 底部边  
        vertex(x + (w - bottomWidth) / 2, y + h + angleOffset);
        endShape(CLOSE);
    }
    
    // 绘制透视段落的辅助方法
    drawPerspectiveSegment(x, y, w, h, progress, cornerRadius) {
        push();
        fill(red(color(...this.rainbowColors[Math.floor(progress * 6)])), 
             green(color(...this.rainbowColors[Math.floor(progress * 6)])), 
             blue(color(...this.rainbowColors[Math.floor(progress * 6)])), 170);
        noStroke();
        rect(x, y, w, h, cornerRadius);
        pop();
    }
    
    // 更新下落物
    updateDropObjects() {
        for (let i = this.dropObjects.length - 1; i >= 0; i--) {
            const drop = this.dropObjects[i];
            if (!drop.active) continue;
            
            const elapsed = millis() - drop.startTime;
            const progress = elapsed / this.dropDuration;
            
            if (progress >= 1.0) {
                // 到达底部
                this.createHitEffect(drop.trackIndex);
                this.dropObjects.splice(i, 1);
                continue;
            }
            
            // 更新位置（使用弹性缓动）
            const easeProgress = 1 - pow(1 - progress, 3); // easeOutCubic
            drop.y = lerp(drop.y, drop.targetY, easeProgress * 0.05 + 0.02);
            
            // 添加轻微的左右摆动
            drop.x = this.tracks[drop.trackIndex].x + sin(millis() * 0.01 + drop.startTime * 0.001) * 5;
            
            // 更新旋转和弹跳
            drop.rotation += 0.1;
            drop.bounce = sin(millis() * 0.02) * 3;
            
            // 更新拖尾
            drop.trail.push({x: drop.x, y: drop.y, life: 1.0});
            if (drop.trail.length > 8) {
                drop.trail.shift();
            }
            
            // 更新拖尾生命周期
            for (let t of drop.trail) {
                t.life *= 0.85;
            }
        }
    }
    
    // 绘制下落物 - 卡通形状
    drawDropObjects() {
        for (const drop of this.dropObjects) {
            if (!drop.active) continue;
            
            // 绘制拖尾
            for (let i = 0; i < drop.trail.length; i++) {
                const t = drop.trail[i];
                push();
                fill(drop.shape.color[0], drop.shape.color[1], drop.shape.color[2], t.life * 100);
                noStroke();
                const trailSize = (drop.size * 0.3) * t.life;
                ellipse(t.x, t.y, trailSize);
                pop();
            }
            
            push();
            translate(drop.x, drop.y + drop.bounce);
            rotate(drop.rotation);
            
            // 绘制形状阴影
            fill(0, 0, 0, 100);
            noStroke();
            this.drawShape(drop.shape.type, 2, 2, drop.size);
            
            // 绘制主形状
            fill(drop.shape.color[0], drop.shape.color[1], drop.shape.color[2]);
            stroke(255);
            strokeWeight(3);
            this.drawShape(drop.shape.type, 0, 0, drop.size);
            
            // 添加高光效果
            fill(255, 255, 255, 150);
            noStroke();
            this.drawShape(drop.shape.type, -drop.size * 0.15, -drop.size * 0.15, drop.size * 0.3);
            
            pop();
        }
    }
    
    // 绘制卡通形状
    drawShape(type, x, y, size) {
        push();
        translate(x, y);
        
        switch(type) {
            case 'star':
                this.drawStar(0, 0, size * 0.4, size * 0.2, 5);
                break;
            case 'heart':
                this.drawHeart(0, 0, size * 0.8);
                break;
            case 'diamond':
                this.drawDiamond(0, 0, size * 0.8);
                break;
            case 'flower':
                this.drawFlower(0, 0, size * 0.7);
                break;
            default:
                ellipse(0, 0, size);
        }
        
        pop();
    }
    
    // 绘制星星
    drawStar(x, y, radius1, radius2, npoints) {
        let angle = TWO_PI / npoints;
        let halfAngle = angle / 2.0;
        beginShape();
        for (let a = 0; a < TWO_PI; a += angle) {
            let sx = x + cos(a) * radius1;
            let sy = y + sin(a) * radius1;
            vertex(sx, sy);
            sx = x + cos(a + halfAngle) * radius2;
            sy = y + sin(a + halfAngle) * radius2;
            vertex(sx, sy);
        }
        endShape(CLOSE);
    }
    
    // 绘制爱心
    drawHeart(x, y, size) {
        beginShape();
        vertex(x, y);
        bezierVertex(x - size/2, y - size/2, x - size, y + size/3, x, y + size);
        bezierVertex(x + size, y + size/3, x + size/2, y - size/2, x, y);
        endShape(CLOSE);
    }
    
    // 绘制钻石
    drawDiamond(x, y, size) {
        beginShape();
        vertex(x, y - size/2);
        vertex(x + size/3, y);
        vertex(x, y + size/2);
        vertex(x - size/3, y);
        endShape(CLOSE);
    }
    
    // 绘制花朵
    drawFlower(x, y, size) {
        push();
        translate(x, y);
        
        // 花瓣
        for (let i = 0; i < 6; i++) {
            push();
            rotate(i * PI / 3);
            ellipse(0, -size/3, size/3, size/2);
            pop();
        }
        
        // 花心
        fill(255, 223, 0);
        ellipse(0, 0, size/3);
        
        pop();
    }
    
    // 更新击中效果
    updateHitEffects() {
        for (let i = this.hitEffects.length - 1; i >= 0; i--) {
            const effect = this.hitEffects[i];
            if (!effect.active) continue;
            
            const elapsed = millis() - effect.startTime;
            const progress = elapsed / effect.duration;
            
            if (progress >= 1.0) {
                this.hitEffects.splice(i, 1);
                continue;
            }
            
            // 更新粒子
            for (const particle of effect.particles) {
                particle.x += particle.vx;
                particle.y += particle.vy;
                particle.vx *= 0.98; // 空气阻力
                particle.vy += 0.2;  // 重力
                particle.life = 1.0 - progress;
                particle.rotation += particle.rotationSpeed;
                particle.size *= 0.995; // 粒子收缩
            }
        }
    }
    
    // 绘制击中效果 - 卡通风格
    drawHitEffects() {
        for (const effect of this.hitEffects) {
            if (!effect.active) continue;
            
            const track = this.tracks[effect.trackIndex];
            
            // 绘制粒子
            for (const particle of effect.particles) {
                push();
                translate(particle.x, particle.y);
                rotate(particle.rotation);
                
                fill(particle.color[0], particle.color[1], particle.color[2], particle.life * 255);
                stroke(255, 255, 255, particle.life * 150);
                strokeWeight(1);
                
                if (particle.type === 'heart') {
                    this.drawHeart(0, 0, particle.size);
                } else {
                    // 星星粒子
                    this.drawStar(0, 0, particle.size * 0.4, particle.size * 0.2, 5);
                }
                
                pop();
            }
            
            // 中心闪光效果 - 更卡通化
            const elapsed = millis() - effect.startTime;
            if (elapsed < 300) {
                const flashProgress = elapsed / 300;
                push();
                translate(track.x, track.y + track.height - 50);
                
                // 彩虹圆环效果
                for (let i = 0; i < 6; i++) {
                    const ringColor = this.rainbowColors[i];
                    fill(ringColor[0], ringColor[1], ringColor[2], (1 - flashProgress) * 200);
                    noStroke();
                    
                    const ringSize = lerp(10, 60, flashProgress) + i * 5;
                    ellipse(0, 0, ringSize);
                }
                
                // 中心白光
                fill(255, 255, 255, (1 - flashProgress) * 255);
                ellipse(0, 0, lerp(5, 25, flashProgress));
                
                pop();
            }
        }
    }
    
    // 绘制背景装饰
    drawBackground() {
        // 更新云朵位置
        for (let cloud of this.clouds) {
            cloud.x += cloud.speed;
            if (cloud.x > width/2 + 100) {
                cloud.x = -width/2 - 100;
            }
        }
        
        // 绘制云朵
        for (let cloud of this.clouds) {
            push();
            translate(cloud.x, cloud.y);
            fill(255, 255, 255, cloud.opacity);
            noStroke();
            
            // 简单的云朵形状
            ellipse(0, 0, cloud.size);
            ellipse(-cloud.size * 0.3, 0, cloud.size * 0.7);
            ellipse(cloud.size * 0.3, 0, cloud.size * 0.7);
            ellipse(0, -cloud.size * 0.3, cloud.size * 0.8);
            
            pop();
        }
        
        // 绘制背景星星
        for (let star of this.backgroundStars) {
            star.twinkle += star.speed;
            
            push();
            translate(star.x, star.y);
            
            const brightness = (sin(star.twinkle) + 1) * 0.5;
            fill(255, 255, 200, brightness * 200);
            noStroke();
            
            this.drawStar(0, 0, star.size, star.size * 0.4, 5);
            
            pop();
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
    
    // WebSocket设置
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
                
                // 更新数据显示
                const dataElement = document.getElementById('arduino-data');
                if (dataElement) {
                    let formattedData = `
距离: ${this.arduinoData.distance ? this.arduinoData.distance.toFixed(2) : 0}cm
音阶: ${this.arduinoData.scale || 'N/A'}
音符: ${this.arduinoData.note || 0}
频率: ${this.arduinoData.frequency ? this.arduinoData.frequency.toFixed(2) : 0}Hz 
电位器: ${this.arduinoData.potentiometer ? this.arduinoData.potentiometer.toFixed(2) : 0}V
旋转电位器: ${this.arduinoData.rotary_potentiometer || 'N/A'}V
按钮状态: ${this.arduinoData.button_state === 1 ? '录制中' : '未录制'}
`;
                    dataElement.textContent = formattedData;
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
        this.dropObjects = [];
        this.hitEffects = [];
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

// P5.js setup函数
function setup() {
    // 创建全屏2D画布
    let canvas = createCanvas(windowWidth, windowHeight);
    canvas.parent('p5-canvas-container');
    
    // 初始化音游系统
    musicGame = new MusicGameVisualizationP5();
    
    // 设置全局变量以便HTML访问
    window.musicGame = musicGame;
    
    console.log('P5.js 卡通音游可视化初始化完成');
}

// P5.js draw函数
function draw() {
    // 卡通风格背景渐变
    for (let i = 0; i <= height; i++) {
        const inter = map(i, 0, height, 0, 1);
        const c = lerpColor(color(135, 206, 250), color(255, 182, 193), inter); // 天蓝到粉红渐变
        stroke(c);
        line(0, i, width, i);
    }
    
    // 移动坐标系到中心
    push();
    translate(width/2, height/2);
    
    if (musicGame) {
        // 绘制背景装饰
        musicGame.drawBackground();
        
        // 更新游戏状态
        musicGame.updateDropObjects();
        musicGame.updateHitEffects();
        
        // 绘制游戏元素
        musicGame.drawTracks();
        musicGame.drawDropObjects();
        musicGame.drawHitEffects();
    }
    
    pop();
}

// 窗口大小改变时调整画布
function windowResized() {
    // 全屏响应式调整
    resizeCanvas(windowWidth, windowHeight);
    
    // 重新创建轨道以适应新的屏幕尺寸
    if (musicGame) {
        musicGame.createTracks();
    }
}

// 页面卸载时清理资源
window.addEventListener('beforeunload', function() {
    if (musicGame) {
        musicGame.destroy();
    }
}); 