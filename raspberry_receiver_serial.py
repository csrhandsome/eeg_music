import serial
import time

# 配置串口参数
SERIAL_PORT = '/dev/ttyACM0'  # 根据实际情况修改为你的虚拟串口号（Linux）
# SERIAL_PORT = 'COM3'        # 如果是Windows，修改为对应的COM端口号
BAUD_RATE = 9600              # 波特率与Arduino一致

def main():
    try:
        # 打开虚拟串口
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"成功连接到蓝牙虚拟串口 {SERIAL_PORT}，波特率 {BAUD_RATE}")

        while True:
            # 检查是否有数据可读
            if ser.in_waiting > 0:
                # 读取一行数据
                received_data = ser.readline().decode('utf-8').strip()
                print(f"接收到的数据: {received_data}")

            # 等待一段时间以避免CPU占用过高
            time.sleep(0.1)

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("虚拟串口已关闭")

if __name__ == "__main__":
    main()