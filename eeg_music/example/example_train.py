import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse
from eeg_music.train.eeg_dataset import MyEEGDataset
from eeg_music.train.eeg_runner import EEGNetRunner

def train(args):
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() and not args.no_cuda else 'cpu')
    print(f"使用设备: {device}")
    
    # 加载数据集
    dataset = MyEEGDataset(
        data_path=args.data_path,
        window_size=args.window_size,
        window_stride=args.window_stride,
        normalize=True
    )
    
    # 显示类别分布
    class_dist = dataset.get_class_distribution()
    print(f"类别分布: {class_dist}")
    
    # 可视化部分窗口
    if args.visualize:
        os.makedirs('plots', exist_ok=True)
        for i in range(min(5, len(dataset))):
            dataset.visualize_window(i, save_path=f'plots/window_{i}.png')
            
    # 划分训练集、验证集和测试集
    total_size = len(dataset)
    train_size = int(total_size * 0.7)
    val_size = int(total_size * 0.15)
    test_size = total_size - train_size - val_size
    
    train_dataset, val_dataset, test_dataset = random_split(
        dataset, [train_size, val_size, test_size],
        generator=torch.Generator().manual_seed(args.seed)
    )
    
    # 创建数据加载器
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size)
    
    # 设置损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    
    # 创建模型
    model = EEGNetRunner(
        optimizer=optim.Adam(
            [{'params': [p for n, p in EEGNetRunner(None, None, device).model.named_parameters()]}], 
            lr=args.learning_rate
        ),
        criterion=criterion,
        device=device
    )
    
    # 训练模型
    history = model.compute_loss(train_loader, val_loader, args.epochs)
    
    # 保存模型
    os.makedirs('models', exist_ok=True)
    model.save_model(f'models/eegnet_model_{args.window_size}_{args.window_stride}.pt')
    
    # 绘制训练历史
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='训练损失')
    plt.plot(history['val_loss'], label='验证损失')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(1, 2, 2)
    plt.plot(history['train_acc'], label='训练准确率')
    plt.plot(history['val_acc'], label='验证准确率')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('plots/training_history.png')
    
    # 在测试集上评估
    test_loss, test_acc = model.evaluate(test_loader)
    print(f"测试集结果 - Loss: {test_loss:.4f}, Accuracy: {test_acc:.2f}%")
    
    return model

def main():
    parser = argparse.ArgumentParser(description='EEG情绪分类模型训练')
    parser.add_argument('--data_path', type=str, required=True, help='数据文件路径')
    parser.add_argument('--batch_size', type=int, default=32, help='批量大小')
    parser.add_argument('--epochs', type=int, default=30, help='训练轮数')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='学习率')
    parser.add_argument('--window_size', type=int, default=128, help='窗口大小')
    parser.add_argument('--window_stride', type=int, default=64, help='窗口步长')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--no_cuda', action='store_true', help='禁用CUDA')
    parser.add_argument('--visualize', action='store_true', help='可视化数据窗口')
    
    args = parser.parse_args()
    
    # 设置随机种子
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    
    train(args)

if __name__ == "__main__":
    main() 