from eeg_music.train.knn_runner import KNN_Runner
from eeg_music.model.knn_classifier import KNNClassifier
from eeg_music.reader.MindwaveSerialReader import MindwaveSerialReader
import os
import pandas as pd
def train():
    print("多用户KNN EEG情绪分类器训练示例")
    print("=" * 60)
    
    # 创建多用户分类器
    multi_classifier = KNN_Runner()
    
    try:
        # 1. 加载所有用户数据
        multi_classifier.load_all_users_data()
                
        # 2. 组合模型训练（使用所有用户数据）
        combined_model, combined_results = multi_classifier.train_combined_model()
        
        print(f"\n" + "=" * 60)
        print("保存训练结果")
        print("=" * 60)
        
        # 3. 保存组合模型
        if combined_model:
            os.makedirs('data/models', exist_ok=True)
            combined_model.save_model('data/models/multi_user_combined_knn_model.pkl')
            print("组合模型已保存到: data/models/multi_user_combined_knn_model.pkl")
         
        # 4. 训练结果总结
        print(f"\n" + "=" * 60)
        print("训练结果总结")
        print("=" * 60)
        
        if combined_results:
            print(f"组合模型验证准确率: {combined_results['val_accuracy']:.4f}")   
    
    except Exception as e:
        print(f"训练过程中出错: {e}")
        import traceback
        traceback.print_exc()
        
def predict():
    print("多用户KNN EEG情绪分类器分类示例")
    print("=" * 60)
    mindwave_reader = MindwaveSerialReader(port='/dev/ttyACM0',baudrate=57600,timeout=1,mood='happy')
    # 创建多用户分类器
    knn_classifier = KNNClassifier()
    try:
        model_path = 'data/models/multi_user_combined_knn_model.pkl'
        knn_classifier.load_model(model_path)
        if mindwave_reader.connect():
            while True:
                data = mindwave_reader.current_data
                if data['poorSignal'] == 0:
                    # 将字典转换为单行DataFrame，使用index=[0]来处理标量值
                    data = pd.DataFrame([data])
                    # current_data没有timestamp列，只需要去掉最后的mood列
                    data = data.iloc[:,:-1]
                    predict_mood = knn_classifier.predict(data)[0]
                    mindwave_reader.set_mood(predict_mood)
                    print(f"当前情绪: {predict_mood}")
    except Exception as e:
        print(f"分类过程中出错: {e}")
        import traceback
        traceback.print_exc()
        

if __name__ == "__main__":
    predict() 