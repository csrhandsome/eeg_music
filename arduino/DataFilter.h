#ifndef DATAFILTER_H
#define DATAFILTER_H
#include "Arduino.h"

namespace DataFilter
{
    void init();
    float filterSuddenChange(float newDistance);  // 过滤突然变化的距离值，防止跳跃
    float smoothDistance(float distance);         // 平滑距离数据，减少噪声
} // namespace DataFilter

#endif
