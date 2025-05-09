import os
import json
import numpy as np
import matplotlib.pyplot as plt

# 根資料夾設定
features_root = "./features_json"  # 用於樂器分類
converted_root = "./converted_json"  # 用於音符分析
output_root = "./output"
os.makedirs(output_root, exist_ok=True)

# 樂器分類規則
def classify_brass_instrument(features):
    avg_pitch = features.get("avg_pitch", 0)
    if avg_pitch >= 72:
        return "trumpet"
    elif avg_pitch >= 65:
        return "french_horn"
    elif avg_pitch >= 60:
        return "euphonium"
    elif avg_pitch >= 55:
        return "trombone"
    else:
        return "tuba"

# 換氣點適合度分析
def analyze_breathing_suitability(notes, output_path):
    positions = []
    suitability_scores = []
    max_pause = 0

    for i in range(1, len(notes)):
        pause_duration = notes[i]["position"] - notes[i - 1]["position"] - notes[i - 1]["duration"]
        pause_duration = max(0, pause_duration)
        positions.append(notes[i]["position"])
        suitability_scores.append(pause_duration)
        max_pause = max(max_pause, pause_duration)

    if max_pause > 0:
        suitability_scores = np.array(suitability_scores) / max_pause
    else:
        suitability_scores = np.zeros_like(suitability_scores)

    plt.figure(figsize=(10, 5))
    plt.plot(positions, suitability_scores)
    plt.title("Breathing Suitability Analysis")
    plt.xlabel("Position")
    plt.ylabel("Suitability Score")
    plt.savefig(output_path)
    plt.close()

# 技術難度分析
def analyze_technical_difficulty(notes, output_path):
    positions = []
    difficulty_scores = []
    max_pitch_change = 0
    max_density = 0

    for i in range(1, len(notes)):
        pitch1 = notes[i - 1]["octave"] * 12 + notes[i - 1]["pitch_class"]
        pitch2 = notes[i]["octave"] * 12 + notes[i]["pitch_class"]
        pitch_change = abs(pitch2 - pitch1)
        note_density = 1 / notes[i]["duration"] if notes[i]["duration"] > 0 else 0
        positions.append(notes[i]["position"])
        difficulty_scores.append(pitch_change + note_density)
        max_pitch_change = max(max_pitch_change, pitch_change)
        max_density = max(max_density, note_density)

    if max_pitch_change + max_density > 0:
        difficulty_scores = np.array(difficulty_scores) / (max_pitch_change + max_density)
    else:
        difficulty_scores = np.zeros_like(difficulty_scores)

    plt.figure(figsize=(10, 5))
    plt.plot(positions, difficulty_scores)
    plt.title("Technical Difficulty Analysis")
    plt.xlabel("Position")
    plt.ylabel("Difficulty Score")
    plt.savefig(output_path)
    plt.close()

# 處理每一個 track 資料夾
for track_folder in os.listdir(features_root):  # 從 features_root 讀取 Track 資料夾
    track_path = os.path.join(features_root, track_folder)
    if not os.path.isdir(track_path) or not track_folder.startswith("Track"):
        continue

    print(f"\n🔍 處理中: {track_folder}")

    # 載入 metadata
    metadata_path = os.path.join(track_path, "metadata.json")
    if not os.path.exists(metadata_path):
        print(f"[警告] 找不到 metadata.json，略過 {track_folder}")
        continue

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    result_metadata = {
        "UUID": metadata.get("UUID", ""),
        "stems": {}
    }

    # 處理每個 stem S00～S20
    for i in range(21):
        stem_id = f"S{i:02d}"
        json_path = os.path.join(track_path, f"{stem_id}.json")

        if not os.path.exists(json_path):
            print(f"[跳過] 找不到 {stem_id}.json，略過")
            continue

        if stem_id not in metadata.get("stems", {}):
            print(f"[跳過] metadata 不包含 {stem_id}，略過")
            continue

        stem_info = metadata["stems"][stem_id]
        is_drum = stem_info.get("is_drum", False)
        inst_class = stem_info.get("inst_class", "")

        if is_drum:
            assigned_instrument = "Drums"
        else:
            with open(json_path, "r") as f:
                features = json.load(f)
            assigned_instrument = classify_brass_instrument(features)

            # 載入 notes 資料 (從 converted_json 讀取)
            converted_track_path = os.path.join(converted_root, track_folder.replace("_features", ""))  # 構建 converted_json 中的對應路徑
            notes_path = os.path.join(converted_track_path, f"{stem_id}.json")
            try:
                with open(notes_path, "r") as nf:
                    notes_data = json.load(nf)[0]  # 讀取音符資料
            except FileNotFoundError:
                print(f"[警告] 找不到 {notes_path}，略過音符分析")
                continue  # 如果找不到檔案，跳過分析

            # 分析並儲存圖表
            output_file_path = os.path.join(output_root, track_folder, f"{stem_id}_breathing.png")
            analyze_breathing_suitability(notes_data, output_file_path)

            output_file_path = os.path.join(output_root, track_folder, f"{stem_id}_difficulty.png")
            analyze_technical_difficulty(notes_data, output_file_path)

        result_metadata["stems"][stem_id] = {
            "original_inst_class": inst_class,
            "assigned_instrument": assigned_instrument
        }

    # 輸出到對應的資料夾
    track_output_dir = os.path.join(output_root, track_folder)
    os.makedirs(track_output_dir, exist_ok=True)
    output_metadata_path = os.path.join(track_output_dir, "metadata.json")
    with open(output_metadata_path, "w") as f:
        json.dump(result_metadata, f, indent=4)

    print(f"✅ 已儲存至 {output_metadata_path}")

print("\n🎉 所有 track 資料夾處理完成！")