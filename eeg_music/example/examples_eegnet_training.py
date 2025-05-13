"""
使用EEGNet进行训练和部署
=======================

在本教程中，我们将展示如何使用TorchEEG库训练一个EEGNet模型，并将其部署到树莓派上进行实时推理。EEGNet是一个轻量级的CNN模型，
非常适合资源受限的设备如树莓派进行部署。

"""

######################################################################
# 步骤1：加载和准备数据集
# ----------------------------------------------
#
# 首先，我们使用TorchEEG中内置的DEAP数据集作为示例。DEAP数据集包含32个受试者观看音乐视频时的EEG记录，标记了情感状态（如效价和唤醒度）。
# 我们使用频带差分熵作为特征，并将EEG信号转换为2D表示。
#

from torcheeg.datasets import DEAPDataset
from torcheeg import transforms
from torcheeg.model_selection import KFoldGroupbyTrial
from torch.utils.data import DataLoader
from torcheeg.models import EEGNet
from torcheeg.trainers import ClassifierTrainer

import pytorch_lightning as pl
import torch
import os

# 设置数据文件夹路径
io_path = './eegnet_training/deap'
os.makedirs(os.path.dirname(io_path), exist_ok=True)

# 加载数据集
dataset = DEAPDataset(
    io_path=io_path,
    root_path='./data_preprocessed_python',  # 请确保您已下载DEAP数据集并放在此路径
    offline_transform=transforms.Compose([
        transforms.BandDifferentialEntropy(sampling_rate=128, apply_to_baseline=True),
    ]),
    online_transform=transforms.Compose([
        transforms.BaselineRemoval(),
        transforms.To2d(),
        transforms.ToTensor()
    ]),
    label_transform=transforms.Compose([
        transforms.Select('valence'),
        transforms.Binary(5.0),  # 将效价分为两类：低(<5)和高(>=5)
    ]),
    chunk_size=128,  # 1秒数据(采样率为128Hz)
    num_baseline=1,
    baseline_chunk_size=128,
    num_worker=4)

######################################################################
# 步骤2：数据分割和加载器创建
# ----------------------------------------------
#
# 使用K折交叉验证分割数据集，为每一折创建训练和验证加载器。
#

# 创建k-fold划分
k_fold = KFoldGroupbyTrial(
    n_splits=5,
    split_path='./eegnet_training/split'
)

######################################################################
# 步骤3：定义和训练EEGNet模型
# ----------------------------------------------
#
# 配置并训练EEGNet模型。我们使用了针对树莓派优化的轻量级配置。
#

for i, (train_dataset, val_dataset) in enumerate(k_fold.split(dataset)):
    # 创建数据加载器
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

    # 创建EEGNet模型 - 轻量级配置适合树莓派部署
    model = EEGNet(
        chunk_size=128,           # 1秒数据，128个采样点
        num_electrodes=32,        # DEAP数据集有32个电极
        F1=4,                     # 减少滤波器数量以降低计算复杂度
        F2=8,                     # 减少第二层滤波器数量
        D=2,                      # 深度乘数
        num_classes=2,            # 二分类任务
        kernel_1=32,              # 减小卷积核尺寸
        kernel_2=8,               # 减小第二层卷积核尺寸
        dropout=0.25              # 添加适当的dropout防止过拟合
    )

    # 配置训练器
    trainer = ClassifierTrainer(
        model=model,
        num_classes=2,
        lr=1e-3,                 # 使用较大的学习率加速训练
        weight_decay=1e-4,
        metrics=['accuracy', 'f1score'],  # 记录准确率和F1分数
        accelerator="cpu"        # 可以在训练时使用GPU，但为了测试在树莓派上的性能，这里使用CPU
    )

    # 训练模型
    trainer.fit(
        train_loader,
        val_loader,
        max_epochs=20,           # 减少训练轮次，加快训练速度
        default_root_dir=f'./eegnet_training/model/{i}',
        callbacks=[pl.callbacks.ModelCheckpoint(save_last=True)],
        enable_progress_bar=True,
        enable_model_summary=True
    )

    # 测试模型
    score = trainer.test(val_loader)[0]
    print(f'Fold {i} test accuracy: {score["test_accuracy"]:.4f}, F1 score: {score["test_f1score"]:.4f}')

    # 保存用于部署的模型
    if i == 0:  # 仅保存第一折的模型用于部署示例
        deploy_model_path = f'./eegnet_training/deploy_model.pt'
        scripted_model = torch.jit.script(model)
        scripted_model.save(deploy_model_path)
        print(f"部署模型已保存至: {deploy_model_path}")

######################################################################
# 步骤4：模型优化和量化
# ----------------------------------------------
#
# 对训练好的模型进行优化和量化，使其在树莓派等资源受限设备上运行更高效。
#

# 加载最佳模型
best_model_path = './eegnet_training/model/0/version_0/checkpoints/last.ckpt'
model = EEGNet(
    chunk_size=128,
    num_electrodes=32,
    F1=4,
    F2=8,
    D=2,
    num_classes=2,
    kernel_1=32,
    kernel_2=8,
    dropout=0.25
)

# 加载权重
checkpoint = torch.load(best_model_path, map_location=torch.device('cpu'))
model.load_state_dict(checkpoint['state_dict'], strict=False)
model.eval()

# 静态量化 - 减小模型尺寸并提高推理速度
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear, torch.nn.Conv2d},
    dtype=torch.qint8
)

# 保存量化后的模型
quantized_model_path = './eegnet_training/deploy_model_quantized.pt'
torch.jit.script(quantized_model).save(quantized_model_path)
print(f"量化后的模型已保存至: {quantized_model_path}")

# 打印模型大小
import os
original_size = os.path.getsize(deploy_model_path) / (1024 * 1024)
quantized_size = os.path.getsize(quantized_model_path) / (1024 * 1024)
print(f"原始模型大小: {original_size:.2f} MB")
print(f"量化后模型大小: {quantized_size:.2f} MB")
print(f"大小减少: {(1 - quantized_size/original_size) * 100:.2f}%")

######################################################################
# 步骤5：在树莓派上部署的代码
# ----------------------------------------------
#
# 以下是在树莓派上运行优化后模型的示例代码。该代码应该保存为单独的Python文件，并在树莓派上运行。
#

# 保存以下代码为 eegnet_inference.py
"""
import torch
import numpy as np
import time
from torcheeg import transforms

# 函数：加载模型
def load_model(model_path):
    model = torch.jit.load(model_path)
    model.eval()
    return model

# 函数：预处理EEG数据
def preprocess_eeg(eeg_data, sampling_rate=128):
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

# 函数：执行推理
def infer(model, eeg_data):
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

# 主函数：实时EEG处理流程
def main():
    print("加载EEGNet模型...")
    model = load_model("deploy_model_quantized.pt")
    
    # 此处应该连接实际的EEG设备获取数据
    # 在本例中我们使用模拟数据进行演示
    
    print("开始模拟EEG数据流...")
    for i in range(10):  # 模拟10次推理
        # 模拟生成EEG数据 [32通道, 128个采样点]
        mock_eeg_data = np.random.randn(32, 128)
        
        # 预处理数据
        processed_data = preprocess_eeg(mock_eeg_data)
        
        # 执行推理
        predicted_class, confidence, _ = infer(model, processed_data)
        
        # 输出结果
        emotion = "积极" if predicted_class == 1 else "消极"
        print(f"预测情绪: {emotion}, 置信度: {confidence:.4f}")
        
        # 模拟数据采集延迟
        time.sleep(0.5)
    
    print("演示完成")

if __name__ == "__main__":
    main()
"""

######################################################################
# 步骤6：在树莓派上部署的指南
# ----------------------------------------------
#
# 要在树莓派上部署模型，请按照以下步骤操作：
#
# 1. 在树莓派上安装必要的依赖项:
#    ```bash
#    sudo apt-get update
#    sudo apt-get install -y python3-pip python3-dev libopenblas-dev
#    pip3 install https://github.com/pytorch/pytorch/releases/download/v1.9.0/torch-1.9.0-cp39-cp39-linux_aarch64.whl
#    pip3 install numpy scipy scikit-learn
#    pip3 install torcheeg  # 安装TorchEEG库
#    ```
#
# 2. 将量化后的模型文件 `deploy_model_quantized.pt` 传输到树莓派:
#    ```bash
#    scp deploy_model_quantized.pt pi@<树莓派IP地址>:~/eeg_project/
#    ```
#
# 3. 将推理脚本 `eegnet_inference.py` 传输到树莓派:
#    ```bash
#    scp eegnet_inference.py pi@<树莓派IP地址>:~/eeg_project/
#    ```
#
# 4. 在树莓派上运行推理代码:
#    ```bash
#    cd ~/eeg_project/
#    python3 eegnet_inference.py
#    ```
#
# 5. 连接实际的EEG设备:
#    修改 `eegnet_inference.py` 文件，将模拟数据替换为从实际EEG设备读取的数据。
#    您可能需要使用特定的设备驱动或API来获取数据。

######################################################################
# 性能优化技巧
# ----------------------------------------------
#
# 为了在树莓派等资源受限设备上获得最佳性能，可以考虑以下优化策略:
#
# 1. 减少模型的层数和滤波器数量
# 2. 使用较小的卷积核尺寸
# 3. 对模型进行量化，如上面示例中所示
# 4. 使用批处理推理而非单样本推理
# 5. 降低输入数据的采样率或维度
# 6. 使用异步处理，将数据采集和模型推理分开
#
# 通过这些优化，可以显著提高EEGNet在树莓派上的推理速度，使实时EEG分类任务成为可能。 