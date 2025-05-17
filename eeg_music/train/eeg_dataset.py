import torch
from torch.utils.data import Dataset
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

class MyEEGDataset(Dataset):
    def __init__(self, data_path, window_size=128, window_stride=64, transform=None, normalize=True):
        """
        初始化EEG数据集
        
        参数:
        data_path (str): CSV数据文件路径
        window_size (int): 滑动窗口大小
        window_stride (int): 滑动窗口步长
        transform: 数据转换函数
        normalize (bool): 是否对特征进行标准化
        """
        # 加载数据
        self.data = np.genfromtxt(data_path, delimiter=',', skip_header=1)
        self.features = self.data[:,1:-1]  # 去掉第一列(timestamp)和最后一列(标签)
        self.mood = self.data[:,-1]
        self.transform = transform
        # 窗口大小
        self.window_size = window_size
        # 窗口步长 
        self.window_stride = window_stride
        
        # 标准化特征
        if normalize:
            self.scaler = StandardScaler()
            self.features = self.scaler.fit_transform(self.features)
        
        # 计算有效窗口数量
        self.num_windows = max(0, (len(self.features) - window_size) // window_stride + 1)
        
    def __len__(self):
        return self.num_windows
        
    def __getitem__(self, idx):
        """返回一个滑动窗口的数据"""
        start_idx = idx * self.window_stride
        end_idx = start_idx + self.window_size
        
        # 获取窗口内的特征数据
        window_data = self.features[start_idx:end_idx, :]
        
        # 使用窗口末尾的情绪作为标签（或者可以使用窗口内的众数）
        mood = self.mood[end_idx - 1]
        
        # 转换数据格式为tensor
        window_data = torch.tensor(window_data, dtype=torch.float32)
        
        if self.transform:
            window_data = self.transform(window_data)
            
        return window_data, torch.tensor(mood, dtype=torch.float32)
    
    def visualize_window(self, idx, save_path=None, feature_names=None):
        """
        可视化指定索引的窗口数据
        
        参数:
        idx (int): 窗口索引
        save_path (str): 保存图像的路径,None表示不保存
        feature_names (list): 特征名称列表
        """
        if idx >= self.num_windows:
            raise ValueError(f"索引 {idx} 超出范围，数据集只有 {self.num_windows} 个窗口")
        
        start_idx = idx * self.window_stride
        end_idx = start_idx + self.window_size
        
        window_data = self.features[start_idx:end_idx, :]
        window_mood = self.mood[start_idx:end_idx]
        
        # 如果没有提供特征名称，则使用默认名称
        if feature_names is None:
            feature_names = [f"Feature {i+1}" for i in range(window_data.shape[1])]
            
        # 情绪标签映射
        mood_labels = {0: "开心", 1: "悲伤", 2: "愤怒", 3: "平静"}
        
        # 创建多子图
        num_features = window_data.shape[1]
        fig, axs = plt.subplots(num_features, 1, figsize=(10, 2*num_features))
        fig.suptitle(f"窗口 #{idx} (样本 {start_idx}-{end_idx})", fontsize=16)
        # axs是子图的列表  
        for i in range(num_features):
            axs[i].plot(window_data[:, i])
            axs[i].set_ylabel(feature_names[i])
            axs[i].grid(True)
        
        # 在底部添加情绪信息
        mood_text = f"情绪: {mood_labels.get(int(window_mood[-1]), '未知')}"
        fig.text(0.5, 0.01, mood_text, ha='center', fontsize=12)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
    
    def get_class_distribution(self):
        """获取数据集的类别分布"""
        # 使用每个窗口末尾的情绪作为窗口的情绪
        window_moods = [self.mood[idx * self.window_stride + self.window_size - 1] for idx in range(self.num_windows)]
        unique, counts = np.unique(window_moods, return_counts=True)
        return dict(zip(unique, counts))