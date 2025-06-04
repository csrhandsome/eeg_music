import torch.nn as nn
import tqdm
import torch
from eeg_music.model.eegnet import EEGNet

class EEGNetRunner:
    def __init__(self, optimizer, criterion, device):
        self.model = EEGNet(chunk_size=128,
            num_electrodes=14,
            dropout=0.5,
            kernel_1=32,
            kernel_2=16,
            F1=8,
            F2=16,
            D=2,
            num_classes=4)
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device
        self.model.to(device)

    def compute_loss(self, train_loader, val_loader, num_epochs):
        """
        训练模型并计算损失
        
        参数:
        train_loader: 训练数据加载器
        val_loader: 验证数据加载器
        num_epochs: 训练轮数
        
        返回:
        训练心音轨迹 (dict): 包含训练和验证的损失与准确率
        """
        history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': []
        }
        
        for epoch in range(num_epochs):
            # 训练阶段
            self.model.train()
            running_loss = 0.0
            correct = 0
            total = 0
            
            for inputs, labels in tqdm.tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs} [Train]"):
                inputs = inputs.to(self.device)
                labels = labels.to(self.device)
                
                # 清零梯度
                self.optimizer.zero_grad()
                
                # 前向传播
                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)
                
                # 反向传播和优化
                loss.backward()
                self.optimizer.step()
                
                # 统计
                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
            
            train_loss = running_loss / len(train_loader)
            train_acc = 100.0 * correct / total
            history['train_loss'].append(train_loss)
            history['train_acc'].append(train_acc)
            
            # 验证阶段
            val_loss, val_acc = self.evaluate(val_loader)
            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)
            
            print(f"Epoch {epoch+1}/{num_epochs} - "
                  f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% - "
                  f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
            
        return history
    
    def evaluate(self, data_loader):
        """
        评估模型在给定数据上的性能
        
        参数:
        data_loader: 数据加载器
        
        返回:
        loss: 平均损失
        accuracy: 准确率 (%)
        """
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for inputs, labels in tqdm.tqdm(data_loader, desc="Evaluating"):
                inputs = inputs.to(self.device)
                labels = labels.to(self.device)
                
                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)
                
                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
                
        return running_loss / len(data_loader), 100.0 * correct / total

    def predict_emotion(self, test_loader):
        """
        预测情绪分类
        
        参数:
        test_loader: 测试数据加载器
        
        返回:
        predictions: 预测结果列表
        """
        self.model.eval()
        predictions = []
        
        with torch.no_grad():
            for inputs, _ in test_loader:
                inputs = inputs.to(self.device)
                outputs = self.model(inputs)
                _, predicted = outputs.max(1)
                predictions.extend(predicted.cpu().numpy())
                
        return predictions
        
    def save_model(self, path):
        """保存模型到指定路径"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, path)
        
    def load_model(self, path):
        """从指定路径加载模型"""
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])