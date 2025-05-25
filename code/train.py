import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv1D, MaxPooling1D, Bidirectional, LSTM, Dense, Dropout, Flatten
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# 確保可以從父目錄導入 data_loader
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_loader import load_and_preprocess_data

# --- 超參數設定 ---
# 數據路徑 (確保與 data_loader.py 中的一致)
CONVERTED_ROOT = "./converted_json" # 原始音符 JSON 檔案的路徑
OUTPUT_ROOT = "./output" # baseline_rule.py 輸出 metadata.json 的路徑

# 模型超參數
MAX_SEQUENCE_LENGTH = 500 # 必須與 data_loader.py 中使用的一致
FEATURE_DIM = 4 # 每個音符的特徵數量 (pitch_class, octave, duration, position, breathing_score, difficulty_score)
EPOCHS = 200
BATCH_SIZE = 32
LEARNING_RATE = 0.001

# 模型保存路徑
MODEL_SAVE_PATH = "./models/instrument_classifier_bilstm_cnn.h5"
HISTORY_SAVE_PATH = "./models/training_history.png" # 保存訓練歷史圖

def build_bilstm_cnn_model(input_shape, num_classes):
    """
    構建一個 BiLSTM + CNN 模型用於樂器分類。
    """
    inputs = Input(shape=input_shape)

    # 第一層：1D 卷積層
    conv = Conv1D(filters=64, kernel_size=5, activation='relu', padding='same')(inputs)
    pool = MaxPooling1D(pool_size=2)(conv)
    drop1 = Dropout(0.3)(pool)

    # 第二層：另一個 1D 卷積層
    conv2 = Conv1D(filters=128, kernel_size=3, activation='relu', padding='same')(drop1)
    pool2 = MaxPooling1D(pool_size=2)(conv2)
    drop2 = Dropout(0.3)(pool2)

    # 雙向 LSTM 層
    bilstm = Bidirectional(LSTM(128, return_sequences=True))(drop2)
    bilstm_dropout = Dropout(0.4)(bilstm)
    
    # 再次使用雙向 LSTM 層，最後一個 Bidirectional 層設置 return_sequences=False
    bilstm2 = Bidirectional(LSTM(64))(bilstm_dropout)
    bilstm2_dropout = Dropout(0.4)(bilstm2)

    # Flatten 層，為全連接層做準備
    flatten = Flatten()(bilstm2_dropout)

    # 全連接層
    dense = Dense(128, activation='relu')(flatten)
    drop3 = Dropout(0.5)(dense)

    # 輸出層
    outputs = Dense(num_classes, activation='softmax')(drop3)

    model = Model(inputs=inputs, outputs=outputs)
    return model

def plot_training_history(history, save_path):
    """
    繪製訓練過程中的損失和準確率曲線。
    """
    plt.figure(figsize=(12, 6))

    # 繪製損失曲線
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Model Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)

    # 繪製準確率曲線
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Train Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Model Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(save_path)
    print(f"訓練歷史圖已保存至: {save_path}")
    plt.show()

if __name__ == "__main__":
    print("--- 載入和預處理數據 ---")
    X_train, X_val, X_test, y_train, y_val, y_test, label_encoder, num_classes = \
        load_and_preprocess_data(CONVERTED_ROOT, OUTPUT_ROOT, MAX_SEQUENCE_LENGTH)

    if X_train is None:
        print("數據載入失敗，無法進行模型訓練。")
    else:
        print(f"訓練集形狀: X={X_train.shape}, y={y_train.shape}")
        print(f"驗證集形狀: X={X_val.shape}, y={y_val.shape}")
        print(f"測試集形狀: X={X_test.shape}, y={y_test.shape}")
        print(f"類別數量: {num_classes}")
        print(f"樂器標籤映射: {list(label_encoder.classes_)}")

        # --- 構建模型 ---
        print("\n--- 構建 BiLSTM + CNN 模型 ---")
        input_shape = (MAX_SEQUENCE_LENGTH, FEATURE_DIM)
        model = build_bilstm_cnn_model(input_shape, num_classes)
        model.summary()

        # --- 編譯模型 ---
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
                      loss='sparse_categorical_crossentropy', # 因為 y 是整數標籤
                      metrics=['accuracy'])

        # --- 設定回調函數 ---
        # Early Stopping: 如果驗證損失在連續幾輪沒有改善，則停止訓練
        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

        # Model Checkpoint: 保存最佳模型
        os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True) # 確保模型保存目錄存在
        model_checkpoint = ModelCheckpoint(MODEL_SAVE_PATH,
                                           monitor='val_loss',
                                           save_best_only=True,
                                           verbose=1)

        # --- 訓練模型 ---
        print("\n--- 開始訓練模型 ---")
        history = model.fit(X_train, y_train,
                            epochs=EPOCHS,
                            batch_size=BATCH_SIZE,
                            validation_data=(X_val, y_val),
                            callbacks=[early_stopping, model_checkpoint],
                            verbose=1)

        print("\n--- 模型訓練完成 ---")

        # --- 繪製訓練歷史 ---
        plot_training_history(history, HISTORY_SAVE_PATH)

        # --- 評估模型 ---
        print("\n--- 評估測試集上的模型性能 ---")
        loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
        print(f"測試集損失: {loss:.4f}")
        print(f"測試集準確率: {accuracy:.4f}")

        # 獲取預測結果並打印分類報告
        y_pred_probs = model.predict(X_test)
        y_pred = np.argmax(y_pred_probs, axis=1)

        print("\n--- 分類報告 ---")
        print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

        # 繪製混淆矩陣
        print("\n--- 混淆矩陣 ---")
        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_)
        plt.title('Confusion Matrix')
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.show()