/**
 * 背景增强脚本 - 创建更动态的三色渐变效果
 * 模拟图片中的自然颜色交融效果
 */

class BackgroundEnhancer {
    constructor() {
        this.body = document.body;
        this.colorPoints = [
            { x: 20, y: 30, color: 'rgba(255, 182, 193, 0.8)', size: 150 }, // 粉色
            { x: 80, y: 20, color: 'rgba(173, 216, 230, 0.8)', size: 140 }, // 蓝色
            { x: 50, y: 80, color: 'rgba(255, 250, 205, 0.8)', size: 160 }  // 黄色
        ];
        this.animationSpeed = 0.001; // 减慢动画速度
        this.time = 0;
        this.isAnimating = true;
        
        this.init();
    }

    init() {
        this.createDynamicBackground();
        this.startAnimation();
        this.addInteractivity();
    }

    createDynamicBackground() {
        // 创建动态背景容器
        const bgContainer = document.createElement('div');
        bgContainer.className = 'dynamic-bg-container';
        bgContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -2;
            pointer-events: none;
            will-change: transform;
        `;
        
        // 创建多个颜色层
        this.colorPoints.forEach((point, index) => {
            const colorLayer = document.createElement('div');
            colorLayer.className = `color-layer-${index}`;
            colorLayer.style.cssText = `
                position: absolute;
                width: ${point.size}%;
                height: ${point.size}%;
                background: radial-gradient(ellipse, ${point.color} 0%, transparent 70%);
                left: ${point.x}%;
                top: ${point.y}%;
                transform: translate(-50%, -50%);
                will-change: transform;
                filter: blur(0.5px);
            `;
            bgContainer.appendChild(colorLayer);
        });

        document.body.appendChild(bgContainer);
        this.bgContainer = bgContainer;
    }

    startAnimation() {
        let lastTime = 0;
        const targetFPS = 30; // 限制帧率以减少闪烁
        const frameInterval = 1000 / targetFPS;
        
        const animate = (currentTime) => {
            if (!this.isAnimating) return;
            
            if (currentTime - lastTime >= frameInterval) {
                this.time += this.animationSpeed;
                
                // 更新每个颜色点的位置和大小
                this.colorPoints.forEach((point, index) => {
                    const layer = this.bgContainer.querySelector(`.color-layer-${index}`);
                    if (layer) {
                        // 创建更平滑的浮动效果
                        const offsetX = Math.sin(this.time + index * 2) * 2; // 减小移动幅度
                        const offsetY = Math.cos(this.time * 0.8 + index * 1.5) * 1.5;
                        const scale = 1 + Math.sin(this.time * 0.3 + index) * 0.05; // 减小缩放幅度
                        
                        // 使用 transform 而不是改变 left/top 以提高性能
                        const translateX = point.x + offsetX;
                        const translateY = point.y + offsetY;
                        
                        layer.style.transform = `translate(calc(-50% + ${translateX - point.x}%), calc(-50% + ${translateY - point.y}%)) scale(${scale})`;
                    }
                });
                
                lastTime = currentTime;
            }
            
            requestAnimationFrame(animate);
        };
        
        requestAnimationFrame(animate);
    }

    // 移除会导致闪烁的滤镜效果
    updateMainBackground() {
        // 注释掉原来的滤镜效果，这是导致闪烁的主要原因
        // const hueShift = Math.sin(this.time * 0.3) * 10;
        // const saturation = 80 + Math.sin(this.time * 0.2) * 20;
        // this.body.style.filter = `hue-rotate(${hueShift}deg) saturate(${saturation}%)`;
    }

    addInteractivity() {
        // 添加鼠标交互效果，但减少频率
        let mouseX = 0;
        let mouseY = 0;
        let lastMouseUpdate = 0;
        
        document.addEventListener('mousemove', (e) => {
            const now = Date.now();
            if (now - lastMouseUpdate < 50) return; // 限制更新频率
            
            mouseX = (e.clientX / window.innerWidth) * 100;
            mouseY = (e.clientY / window.innerHeight) * 100;
            
            // 根据鼠标位置微调颜色点
            this.colorPoints.forEach((point, index) => {
                const layer = this.bgContainer.querySelector(`.color-layer-${index}`);
                if (layer) {
                    const distanceX = (mouseX - point.x) * 0.01; // 减小响应幅度
                    const distanceY = (mouseY - point.y) * 0.01;
                    
                    // 使用 CSS 变量来避免频繁的样式计算
                    layer.style.setProperty('--mouse-offset-x', `${distanceX}px`);
                    layer.style.setProperty('--mouse-offset-y', `${distanceY}px`);
                }
            });
            
            lastMouseUpdate = now;
        });

        // 添加窗口大小变化响应
        window.addEventListener('resize', () => {
            this.adjustForScreenSize();
        });
        
        // 添加页面可见性变化监听，当页面不可见时暂停动画
        document.addEventListener('visibilitychange', () => {
            this.isAnimating = !document.hidden;
            if (this.isAnimating) {
                this.startAnimation();
            }
        });
    }

    adjustForScreenSize() {
        // 根据屏幕尺寸调整效果
        const aspectRatio = window.innerWidth / window.innerHeight;
        
        this.colorPoints.forEach((point, index) => {
            const layer = this.bgContainer.querySelector(`.color-layer-${index}`);
            if (layer) {
                // 调整颜色层大小以适应屏幕比例
                const adjustedSize = point.size * (aspectRatio > 1 ? 1.1 : 0.9); // 减小调整幅度
                layer.style.width = `${adjustedSize}%`;
                layer.style.height = `${adjustedSize}%`;
            }
        });
    }

    // 提供颜色主题切换功能
    switchColorTheme(theme = 'default') {
        const themes = {
            default: [
                { color: 'rgba(255, 182, 193, 0.8)' }, // 粉色
                { color: 'rgba(173, 216, 230, 0.8)' }, // 蓝色
                { color: 'rgba(255, 250, 205, 0.8)' }  // 黄色
            ],
            sunset: [
                { color: 'rgba(255, 154, 162, 0.8)' }, // 珊瑚粉
                { color: 'rgba(255, 183, 77, 0.8)' },  // 橙色
                { color: 'rgba(255, 206, 84, 0.8)' }   // 金黄色
            ],
            ocean: [
                { color: 'rgba(130, 204, 221, 0.8)' }, // 海蓝
                { color: 'rgba(157, 224, 173, 0.8)' }, // 海绿
                { color: 'rgba(255, 255, 255, 0.6)' }  // 白色泡沫
            ]
        };

        const selectedTheme = themes[theme] || themes.default;
        
        selectedTheme.forEach((themeColor, index) => {
            if (this.colorPoints[index]) {
                this.colorPoints[index].color = themeColor.color;
                const layer = this.bgContainer.querySelector(`.color-layer-${index}`);
                if (layer) {
                    layer.style.background = `radial-gradient(ellipse, ${themeColor.color} 0%, transparent 70%)`;
                }
            }
        });
    }
    
    // 添加销毁方法
    destroy() {
        this.isAnimating = false;
        if (this.bgContainer) {
            this.bgContainer.remove();
        }
    }
}

// 当DOM加载完成后初始化背景增强器
document.addEventListener('DOMContentLoaded', () => {
    // 添加延迟以确保CSS动画已经稳定
    setTimeout(() => {
        window.backgroundEnhancer = new BackgroundEnhancer();
    }, 100);
});

// 导出类以供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BackgroundEnhancer;
} 