// 定义引脚
#define TRIG_PIN A0  // 超声波 trig 引脚
#define ECHO_PIN A1  // 超声波 echo 引脚
#define POT1_PIN A2  // 滑动电位器引脚
#define POT2_PIN A3  // 旋转电位器引脚
#define BUTTON_PIN 4 // 按钮引脚

// 音符数量
#define NUM_NOTES 15  // 两个八度中的音符数量（C4-C6）

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
  698.46,  // F5
  783.99,  // G5
  880.00,  // A5
  987.77,  // B5
  1046.50  // C6
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
  1046.50, // C6
  1174.66, // D6
  1318.51, // E6
  1479.98, // F♯6
  1567.98  // G6
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
  783.99,  // G5
  880.00,  // A5
  987.77,  // B5
  1108.73, // C♯6
  1174.66  // D6
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
  880.00,  // A5
  987.77,  // B5
  1046.50, // C6
  1174.66, // D6
  1318.51  // E6
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
  1174.66, // D6
  1318.51, // E6
  1396.91, // F6
  1567.98, // G6
  1760.00  // A6
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

// 状态变量
int toggleState = 0;       // 切换状态，初始为0
int lastButtonState = HIGH; // 上一次按钮状态，初始为高电平（未按下）

void setup() {
  // 设置引脚模式
  pinMode(TRIG_PIN, OUTPUT);  // 超声波 trig
  pinMode(ECHO_PIN, INPUT);   // 超声波 echo
  pinMode(POT1_PIN, INPUT);   // 滑动电位器
  pinMode(POT2_PIN, INPUT);   // 旋转电位器
  pinMode(BUTTON_PIN, INPUT_PULLUP);  // 按钮，使用内部上拉电阻
  
  // 初始化串口通信
  Serial.begin(9600);
}

void loop() {
  // 读取按钮的当前状态
  int currentButtonState = digitalRead(BUTTON_PIN);

  // 检测按下事件（从高到低的转换）
  if (currentButtonState == LOW && lastButtonState == HIGH) {
    toggleState = 1 - toggleState;  // 切换状态
  }

  // 更新上一次按钮状态
  lastButtonState = currentButtonState;

  // 超声波测距
  float distance = checkdistance();
  
  // 根据距离计算音符索引
  int note_index;
  if (distance < 5) {
    note_index = 0;  // 小于5cm，固定为最低音符
  } else if (distance >= 50) {
    note_index = NUM_NOTES - 1;  // 大于等于50cm，固定为最高音符
  } else {
    // 将5-50cm区间均匀映射到15个音符
    note_index = floor((distance - 5) / ((50.0 - 5.0) / (NUM_NOTES - 1)));
    
    // 确保索引在有效范围内
    if (note_index < 0) note_index = 0;
    if (note_index >= NUM_NOTES) note_index = NUM_NOTES - 1;
  }
  
  // 读取旋转电位器（A3）值来选择音阶
  int pot2_value = analogRead(POT2_PIN);
  float pot2_voltage = (pot2_value / 978.0) * 5.0;  // 计算电压，保留原逻辑

  // 将旋转电位器的值（0-1023）分成五个区间
  float* selected_frequencies;  // 指向选定音阶的频率数组
  String scale_name;           // 音阶名称用于串口输出
  if (pot2_value <= 204) {     // 0-204: C大调
    selected_frequencies = base_frequencies;
    scale_name = "C Major";
  } else if (pot2_value <= 409) {  // 205-409: G大调
    selected_frequencies = g_major_frequencies;
    scale_name = "G Major";
  } else if (pot2_value <= 614) {  // 410-614: D大调
    selected_frequencies = d_major_frequencies;
    scale_name = "D Major";
  } else if (pot2_value <= 819) {  // 615-819: e小调
    selected_frequencies = e_minor_frequencies;
    scale_name = "E Minor";
  } else {                        // 820-1023: a小调
    selected_frequencies = a_minor_frequencies;
    scale_name = "A Minor";
  }

  // 获取基础音符频率
  float base_frequency = selected_frequencies[note_index];

  // 读取滑动电位器（A2）
  int pot1_value = analogRead(POT1_PIN);
  float pot1_voltage = (pot1_value / 978.0) * 5.0;  // 计算电压

  // 使用旋转电位器值计算音高弯曲因子
  float bend = (pot2_value - 512) / 512.0 * 0.05;  // 范围从 -0.05 到 0.05
  float factor = 1.0 + bend;  // 频率调整因子，范围 0.95 到 1.05
  float adjusted_frequency = base_frequency * factor;  // 调整后的频率

  // 输出到串口监视器（一行）
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.print(" cm, Scale: ");
  Serial.print(scale_name);
  Serial.print(", Note: ");
  Serial.print(note_index);
  Serial.print(", Adjusted Frequency: ");
  Serial.print(adjusted_frequency);
  Serial.print(" potentiometer ");
  Serial.print(pot1_voltage);
  Serial.print(" Rotary potentiometer: ");
  Serial.print(pot2_voltage);
  Serial.print(" Button State: ");
  Serial.print(toggleState);
  Serial.println();
  
  // 延迟以控制更新速率
  delay(200);  // 每200ms更新一次
}