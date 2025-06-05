import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import StratifiedKFold
import seaborn as sns
from eeg_music.model.knn_classifier import KNNClassifier
# # 添加项目根目录到Python路径
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    
class KNN_Runner:
    """
    多用户EEG分类器
    支持处理多个用户的数据，进行跨用户或用户特定的情绪分类
    """
    
    def __init__(self,mindwave_reader=None):
        self.users = ['murmur', 'csr', 'tour' , 'xiayi']
        self.data_dir = 'data/eeg'
        self.user_data = {}
        self.combined_data = None
        self.label_encoder = LabelEncoder()
        self.classifier = None
        self.mindwave_reader = mindwave_reader
        # 预测用的KNN分类器，只初始化一次
        self.knn_classifier = None
    def load_all_users_data(self):
        """
        加载所有用户的数据
        """
        print("=" * 60)
        print("加载多用户EEG数据")
        print("=" * 60)
        
        for user in self.users:
            user_dir = os.path.join(self.data_dir, user)
            
            if not os.path.exists(user_dir):
                print(f"用户 {user} 的数据目录不存在: {user_dir}")
                continue
                
            # 查找用户的所有CSV文件
            csv_files = []
            for file in os.listdir(user_dir):
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(user_dir, file))
            
            if not csv_files:
                print(f"用户 {user} 没有数据文件")
                continue
            
            print(f"\n用户 {user}:")
            user_data_list = []
            
            for csv_file in csv_files:
                try:
                    data = pd.read_csv(csv_file)
                    print(f"  加载文件: {os.path.basename(csv_file)} - 形状: {data.shape}")
                    
                    # 添加用户标识列
                    data['user'] = user
                    user_data_list.append(data)
                    
                except Exception as e:
                    print(f"  加载文件 {csv_file} 失败: {e}")
                    continue
            
            if user_data_list:
                # 合并用户的所有数据
                user_combined = pd.concat(user_data_list, ignore_index=True)
                self.user_data[user] = user_combined
                print(f"  用户 {user} 总数据: {user_combined.shape}")
                print(f"  情绪分布: {user_combined['mood'].value_counts().to_dict()}")
        
        if not self.user_data:
            raise ValueError("没有加载到任何用户数据")
        
        # 合并所有用户数据
        all_data = []
        for user, data in self.user_data.items():
            all_data.append(data)
        
        self.combined_data = pd.concat(all_data, ignore_index=True)
        print(f"\n总体数据形状: {self.combined_data.shape}")
        print(f"总体情绪分布: {self.combined_data['mood'].value_counts().to_dict()}")
        print(f"用户分布: {self.combined_data['user'].value_counts().to_dict()}")
    
    def visualize_user_data(self, save_plots=False, confusion_matrix_data=None):
        """
        可视化多用户数据分析
        
        参数:
            save_plots: 是否保存图表
            confusion_matrix_data: 混淆矩阵数据，格式为 (y_true, y_pred)
        """
        print(f"\n" + "=" * 60)
        print("数据可视化分析")
        print("=" * 60)
        
        # 设置matplotlib字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建子图
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Multi-User EEG Data Analysis', fontsize=16)
        
        # 1. 用户数据量分布
        user_counts = self.combined_data['user'].value_counts()
        axes[0,0].bar(user_counts.index, user_counts.values, color=['skyblue', 'lightgreen', 'lightcoral', 'lightyellow'])
        axes[0,0].set_title('User Data Distribution')
        axes[0,0].set_xlabel('User')
        axes[0,0].set_ylabel('Data Count')
        for i, v in enumerate(user_counts.values):
            axes[0,0].text(i, v + max(user_counts.values)*0.01, str(v), ha='center')
        
        # 2. 情绪分布
        mood_counts = self.combined_data['mood'].value_counts().sort_index()
        # 添加情绪标签映射
        mood_labels = {0: 'Happy', 1: 'Sad', 2: 'Angry', 3: 'Peaceful'}
        pie_labels = [f'{mood_labels.get(k, k)}\n({v} samples)' for k, v in mood_counts.items()]
        
        axes[0,1].pie(mood_counts.values, labels=pie_labels, autopct='%1.1f%%', 
                     colors=['gold', 'lightblue', 'lightcoral', 'lightgreen'])
        axes[0,1].set_title('Overall Emotion Distribution')
        
        # 3. 用户-情绪交叉分布
        user_mood_crosstab = pd.crosstab(self.combined_data['user'], self.combined_data['mood'])
        # 为交叉表添加列标签
        mood_label_names = [mood_labels.get(col, str(col)) for col in user_mood_crosstab.columns]
        
        print(f"用户-情绪交叉表形状: {user_mood_crosstab.shape}")
        print(f"用户-情绪交叉表数据:\n{user_mood_crosstab}")
        
        # 使用手动绘制方法
        im = axes[1,0].imshow(user_mood_crosstab.values, interpolation='nearest', cmap='Blues')
        axes[1,0].figure.colorbar(im, ax=axes[1,0], label='Sample Count')
        
        # 手动添加数字标注
        crosstab_values = user_mood_crosstab.values
        thresh = crosstab_values.max() / 2.
        for i in range(crosstab_values.shape[0]):
            for j in range(crosstab_values.shape[1]):
                color = "white" if crosstab_values[i, j] > thresh else "black"
                axes[1,0].text(j, i, f'{crosstab_values[i, j]}', 
                              ha="center", va="center", 
                              color=color, fontsize=10, weight='bold')
        
        # 设置标签
        axes[1,0].set_xticks(range(len(mood_label_names)))
        axes[1,0].set_yticks(range(len(user_mood_crosstab.index)))
        axes[1,0].set_xticklabels(mood_label_names)
        axes[1,0].set_yticklabels(user_mood_crosstab.index)
        
        axes[1,0].set_title('User-Emotion Cross Distribution')
        axes[1,0].set_xlabel('Emotion')
        axes[1,0].set_ylabel('User')
        
        # 确保标签可见
        axes[1,0].tick_params(axis='x', labelsize=9)
        axes[1,0].tick_params(axis='y', labelsize=9)
        
        # 4. 混淆矩阵或关键特征分布
        if confusion_matrix_data is not None:
            print("正在绘制混淆矩阵...")
            y_true, y_pred = confusion_matrix_data
            from sklearn.metrics import confusion_matrix, accuracy_score
            cm = confusion_matrix(y_true, y_pred)
            
            # 获取实际出现的类别
            unique_labels = sorted(np.unique(np.concatenate([y_true, y_pred])))
            display_labels = [mood_labels.get(label, f'Unknown({label})') for label in unique_labels]
            
            print(f"混淆矩阵形状: {cm.shape}")
            print(f"标签: {display_labels}")
            print(f"混淆矩阵数据:\n{cm}")
            
            # 绘制混淆矩阵 - 使用更简单的设置
            im = axes[1,1].imshow(cm, interpolation='nearest', cmap='Blues')
            axes[1,1].figure.colorbar(im, ax=axes[1,1], label='Sample Count')
            
            # 手动添加数字标注
            thresh = cm.max() / 2.
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    color = "white" if cm[i, j] > thresh else "black"
                    axes[1,1].text(j, i, f'{cm[i, j]}', 
                                  ha="center", va="center", 
                                  color=color, fontsize=12, weight='bold')
            
            # 设置标签
            axes[1,1].set_xticks(range(len(display_labels)))
            axes[1,1].set_yticks(range(len(display_labels)))
            axes[1,1].set_xticklabels(display_labels)
            axes[1,1].set_yticklabels(display_labels)
            
            axes[1,1].set_title('Confusion Matrix', fontsize=14)
            axes[1,1].set_xlabel('Predicted Label', fontsize=12)
            axes[1,1].set_ylabel('True Label', fontsize=12)
            
            # 确保标签可见
            axes[1,1].tick_params(axis='x', labelsize=10)
            axes[1,1].tick_params(axis='y', labelsize=10)
            
            # 添加准确率信息
            accuracy = accuracy_score(y_true, y_pred)
            axes[1,1].text(0.02, 0.98, f'Accuracy: {accuracy:.4f}', 
                          transform=axes[1,1].transAxes, fontsize=11,
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.8))
        else:
            print("没有混淆矩阵数据，显示特征分布...")
            # 关键特征分布（以attention和meditation为例）
            colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red']
            for i, user in enumerate(self.users):
                if user in self.user_data:
                    user_data = self.user_data[user]
                    color = colors[i % len(colors)]
                    axes[1,1].scatter(user_data['attention'], user_data['meditation'], 
                                    label=f'{user} (n={len(user_data)})', alpha=0.6, color=color)
            axes[1,1].set_xlabel('Attention')
            axes[1,1].set_ylabel('Meditation')
            axes[1,1].set_title('User Feature Distribution (Attention vs Meditation)')
            axes[1,1].legend()
            axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plots:
            os.makedirs('data/plots', exist_ok=True)
            plt.savefig('data/plots/multi_user_data_analysis.png', dpi=300, bbox_inches='tight')
            print("图表已保存到: plots/multi_user_data_analysis.png")
        
        plt.show()
    
    def train_cross_user_model(self, test_user='csr'):
        """
        用其他用户的数据训练，在指定用户上测试
        """
        print(f"\n" + "=" * 60)
        print(f"跨用户模型训练 (测试用户: {test_user})")
        print("=" * 60)
        
        if test_user not in self.user_data:
            print(f"测试用户 {test_user} 没有数据")
            return None
        
        # 准备训练数据（除测试用户外的所有用户）
        train_data_list = []
        for user, data in self.user_data.items():
            if user != test_user:
                train_data_list.append(data)
        
        if not train_data_list:
            print("没有可用的训练数据")
            return None
        
        train_data = pd.concat(train_data_list, ignore_index=True)
        test_data = self.user_data[test_user]
        
        print(f"训练数据: {train_data.shape} (用户: {train_data['user'].unique()})")
        print(f"测试数据: {test_data.shape} (用户: {test_user})")
        
        # 提取特征和标签
        feature_cols = ['attention', 'meditation', 'rawValue', 'delta', 'theta', 
                       'lowAlpha', 'highAlpha', 'lowBeta', 'highBeta', 
                       'lowGamma', 'midGamma', 'poorSignal', 'blinkStrength']
        
        X_train = train_data[feature_cols].values
        y_train = train_data['mood'].values
        X_test = test_data[feature_cols].values
        y_test = test_data['mood'].values
        
        # 数据清理：处理NaN和inf值
        print("清理训练数据...")
        X_train = np.nan_to_num(X_train, nan=0, posinf=0, neginf=0)
        y_train = np.nan_to_num(y_train, nan=0, posinf=0, neginf=0)
        X_test = np.nan_to_num(X_test, nan=0, posinf=0, neginf=0)
        y_test = np.nan_to_num(y_test, nan=0, posinf=0, neginf=0)
        
        print(f"训练数据中的NaN: {np.isnan(X_train).sum()}, 标签中的NaN: {np.isnan(y_train).sum()}")
        print(f"测试数据中的NaN: {np.isnan(X_test).sum()}, 标签中的NaN: {np.isnan(y_test).sum()}")
        print(f"训练标签唯一值: {np.unique(y_train)}")
        print(f"测试标签唯一值: {np.unique(y_test)}")
        
        # 创建并训练KNN分类器
        classifier = KNNClassifier(n_neighbors=5, weights='distance')
        classifier.feature_names = feature_cols
        
        # 获取类别信息
        unique_labels = np.unique(np.concatenate([y_train, y_test]))
        classifier.class_names = [str(label) for label in unique_labels]
        
        # 预处理数据
        X_train_scaled = classifier.scaler.fit_transform(X_train)
        X_test_scaled = classifier.scaler.transform(X_test)
        
        # 训练模型
        classifier.knn.fit(X_train_scaled, y_train)
        classifier.is_trained = True
        
        # 评估模型
        train_score = classifier.knn.score(X_train_scaled, y_train)
        test_score = classifier.knn.score(X_test_scaled, y_test)
        
        print(f"训练准确率: {train_score:.4f}")
        print(f"跨用户测试准确率: {test_score:.4f}")
        
        # 详细分类报告
        from sklearn.metrics import classification_report, confusion_matrix
        y_pred = classifier.knn.predict(X_test_scaled)
        
        print(f"\n详细分类报告:")
        print(classification_report(y_test, y_pred, target_names=classifier.class_names))
        
        print(f"\n混淆矩阵:")
        print(confusion_matrix(y_test, y_pred))
        
        return classifier, {'train_acc': train_score, 'test_acc': test_score}
    
    def plot_confusion_matrix(self, y_true, y_pred, save_path=None):
        """
        绘制混淆矩阵
        
        参数:
            y_true: 真实标签
            y_pred: 预测标签
            save_path: 保存路径，如果为None则不保存
        """
        # 设置matplotlib字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 计算混淆矩阵
        from sklearn.metrics import confusion_matrix, accuracy_score
        cm = confusion_matrix(y_true, y_pred)
        
        # 情绪标签映射
        mood_labels = {
            0: 'Happy',
            1: 'Sad', 
            2: 'Angry',
            3: 'Peaceful'
        }
        
        # 获取实际出现的类别
        unique_labels = sorted(np.unique(np.concatenate([y_true, y_pred])))
        display_labels = [mood_labels.get(label, f'Unknown({label})') for label in unique_labels]
        
        # 创建图形
        plt.figure(figsize=(10, 8))
        
        # 绘制热力图
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=display_labels, yticklabels=display_labels,
                   cbar_kws={'label': 'Sample Count'},
                   square=True)
        
        plt.title('Confusion Matrix', fontsize=16, pad=20)
        plt.xlabel('Predicted Label', fontsize=14)
        plt.ylabel('True Label', fontsize=14)
        
        # 添加准确率信息
        accuracy = accuracy_score(y_true, y_pred)
        plt.figtext(0.02, 0.02, f'Overall Accuracy: {accuracy:.4f}', fontsize=12, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
        
        # 旋转x轴标签以避免重叠
        plt.xticks(rotation=30, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"混淆矩阵已保存到: {save_path}")
        
        plt.show()
        
        return cm

    def train_combined_model(self):
        """
        使用所有用户的数据训练
        """
        print(f"\n" + "=" * 60)
        print("组合用户模型训练")
        print("=" * 60)
        
        # 提取特征和标签
        feature_cols = ['attention', 'meditation', 'rawValue', 'delta', 'theta', 
                       'lowAlpha', 'highAlpha', 'lowBeta', 'highBeta', 
                       'lowGamma', 'midGamma', 'poorSignal', 'blinkStrength']
        
        X = self.combined_data[feature_cols].values
        y = self.combined_data['mood'].values
        users = self.combined_data['user'].values
        
        print(f"总数据: {X.shape}")
        print(f"用户分布: {pd.Series(users).value_counts().to_dict()}")
        print(f"情绪分布: {pd.Series(y).value_counts().to_dict()}")
        
        # 创建KNN分类器
        classifier = KNNClassifier(n_neighbors=5, weights='distance')
        
        # 使用交叉验证评估模型
        from sklearn.model_selection import cross_val_score, StratifiedKFold
        
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(classifier.knn, X, y, cv=cv, scoring='accuracy')
        
        print(f"5折交叉验证准确率: {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")
        print(f"各折准确率: {scores}")
        
        # 训练最终模型
        results = classifier.train(X, y, test_size=0.2, use_grid_search=True)
        
        # 数据可视化分析（包含混淆矩阵）
        confusion_data = None
        if 'y_test' in results and 'y_test_pred' in results:
            confusion_data = (results['y_test'], results['y_test_pred'])
        
        self.visualize_user_data(save_plots=True, confusion_matrix_data=confusion_data)
        
        return classifier, results
    
    def train_user_specific_models(self):
        """
        为每个用户训练专用模型
        """
        print(f"\n" + "=" * 60)
        print("用户专用模型训练")
        print("=" * 60)
        
        user_models = {}
        
        for user, data in self.user_data.items():
            print(f"\n训练用户 {user} 的专用模型:")
            print(f"数据量: {data.shape}")
            
            if len(data) < 50:  # 数据量太少
                print(f"用户 {user} 数据量太少，跳过训练")
                continue
            
            # 提取特征和标签
            feature_cols = ['attention', 'meditation', 'rawValue', 'delta', 'theta', 
                           'lowAlpha', 'highAlpha', 'lowBeta', 'highBeta', 
                           'lowGamma', 'midGamma', 'poorSignal', 'blinkStrength']
            
            X = data[feature_cols].values
            y = data['mood'].values
            
            # 检查是否有多个类别
            unique_classes = np.unique(y)
            if len(unique_classes) < 2:
                print(f"用户 {user} 只有一个情绪类别 {unique_classes}，跳过训练")
                continue
            
            # 创建并训练分类器
            classifier = KNNClassifier(n_neighbors=min(3, len(data)//5), weights='distance')
            
            try:
                results = classifier.train(X, y, test_size=0.3, use_grid_search=False)
                user_models[user] = {'classifier': classifier, 'results': results}
                
                print(f"用户 {user} 模型训练完成:")
                print(f"  训练准确率: {results['train_accuracy']:.4f}")
                print(f"  验证准确率: {results['val_accuracy']:.4f}")
                
            except Exception as e:
                print(f"用户 {user} 模型训练失败: {e}")
                continue
        
        return user_models

    def predict_mood(self,model_path = 'data/models/multi_user_combined_knn_model.pkl'):
        mindwave_reader = self.mindwave_reader
        
        # 检查mindwave_reader是否存在
        if not mindwave_reader:
            return
            
        # 只在第一次调用时创建和加载分类器
        if self.knn_classifier is None:
            self.knn_classifier = KNNClassifier()
            try:
                self.knn_classifier.load_model(model_path)
                print("KNN模型加载完成,开始情绪预测...")
            except Exception as e:
                print(f"加载KNN模型失败: {e}")
                return
        
        try:
            data = mindwave_reader.current_data
            if data['poorSignal'] == 0:
                # 将字典转换为单行DataFrame，使用index=[0]来处理标量值
                data = pd.DataFrame([data])
                # current_data没有timestamp列，只需要去掉最后的mood列
                data = data.iloc[:,:-1]
                predict_mood = self.knn_classifier.predict(data)[0]
                # 确保mood是Python原生int类型，避免JSON序列化错误
                predict_mood = int(predict_mood)
                mindwave_reader.set_mood(predict_mood)
        except Exception as e:
            print(f"情绪预测过程中出错: {e}")
            import traceback
            traceback.print_exc()

def main():
    print("多用户KNN EEG情绪分类器训练示例")
    print("=" * 60)
    
    # 创建多用户分类器
    multi_classifier = KNN_Runner()
    
    try:
        # 1. 加载所有用户数据
        multi_classifier.load_all_users_data()
        
        # 2. 数据可视化分析
        multi_classifier.visualize_user_data(save_plots=True)
        
        # 3. 跨用户模型训练（用其他用户数据训练，在csr用户上测试）
        # cross_user_model, cross_results = multi_classifier.train_cross_user_model(test_user='csr')
        
        # 4. 组合模型训练（使用所有用户数据）
        combined_model, combined_results = multi_classifier.train_combined_model()
        
        # 5. 用户专用模型训练
        # user_models = multi_classifier.train_user_specific_models()
        
        # 6. 保存最佳模型
        print(f"\n" + "=" * 60)
        print("保存训练结果")
        print("=" * 60)
        
        # 保存组合模型
        if combined_model:
            os.makedirs('data/models', exist_ok=True)
            combined_model.save_model('data/models/multi_user_combined_knn_model.pkl')
            print("组合模型已保存到: data/smodels/multi_user_combined_knn_model.pkl")
        
        # # 保存跨用户模型
        # if cross_user_model:
        #     cross_user_model.save_model('models/cross_user_knn_model.pkl')
        #     print("跨用户模型已保存到: models/cross_user_knn_model.pkl")
        
        # # 保存用户专用模型
        # for user, model_info in user_models.items():
        #     model_path = f'models/user_{user}_knn_model.pkl'
        #     model_info['classifier'].save_model(model_path)
        #     print(f"用户 {user} 专用模型已保存到: {model_path}")
        
        # 7. 训练结果总结
        print(f"\n" + "=" * 60)
        print("训练结果总结")
        print("=" * 60)
        
        if combined_results:
            print(f"组合模型验证准确率: {combined_results['val_accuracy']:.4f}")
        
        # if cross_results:
        #     print(f"跨用户模型测试准确率: {cross_results['test_acc']:.4f}")
        
        # print(f"用户专用模型数量: {len(user_models)}")
        # for user, model_info in user_models.items():
        #     print(f"  {user}: {model_info['results']['val_accuracy']:.4f}")
        
    except Exception as e:
        print(f"训练过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 