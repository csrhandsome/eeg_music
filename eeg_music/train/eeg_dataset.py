import torch
from torch.utils.data import Dataset
import pandas as pd


class MyEEGDataset(Dataset):
    def __init__(self, data_path, transform=None):
        # 加载你的数据
        self.data = pd.read_csv(data_path)
        self.transform = transform
        
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        sample = self.data.iloc[idx]
        if self.transform:
            sample = self.transform(sample)
        return sample