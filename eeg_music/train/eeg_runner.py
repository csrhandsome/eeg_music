import torch.nn as nn
import tqdm
from eeg_music.model.eegnet import EEGNet
class EEGNetTrainer:
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

    def compute_loss(self, train_loader, val_loader, num_epochs):
        for epoch in range(num_epochs):
            self.model.train()
            running_loss = 0.0
            correct = 0

    def predict_emotion(self, test_loader):
        self.model.eval()
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs = inputs.to(self.device)
                outputs = self.model(inputs)
                _, predicted = outputs.max(1)