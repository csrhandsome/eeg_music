// 定义引脚
#define TRIG_PIN A0  // 超声波 trig 引脚
#define ECHO_PIN A1  // 超声波 echo 引脚
#define POT_PIN A2   // 电位器引脚

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

void setup() {
  // 设置引脚模式
  pinMode(TRIG_PIN, OUTPUT);  // 超声波 trig
  pinMode(ECHO_PIN, INPUT);   // 超声波 echo
  pinMode(POT_PIN, INPUT);    // 电位器
  
  // 初始化串口通信
  Serial.begin(9600);
}

void loop() {
  // 超声波测距
  float distance = checkdistance();
  
  // 根据距离计算音符索引
  int note_index;
  if (distance < 5) {
    note_index = 0;  // 小于5cm，固定为最低音符C4
  } else if (distance >= 50) {
    note_index = NUM_NOTES - 1;  // 大于等于50cm，固定为最高音符C6
  } else {
    // 将5-50cm区间均匀映射到15个音符
    // 每个区间约为3.21cm ((50-5) / (15-1))
    note_index = floor((distance - 5) / ((50.0 - 5.0) / (NUM_NOTES - 1)));
    
    // 确保索引在有效范围内
    if (note_index < 0) note_index = 0;
    if (note_index >= NUM_NOTES) note_index = NUM_NOTES - 1;
  }
  
  // 获取音符频率
  float frequency = base_frequencies[note_index];

  // 电位器读取
  int sensorValue = analogRead(A2); //传感器接于模拟口0
  Serial.println(sensorValue); //从串口发送数据并换行
  
 // 输出到串口监视器（一行）
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.print(" cm, Note: ");
  Serial.print(note_index);
  Serial.print(", Frequency: ");
  Serial.print(frequency);
  Serial.print(" Hz, Potentiometer Voltage: ");
  Serial.print(sensorValue);
  Serial.println(" V");
  
  // 延迟以控制更新速率
  delay(200);  // 每200ms更新一次
}