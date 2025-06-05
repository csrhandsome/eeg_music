import numpy as np
import pandas as pd
import pickle
import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
warnings.filterwarnings('ignore')


class KNNClassifier:
    """
    基于KNN的脑电信号分类器
    用于根据EEG特征预测情绪状态
    """
    
    def __init__(self, n_neighbors=4, weights='uniform', algorithm='auto', metric='minkowski'):
        """
        初始化KNN分类器
        
        参数:
            n_neighbors: K值,邻居数量,默认4
            weights: 权重函数，'uniform'或'distance'
            algorithm: 算法选择，'auto', 'ball_tree', 'kd_tree', 'brute'
            metric: 距离度量，默认'minkowski'
        """
        self.n_neighbors = n_neighbors
        self.weights = weights
        self.algorithm = algorithm
        self.metric = metric
        
        # 初始化模型和预处理器
        self.knn = KNeighborsClassifier(
            n_neighbors=n_neighbors,
            weights=weights,
            algorithm=algorithm,
            metric=metric
        )
        self.scaler = StandardScaler()
        
        # 训练状态
        self.is_trained = False
        self.feature_names = None
        self.class_names = None
        
        # 性能指标
        self.train_accuracy = None
        self.val_accuracy = None
        self.cv_scores = None
        
        print(f"KNN分类器初始化完成 - K={n_neighbors}, weights={weights}")
    
    def load_data(self, csv_path):
        try:
            # 读取CSV数据
            data = pd.read_csv(csv_path)
            print(f"已加载数据: {data.shape}")
            print(f"列名: {list(data.columns)}")
            
            # 提取特征 ([:,1:-1]) 和标签 ([:,-1])
            X = data.iloc[:, 1:-1].values  # 除了第一列timestamp和最后一列label
            y = data.iloc[:, -1].values    # 最后一列作为标签
            
            # 保存特征名称
            self.feature_names = list(data.columns[1:-1])
            
            # 获取类别信息
            unique_labels = np.unique(y)
            self.class_names = [str(label) for label in unique_labels]
            
            print(f"特征形状: {X.shape}")
            print(f"标签形状: {y.shape}")
            print(f"特征名称: {self.feature_names}")
            print(f"类别: {self.class_names}")
            print(f"各类别样本数量: {pd.Series(y).value_counts().to_dict()}")
            
            return X, y
            
        except Exception as e:
            print(f"加载数据失败: {e}")
            return None, None
    
    def preprocess_data(self, X_train, X_test=None):
        # 拟合并转换训练数据
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        if X_test is not None:
            # 使用训练数据的参数转换测试数据
            X_test_scaled = self.scaler.transform(X_test)
            return X_train_scaled, X_test_scaled
        
        return X_train_scaled
    
    def grid_search(self, X, y, cv=5):
        """
        网格搜索最优超参数
        
        参数:
            X: 特征矩阵
            y: 标签向量
            cv: 交叉验证折数
            
        返回:
            最优参数字典
        """
        print("开始网格搜索最优参数...")
        
        # 定义参数网格
        param_grid = {
            'n_neighbors': [3, 5, 7, 9, 11, 15],
            'weights': ['uniform', 'distance'],
            'algorithm': ['auto', 'ball_tree', 'kd_tree'],
            'metric': ['euclidean', 'manhattan', 'minkowski']
        }
        
        # 创建网格搜索对象
        grid_search = GridSearchCV(
            KNeighborsClassifier(),
            param_grid,
            cv=cv,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        # 执行网格搜索
        grid_search.fit(X, y)
        
        print(f"最优参数: {grid_search.best_params_}")
        print(f"最优交叉验证分数: {grid_search.best_score_:.4f}")
        
        # 更新模型参数
        self.knn = grid_search.best_estimator_
        
        return grid_search.best_params_
    

    def train(self, X, y, test_size=0.2, random_state=42, use_grid_search=False, cv=5):
        print("开始训练KNN分类器...")
        # 分割数据
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # 数据预处理
        X_train_scaled, X_test_scaled = self.preprocess_data(X_train, X_test)
        
        # 网格搜索（可选）
        if use_grid_search:
            self.grid_search(X_train_scaled, y_train, cv=cv)
        
        # 训练模型
        self.knn.fit(X_train_scaled, y_train)
        
        # 预测
        y_train_pred = self.knn.predict(X_train_scaled)
        y_test_pred = self.knn.predict(X_test_scaled)
        
        # 计算准确率
        self.train_accuracy = accuracy_score(y_train, y_train_pred)
        self.val_accuracy = accuracy_score(y_test, y_test_pred)
        
        # 交叉验证
        self.cv_scores = cross_val_score(self.knn, X_train_scaled, y_train, cv=cv)
        
        # 标记为已训练
        self.is_trained = True
        
        # 打印结果
        print(f"\n训练完成!")
        print(f"训练集准确率: {self.train_accuracy:.4f}")
        print(f"验证集准确率: {self.val_accuracy:.4f}")
        print(f"交叉验证平均分数: {self.cv_scores.mean():.4f} (+/- {self.cv_scores.std() * 2:.4f})")
        
        # 详细分类报告
        print(f"\n验证集分类报告:")
        print(classification_report(y_test, y_test_pred, target_names=self.class_names))
        
        # 混淆矩阵
        print(f"\n混淆矩阵:")
        cm = confusion_matrix(y_test, y_test_pred)
        print(cm)
        
        return {
            'train_accuracy': self.train_accuracy,
            'val_accuracy': self.val_accuracy,
            'cv_scores': self.cv_scores,
            'classification_report': classification_report(y_test, y_test_pred, target_names=self.class_names, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_test_pred).tolist(),
            'y_test': y_test,
            'y_test_pred': y_test_pred
        }
    
    def predict(self, X):
        if not self.is_trained:
            raise ValueError("模型尚未训练,请先调用train()方法")
        
        # 标准化输入数据
        X_scaled = self.scaler.transform(X)
        
        # 预测
        predictions = self.knn.predict(X_scaled)
        
        return predictions
    
    def predict_proba(self, X):
        if not self.is_trained:
            raise ValueError("模型尚未训练,请先调用train()方法")
        
        # 标准化输入数据
        X_scaled = self.scaler.transform(X)
        
        # 预测概率
        probabilities = self.knn.predict_proba(X_scaled)
        
        return probabilities
    
    def save_model(self, model_path):
        if not self.is_trained:
            raise ValueError("模型尚未训练，无法保存")
        
        try:
            # 创建保存目录
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # 保存模型数据
            model_data = {
                'knn': self.knn,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'class_names': self.class_names,
                'train_accuracy': self.train_accuracy,
                'val_accuracy': self.val_accuracy,
                'cv_scores': self.cv_scores
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"模型已保存到: {model_path}")
            
        except Exception as e:
            print(f"保存模型失败: {e}")
    
    def load_model(self, model_path):
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            # 恢复模型状态
            self.knn = model_data['knn']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.class_names = model_data['class_names']
            self.train_accuracy = model_data['train_accuracy']
            self.val_accuracy = model_data['val_accuracy']
            self.cv_scores = model_data['cv_scores']
            
            self.is_trained = True
            
            
        except Exception as e:
            print(f"加载模型失败: {e}")
    
    def get_feature_importance(self):
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        # KNN没有直接的特征重要性，这里返回特征名称
        importance_dict = {name: 1.0/len(self.feature_names) for name in self.feature_names}
        
        return importance_dict 