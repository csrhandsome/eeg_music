"""
EEGNet推理脚本 - 树莓派部署版本
===============================

这个脚本用于在树莓派上运行EEGNet模型进行实时EEG数据推理。
它包含了数据预处理、模型加载和推理的完整流程。

使用方法:
    python3 eegnet_inference.py --model_path deploy_model_quantized.pt

"""

import torch
import numpy as np
import time
import argparse
from torcheeg import transforms
import threading
import queue

# 解析命令行参数
parser = argparse.ArgumentParser(description='EEGNet推理脚本')
parser.add_argument('--model_path', type=str, default='deploy_model_quantized.pt', help='模型文件路径')
parser.add_argument('--num_electrodes', type=int, default=32, help='EEG电极数量')
parser.add_argument('--sampling_rate', type=int, default=128, help='采样率(Hz)')
parser.add_argument('--chunk_size', type=int, default=128, help='每个数据段的采样点数')
parser.add_argument('--simulation', action='store_true', help='使用模拟数据而非真实数据')
args = parser.parse_args()

# 函数：加载模型
def load_model(model_path):
    print(f"正在加载模型: {model_path}")
    try:
        model = torch.jit.load(model_path)
        model.eval()
        print("模型加载成功")
        return model
    except Exception as e:
        print(f"模型加载失败: {e}")
        return None

# 函数：预处理EEG数据
def preprocess_eeg(eeg_data, sampling_rate=128):
    """
    对EEG数据进行预处理
    Args:
        eeg_data: 形状为 [num_electrodes, chunk_size] 的numpy数组
        sampling_rate: 采样率
    Returns:
        处理后的tensor,准备输入到模型
    """
    try:
        # 创建预处理转换
        transform = transforms.Compose([
            transforms.BandDifferentialEntropy(sampling_rate=sampling_rate),
            transforms.To2d(),
            transforms.ToTensor()
        ])
        
        # 应用转换
        processed = transform(eeg=eeg_data)['eeg']
        # 增加批次维度
        processed = processed.unsqueeze(0)
        return processed
    except Exception as e:
        print(f"预处理失败: {e}")
        return None

# 函数：执行推理
def infer(model, eeg_data):
    """
    使用模型进行推理
    Args:
        model: 加载的PyTorch模型
        eeg_data: 预处理后的EEG数据张量
    Returns:
        预测的类别，置信度和推理时间
    """
    try:
        with torch.no_grad():
            start_time = time.time()
            outputs = model(eeg_data)
            inference_time = time.time() - start_time
            
            # 获取预测结果
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            predicted_class = torch.argmax(probabilities, dim=1).item()
            confidence = probabilities[0][predicted_class].item()
            
            print(f"推理时间: {inference_time*1000:.2f}毫秒")
            return predicted_class, confidence, inference_time
    except Exception as e:
        print(f"推理失败: {e}")
        return None, 0, 0

# 函数：生成模拟EEG数据
def generate_mock_eeg_data(num_electrodes, chunk_size):
    """
    生成模拟EEG数据用于测试
    """
    return np.random.randn(num_electrodes, chunk_size)

# 函数：从实际EEG设备读取数据
def read_eeg_from_device():
    """
    从EEG设备读取实际数据
    注意：此函数需要根据您的实际设备进行修改
    """
    # TODO: 实现与实际EEG设备的接口
    # 这里应该是与您的EEG设备通信的代码
    # 例如，使用串口、蓝牙或USB连接读取数据
    
    # 示例代码 - 替换为实际的设备读取代码
    print("警告：使用模拟数据代替实际设备数据")
    return generate_mock_eeg_data(args.num_electrodes, args.chunk_size)

# 数据采集线程
def data_acquisition_thread(data_queue, stop_event):
    """
    持续从设备获取EEG数据并放入队列
    Args:
        data_queue: 线程安全的队列，用于存放采集到的数据
        stop_event: 停止线程的事件
    """
    print("开始数据采集线程")
    while not stop_event.is_set():
        try:
            # 获取EEG数据（实际设备或模拟）
            if args.simulation:
                eeg_data = generate_mock_eeg_data(args.num_electrodes, args.chunk_size)
            else:
                eeg_data = read_eeg_from_device()
            
            # 将数据放入队列
            data_queue.put(eeg_data)
            
            # 控制采集频率
            time.sleep(0.1)  # 每100毫秒采集一次
        except Exception as e:
            print(f"数据采集错误: {e}")
            time.sleep(1)  # 发生错误时暂停一秒
    
    print("数据采集线程已停止")

# 推理线程
def inference_thread(model, data_queue, result_queue, stop_event):
    """
    持续从队列获取数据并进行推理
    Args:
        model: 加载的模型
        data_queue: 包含EEG数据的队列
        result_queue: 存放推理结果的队列
        stop_event: 停止线程的事件
    """
    print("开始推理线程")
    while not stop_event.is_set():
        try:
            # 非阻塞方式获取数据
            try:
                eeg_data = data_queue.get(block=True, timeout=1.0)
            except queue.Empty:
                continue
            
            # 预处理数据
            processed_data = preprocess_eeg(eeg_data, args.sampling_rate)
            if processed_data is None:
                continue
            
            # 执行推理
            predicted_class, confidence, inference_time = infer(model, processed_data)
            if predicted_class is not None:
                # 将结果放入结果队列
                result_queue.put((predicted_class, confidence, inference_time))
        except Exception as e:
            print(f"推理错误: {e}")
    
    print("推理线程已停止")

# 结果处理线程
def result_processing_thread(result_queue, stop_event):
    """
    处理和显示推理结果
    Args:
        result_queue: 包含推理结果的队列
        stop_event: 停止线程的事件
    """
    print("开始结果处理线程")
    total_inferences = 0
    total_time = 0
    
    while not stop_event.is_set():
        try:
            # 非阻塞方式获取结果
            try:
                predicted_class, confidence, inference_time = result_queue.get(block=True, timeout=1.0)
            except queue.Empty:
                continue
            
            # 更新统计信息
            total_inferences += 1
            total_time += inference_time
            
            # 显示结果
            emotion = "积极" if predicted_class == 1 else "消极"
            print(f"预测情绪: {emotion}, 置信度: {confidence:.4f}")
            
            # 每10次推理显示一次平均性能
            if total_inferences % 10 == 0:
                avg_time = (total_time / total_inferences) * 1000
                print(f"性能统计: 平均推理时间 {avg_time:.2f}毫秒")
        except Exception as e:
            print(f"结果处理错误: {e}")
    
    print("结果处理线程已停止")

# 主函数
def main():
    print("========== EEGNet 树莓派推理程序 ==========")
    print(f"电极数量: {args.num_electrodes}")
    print(f"采样率: {args.sampling_rate}Hz")
    print(f"数据段大小: {args.chunk_size}点")
    
    # 加载模型
    model = load_model(args.model_path)
    if model is None:
        return
    
    # 使用队列和线程实现异步处理
    data_queue = queue.Queue(maxsize=10)    # 数据队列
    result_queue = queue.Queue(maxsize=10)  # 结果队列
    stop_event = threading.Event()          # 用于停止线程的事件
    
    # 创建并启动线程
    acquisition_thread = threading.Thread(target=data_acquisition_thread, args=(data_queue, stop_event))
    inference_thread_obj = threading.Thread(target=inference_thread, args=(model, data_queue, result_queue, stop_event))
    result_thread = threading.Thread(target=result_processing_thread, args=(result_queue, stop_event))
    
    acquisition_thread.daemon = True
    inference_thread_obj.daemon = True
    result_thread.daemon = True
    
    acquisition_thread.start()
    inference_thread_obj.start()
    result_thread.start()
    
    # 模式提示
    if args.simulation:
        print("模式: 模拟数据")
    else:
        print("模式: 实际设备数据")
    
    print("系统已启动. 按Ctrl+C停止...")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n接收到停止信号")
        stop_event.set()  # 通知所有线程停止
        
        # 等待线程结束
        acquisition_thread.join(timeout=2.0)
        inference_thread_obj.join(timeout=2.0)
        result_thread.join(timeout=2.0)
        
        print("程序已停止")

if __name__ == "__main__":
    main() 