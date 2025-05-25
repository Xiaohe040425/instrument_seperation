import os
import json
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler # 導入 StandardScaler 用於標準化
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.preprocessing.sequence import pad_sequences

# --- 配置參數 (與 train.py 中的 CONVERTED_ROOT 和 OUTPUT_ROOT 保持一致) ---
# 現在指向 converted_json，因為這裡面才是原始音符序列
RAW_NOTES_JSON_ROOT = "./converted_json" 
OUTPUT_ROOT = "./output" # baseline_rule.py 輸出 metadata.json 的路徑

# 模型輸入的序列長度和特徵維度
MAX_SEQUENCE_LENGTH = 500 # 根據你的數據調整
# FEATURE_DIM 為每個音符的特徵數量：pitch_midi, duration, position, relative_position
FEATURE_DIM = 4 

def load_and_preprocess_data(raw_notes_json_root, output_root, max_seq_length=MAX_SEQUENCE_LENGTH):
    """
    載入樂器分類數據並進行預處理。
    
    Args:
        raw_notes_json_root (str): 包含原始音符 SXX.json 檔案的根目錄 (例如 "./converted_json")。
        output_root (str): 包含 metadata.json 檔案的根目錄 (例如 "./output")。
        max_seq_length (int): 每個序列的最大長度，不足的會填充，超過的會截斷。
        
    Returns:
        tuple: (X_train, X_val, X_test, y_train, y_val, y_test, label_encoder, num_classes)
               如果沒有找到有效數據，則返回 None。
    """
    
    print(f"--- 開始載入數據 ---")
    print(f"從 metadata.json 載入標籤：{output_root}")
    print(f"從原始音符 JSON 載入特徵：{raw_notes_json_root}")

    all_sequences = []
    all_labels = []
    
    # 步驟 1: 從 output/TrackXXXXX/metadata.json 載入 ground truth 標籤
    ground_truth_metadata = {}
    
    for track_folder_output in os.listdir(output_root): # 這裡的 folder name 是 TrackXXXXX
        track_path = os.path.join(output_root, track_folder_output)
        if not os.path.isdir(track_path) or not track_folder_output.startswith("Track"):
            continue

        metadata_path = os.path.join(track_path, "metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    data = json.load(f)
                    for stem_id, stem_info in data.get("stems", {}).items():
                        assigned_instrument_value = stem_info.get("assigned_instrument", "unknown_instrument")
                        ground_truth_metadata[f"{track_folder_output}/{stem_id}"] = str(assigned_instrument_value)
            except json.JSONDecodeError:
                print(f"[警告] 無法解析 {metadata_path}，跳過")
        else:
            print(f"[警告] {metadata_path} 不存在，跳過其分類資訊")

    if not ground_truth_metadata:
        print("沒有找到任何有效數據序列來訓練模型。請檢查路徑和資料格式。")
        return None, None, None, None, None, None, None, None

    # 步驟 2: 遍歷 ground_truth_metadata，載入對應的原始音符 SXX.json 檔案並提取特徵
    for track_stem_key, assigned_instrument in ground_truth_metadata.items():
        if assigned_instrument == "unknown_instrument":
            print(f"[跳過數據] {track_stem_key} 的樂器被分配為 'unknown_instrument'")
            continue
        # 如果你選擇在 data_loader 中過濾 Drums, 可以在這裡加條件
        # if assigned_instrument == "Drums":
        #    print(f"[跳過數據] {track_stem_key} 的樂器是 'Drums'")
        #    continue

        track_folder_name_bare = track_stem_key.split('/')[0] # 例如 "Track00001"
        stem_id = track_stem_key.split('/')[1] # 例如 "S00"

        # 構建原始音符 SXX.json 的完整路徑
        # 這裡假設 converted_json 下的資料夾也是 TrackXXXXX_features 格式
        # 但你給的 S00.json 範例路徑沒有提到 TrackXXXXX_features，
        # 如果 converted_json 下的資料夾是直接 TrackXXXXX，則需要調整這裡
        # 我會假設 converted_json 裡也是 TrackXXXXX_features 的結構
        actual_raw_notes_track_folder = None
        for f_name in os.listdir(raw_notes_json_root):
            if os.path.isdir(os.path.join(raw_notes_json_root, f_name)) and f_name.startswith(track_folder_name_bare):
                actual_raw_notes_track_folder = f_name
                break
        
        if actual_raw_notes_track_folder is None:
            print(f"[警告] 在 {raw_notes_json_root} 中找不到與 {track_folder_name_bare} 匹配的原始音符資料夾，跳過此數據點。")
            continue

        # 修正後的路徑，讀取 converted_json 中的 SXX.json
        current_sxx_json_path = os.path.join(raw_notes_json_root, actual_raw_notes_track_folder, f"{stem_id}.json")


        notes_data = []
        try:
            with open(current_sxx_json_path, "r") as f:
                raw_json_content = json.load(f)
                
            # 根據你提供的 converted_json 範例 S00.json，它是一個包含一個列表的列表
            if isinstance(raw_json_content, list) and raw_json_content and \
               isinstance(raw_json_content[0], list) and raw_json_content[0]:
                notes_data = raw_json_content[0] # 獲取實際的音符列表
            else:
                notes_data = [] # 如果格式不對，視為空音符數據

        except (FileNotFoundError, json.JSONDecodeError):
            print(f"[警告] 無法讀取或解析原始音符 SXX.json 檔案 {current_sxx_json_path}，跳過此數據點")
            continue

        if not notes_data:
            print(f"[警告] {current_sxx_json_path} 中沒有有效音符數據，跳過此數據點。")
            continue
        
        # --- 特徵工程：從每個音符中提取更豐富的特徵 ---
        sequence_features = []
        
        # 為了計算 relative_position，我們需要找到最小的 position
        # 注意：如果 notes_data 是空列表，min() 會報錯，所以需要先判斷
        min_position = 0
        if notes_data:
            # 找到所有音符的 position 值
            positions = [note.get("position", 0) for note in notes_data if "position" in note]
            if positions: # 確保 positions 列表不為空
                min_position = min(positions)

        for note in notes_data:
            # 確保所需的鍵存在且是數值
            if isinstance(note, dict) and all(k in note for k in ["pitch_class", "octave", "duration", "position"]):
                try:
                    pitch_class = float(note["pitch_class"])
                    octave = float(note["octave"])
                    duration = float(note["duration"])
                    position = float(note["position"])

                    # 1. pitch_midi: 將 pitch_class 和 octave 轉換為 MIDI 音高 (0-127)
                    pitch_midi = pitch_class + octave * 12

                    # 2. relative_position: 音符相對於序列起始的相對位置
                    # 避免除以零，如果 min_position 已經是 0 或者沒有音符
                    relative_position = position - min_position
                    
                    current_note_features = [
                        pitch_midi,
                        duration,
                        position, # 原始 position 依然保留，因為它代表絕對時間
                        relative_position
                    ]
                    sequence_features.append(current_note_features)
                except (TypeError, ValueError) as e:
                    print(f"[警告] {current_sxx_json_path} 中的音符特徵轉換失敗 ({e})，跳過此音符。")
            else:
                print(f"[警告] {current_sxx_json_path} 中的音符數據格式不完整或不正確，跳過此音符。")

        if not sequence_features:
            print(f"[警告] {current_sxx_json_path} 處理後沒有有效的序列特徵，跳過此數據點。")
            continue

        # 填充或截斷序列以達到 MAX_SEQUENCE_LENGTH
        padded_sequence = pad_sequences(
            [sequence_features], 
            maxlen=max_seq_length, 
            dtype='float32', 
            padding='post', # 在序列後面填充
            truncating='post', # 從序列後面截斷
            value=0.0 # 填充值
        )[0] # pad_sequences 返回一個批次，所以取第一個元素

        all_sequences.append(padded_sequence)
        all_labels.append(assigned_instrument)

    if not all_sequences:
        print("載入的數據序列為空。可能所有數據都被過濾或沒有有效特徵。")
        return None, None, None, None, None, None, None, None

    # 轉換為 numpy 數組
    X = np.array(all_sequences)
    y = np.array(all_labels)

    print(f"總共載入 {len(all_sequences)} 個有效數據序列。")

    # 步驟 3: 特徵標準化/歸一化 (在數據劃分之前進行，因為Scaler需要fit在訓練數據上)
    original_shape = X.shape
    X_reshaped = X.reshape(-1, FEATURE_DIM) # (總音符數, FEATURE_DIM)

    # 排除填充值 (0.0) 的影響，只對真實數據進行 fit
    # 這裡假設填充值 0.0 不在真實數據的有效範圍內，或者其標準化後仍然是 0
    # 更穩健的做法是只在非零元素上fit scaler
    # 由於 pad_sequences 的 value=0.0 且數據是浮點數，這樣直接 fit_transform 應該是沒問題的
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_reshaped)

    # 再將數據 reshape 回原來的序列形狀
    X_normalized = X_scaled.reshape(original_shape)
    
    print("特徵已完成標準化。")

    # 步驟 4: 標籤編碼
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(y)
    num_classes = len(label_encoder.classes_)
    print(f"已識別 {num_classes} 個樂器類別: {list(label_encoder.classes_)}")

    # 步驟 5: 數據集劃分
    X_train, X_temp, y_train, y_temp = train_test_split(X_normalized, encoded_labels, test_size=0.3, random_state=42, stratify=encoded_labels)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)

    print(f"數據劃分完成: 訓練集 {len(X_train)}，驗證集 {len(X_val)}，測試集 {len(X_test)}")

    return X_train, X_val, X_test, y_train, y_val, y_test, label_encoder, num_classes

if __name__ == "__main__":
    X_train, X_val, X_test, y_train, y_val, y_test, label_encoder, num_classes = load_and_preprocess_data(RAW_NOTES_JSON_ROOT, OUTPUT_ROOT)

    if X_train is not None:
        print("\n數據載入和預處理成功！")
        print(f"訓練集形狀: X={X_train.shape}, y={y_train.shape}")
        print(f"驗證集形狀: X={X_val.shape}, y={y_val.shape}")
        print(f"測試集形狀: X={X_test.shape}, y={y_test.shape}")
        print(f"類別數量: {num_classes}")
        print(f"樂器標籤映射: {list(label_encoder.classes_)}")
        print(f"單個訓練樣本的形狀 (MaxSeqLen, FeatureDim): {X_train[0].shape}")
        print(f"單個訓練樣本的特徵範例 (前5個時間步): \n{X_train[0][:5]}")
    else:
        print("\n數據載入失敗。")