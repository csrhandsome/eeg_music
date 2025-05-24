// 音符SVG图标数据 - 可以用作下落物
const MusicNotesSVG = {
    // 基础音符
    note1: `<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="28" r="6" fill="currentColor"/>
        <rect x="18" y="8" width="2" height="20" fill="currentColor"/>
        <path d="M18 8 Q25 5 32 8 Q25 11 18 14" fill="currentColor"/>
    </svg>`,
    
    // 双音符
    note2: `<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
        <circle cx="8" cy="28" r="5" fill="currentColor"/>
        <circle cx="24" cy="24" r="5" fill="currentColor"/>
        <rect x="13" y="8" width="2" height="20" fill="currentColor"/>
        <rect x="29" y="8" width="2" height="16" fill="currentColor"/>
        <path d="M13 8 Q20 5 31 8 L31 12 Q20 9 13 12" fill="currentColor"/>
    </svg>`,
    
    // 三连音
    note3: `<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
        <circle cx="6" cy="30" r="4" fill="currentColor"/>
        <circle cx="18" cy="26" r="4" fill="currentColor"/>
        <circle cx="30" cy="22" r="4" fill="currentColor"/>
        <rect x="10" y="10" width="1.5" height="20" fill="currentColor"/>
        <rect x="22" y="8" width="1.5" height="18" fill="currentColor"/>
        <rect x="34" y="6" width="1.5" height="16" fill="currentColor"/>
        <path d="M10 10 Q18 7 34 6 L34 10 Q18 11 10 14" fill="currentColor"/>
    </svg>`,
    
    // 高音谱号
    treble: `<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 5 Q15 5 15 12 Q15 18 20 20 Q25 18 25 12 Q25 5 20 5 
                 M20 20 Q15 22 15 28 Q15 35 20 35 Q25 35 25 28 Q25 22 20 20
                 M20 20 L22 8 Q28 8 28 15 Q28 25 20 30" 
              fill="currentColor" stroke="currentColor" stroke-width="1"/>
    </svg>`
};

// 将SVG转换为图片URL的函数
function svgToDataUrl(svgString, color = '#ffffff') {
    const coloredSvg = svgString.replace(/currentColor/g, color);
    const encoded = encodeURIComponent(coloredSvg);
    return `data:image/svg+xml,${encoded}`;
}

// 导出
window.MusicNotesSVG = MusicNotesSVG;
window.svgToDataUrl = svgToDataUrl; 