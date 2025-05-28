#include "Adafruit_NeoPixel.h"     // 包含用于控制 NeoPixels（WS2812B 灯珠）的库文件

// 定义引脚
#define TRIG_PIN A0  // 超声波 trig 引脚
#define ECHO_PIN A1  // 超声波 echo 引脚
#define POT1_PIN A2  // 滑动电位器引脚
#define POT2_PIN A3  // 旋转电位器引脚
#define BUTTON_PIN 4 // 按钮引脚
#define LED_PIN 6    // RGB 灯引脚
#define MAX_LED 12   // 定义 RGB 灯的数量为 12 个

// 创建 NeoPixel 对象
Adafruit_NeoPixel strip = Adafruit_NeoPixel(MAX_LED, LED_PIN, NEO_RGB + NEO_KHZ800);

// 音符数量
#define NUM_NOTES 10  // 一个调中有10个音

// C大调音阶中音符的频率（C4到C6）
float base_frequencies[NUM_NOTES] = {
  261.63,  // C4
  293.66,  // D4
  329.63,  // E4
  349.23,  // F4
  392.00,  // G4
  440.00,  // A4
  493.88,  // B4
  523.25,  // C5
  587.33,  // D5
  659.25,  // E5
};

// G大调音阶中各音符的频率（从G4到G6）
float g_major_frequencies[NUM_NOTES] = {
  392.00,  // G4
  440.00,  // A4
  493.88,  // B4
  523.25,  // C5
  587.33,  // D5
  659.25,  // E5
  739.99,  // F♯5
  783.99,  // G5
  880.00,  // A5
  987.77,  // B5
};  

// D大调音阶中各音符的频率（从D4到D6）
float d_major_frequencies[NUM_NOTES] = {
  293.66,  // D4
  329.63,  // E4
  369.99,  // F♯4
  392.00,  // G4
  440.00,  // A4
  493.88,  // B4
  554.37,  // C♯5
  587.33,  // D5
  659.25,  // E5
  739.99,  // F♯5
};

// e自然小调音阶中各音符的频率（从E4到E6）
float e_minor_frequencies[NUM_NOTES] = {
  329.63,  // E4
  369.99,  // F♯4
  392.00,  // G4
  440.00,  // A4
  493.88,  // B4
  523.25,  // C5
  587.33,  // D5
  659.25,  // E5
  739.99,  // F♯5
  783.99,  // G5
};

// a自然小调音阶中各音符的频率（从A4到A6）
float a_minor_frequencies[NUM_NOTES] = {
  440.00,  // A4
  493.88,  // B4
  523.25,  // C5
  587.33,  // D5
  659.25,  // E5
  698.46,  // F5
  783.99,  // G5
  880.00,  // A5
  987.77,  // B5
  1046.50, // C6
};

// 超声波测距函数
float checkdistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  float distance = pulseIn(ECHO_PIN, HIGH) / 58.00;
  delay(10);
  return distance;
}

// 呼吸灯相关变量
uint8_t brightness = 0;            // 当前亮度值
int fadeAmount = 4;                // 亮度变化步长（由电位器控制）
unsigned long lastUpdateTime = 0;  // 上次更新时间
const unsigned long updateInterval = 5;  // 更新间隔（5ms）

// 状态变量
int toggleState = 0;       // 切换状态，初始为0
int lastButtonState = HIGH; // 上一次按钮状态，初始为高电平（未按下）

// 将频率映射到颜色的函数
void mapFrequencyToColor(float frequency) {
  float minFreq = 261.63;  // C4
  float maxFreq = 1760.00; // A6
  float ratio = (frequency - minFreq) / (maxFreq - minFreq);
  ratio = constrain(ratio, 0.0, 1.0);
  uint8_t red = ratio * 255;
  uint8_t green = (1.0 - ratio) * 255;
  uint8_t blue = 128 + (sin(ratio * 2 * PI) * 127);
  for(uint8_t i = 0; i < MAX_LED; i++) {
    strip.setPixelColor(i, red, green, blue);
  }
  strip.show();
}

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(POT1_PIN, INPUT);
  pinMode(POT2_PIN, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  strip.begin();
  strip.show();
  Serial.begin(9600);
}

void loop() {
  unsigned long currentTime = millis();
  float duration; // 在这里声明 duration 变量

  // 每隔 updateInterval 毫秒更新一次亮度
  if (currentTime - lastUpdateTime >= updateInterval) {
    lastUpdateTime = currentTime;

    // 读取滑动电位器值并映射到 fadeAmount
    int pot1_value = analogRead(POT1_PIN);
    fadeAmount = map(pot1_value, 0, 1023, 20, 80);  // 映射到 20-80

    // 更新亮度值
    brightness += fadeAmount;

    // 如果亮度超过 200，重置为 0
    if (brightness > 200) {
      brightness = 0;
    }

    // 应用亮度到 LED 灯带
    strip.setBrightness(brightness);
  }

  // 读取按钮状态
  int currentButtonState = digitalRead(BUTTON_PIN);
  if (currentButtonState == LOW && lastButtonState == HIGH) {
    toggleState = 1 - toggleState;
  }
  lastButtonState = currentButtonState;

  // 超声波测距
  float distance = checkdistance();
  int note_index;
  if (distance < 10) {
    note_index = 0;
  } else if (distance >= 50) {
    note_index = NUM_NOTES - 1;
  } else {
    note_index = floor((distance - 10) / ((50.0 - 10.0) / (NUM_NOTES)));
    if (note_index < 0) note_index = 0;
    if (note_index >= NUM_NOTES) note_index = NUM_NOTES - 1;
  }

  // 读取旋转电位器选择音阶
  int pot2_value = analogRead(POT2_PIN);
  float pot2_voltage = (pot2_value / 1023.0) * 5.0;
  float* selected_frequencies;
  String scale_name;
  if (pot2_value <= 204) {
    selected_frequencies = base_frequencies;
    scale_name = "C Major";
  } else if (pot2_value <= 409) {
    selected_frequencies = g_major_frequencies;
    scale_name = "G Major";
  } else if (pot2_value <= 614) {
    selected_frequencies = d_major_frequencies;
    scale_name = "D Major";
  } else if (pot2_value <= 818) {
    selected_frequencies = e_minor_frequencies;
    scale_name = "E Minor";
  } else {
    selected_frequencies = a_minor_frequencies;
    scale_name = "A Minor";
  }

  // 计算调整后的频率
  float base_frequency = selected_frequencies[note_index];

  // 映射频率到颜色并显示
  mapFrequencyToColor(base_frequency);

  // 灯光闪烁的时间
  duration = 0.1 * 400/fadeAmount;

  // 串口输出
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.print(" cm, Scale: ");
  Serial.print(scale_name);
  Serial.print(", Note: ");
  Serial.print(note_index);
  Serial.print(", Base Frequency: ");
  Serial.print(base_frequency);
  Serial.print(" Hz, Pot1 Voltage: ");
  Serial.print((analogRead(POT1_PIN) / 1023.0) * 5.0);
  Serial.print(" V, Pot2 Voltage: ");
  Serial.print(pot2_voltage);
  Serial.print(" V, Toggle State: ");
  Serial.print(toggleState);
  Serial.println();

  delay(5);  // 主循环延迟，控制其他操作频率
}