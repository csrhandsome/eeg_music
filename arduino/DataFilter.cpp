#include "DataFilter.h"

namespace DataFilter
{
    // 静态变量用于存储状态
    static float lastDistance = 0;
    static bool initialized = false;
    static float distanceHistory[5];  // 存储最近5个距离值用于平滑
    static int historyIndex = 0;
    static bool historyFull = false;
    static const float MAX_CHANGE_THRESHOLD = 15.0;  // 最大允许变化阈值(cm)
    static int change = 0;
    void init() {
        lastDistance = 0;
        initialized = false;
        historyIndex = 0;
        historyFull = false;
        for(int i = 0; i < 5; i++) {
            distanceHistory[i] = 0;
        }
    }

    // 过滤突然变化的距离值
    float filterSuddenChange(float newDistance) {
        // 第一次调用时直接返回
        if (!initialized) {
            lastDistance = newDistance;
            initialized = true;
            return newDistance;
        }
        
        // 如果距离变化太大（可能是检测错误），保持上一次的值
        if (abs(newDistance - lastDistance) > MAX_CHANGE_THRESHOLD && change<3) {
            change++;
            return lastDistance;  // 不采用突然变化的值
        }
        
        // 更新上一次距离并返回新值
        change=0;
        lastDistance = newDistance;
        return newDistance;
    }

    // 平滑距离数据，使用移动平均滤波
    float smoothDistance(float distance) {
        // 添加新的距离值到心音轨迹
        distanceHistory[historyIndex] = distance;
        historyIndex = (historyIndex + 1) % 5;
        if (historyIndex == 0) historyFull = true;
        
        // 计算移动平均值
        float sum = 0;
        int count = historyFull ? 5 : historyIndex;
        for(int i = 0; i < count; i++) {
            sum += distanceHistory[i];
        }
        
        return sum / count;
    }

} // namespace DataFilter
