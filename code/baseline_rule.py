import os
import json
from collections import defaultdict

# 根資料夾設定
features_root = "./features_json"
output_root = "./output"
os.makedirs(output_root, exist_ok=True)

# 樂器分配
instrument_assignments = defaultdict(lambda: defaultdict(bool))  # 追蹤樂器和聲部是否已分配
available_parts = []  # 每個 Track 的可用聲部列表

# 樂器分類規則
def classify_brass_instrument(features):
    global instrument_assignments, available_parts

    avg_pitch = features.get("avg_pitch", 0)
    min_pitch = features.get("min_pitch", 0)
    max_pitch = features.get("max_pitch", 127)
    avg_duration = features.get("avg_duration", 0)
    note_density = features.get("note_density", 0)
    pitch_range = max_pitch - min_pitch

    # 規則優先級
    if avg_pitch > 70 and max_pitch > 80 and avg_duration < 0.5 and note_density > 1.5:
        instrument = "Trumpet"
    elif avg_pitch > 70 and max_pitch > 75 and pitch_range > 20:
        instrument = "Trumpet"
    elif 55 <= avg_pitch <= 70 and pitch_range > 25 and note_density < 1.5:
        instrument = "French Horn"
    elif avg_pitch < 55 and min_pitch < 50 and avg_duration > 0.6:
        instrument = "Tuba"
    elif avg_pitch < 60 and min_pitch < 55 and avg_duration > 0.5:
        instrument = "Tuba"
    # 備份規則
    elif avg_pitch > 70:
        instrument = "Trumpet"
    elif 55 <= avg_pitch <= 70:
        instrument = "French Horn"
    else:
        instrument = "Tuba"

    # 找到可用的聲部
    assigned_part = None
    for part in available_parts:
        if not instrument_assignments[instrument][part]:
            assigned_part = part
            break

    # 如果沒有可用的聲部，則分配第一個
    if assigned_part is None:
        assigned_part = available_parts[0]

    instrument_assignments[instrument][assigned_part] = True
    return instrument, assigned_part

# 處理每一個 track 資料夾
for track_folder in os.listdir(features_root):
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

    # 重置樂器分配和生成可用聲部列表
    instrument_assignments.clear()
    available_parts = list(range(1, 22))  # 假設最多 21 個聲部，根據你的需求調整

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
            instrument, assigned_part = classify_brass_instrument(features)
            assigned_instrument = instrument # 只取樂器名稱字串

        result_metadata["stems"][stem_id] = {
            "original_inst_class": inst_class,
            "assigned_instrument": assigned_instrument
        }

    # 輸出到對應的資料夾
    # 修改這兩行以移除 "_features" 後綴
    track_output_name = track_folder.replace("_features", "") # 移除 _features 後綴
    track_output_dir = os.path.join(output_root, track_output_name)
    os.makedirs(track_output_dir, exist_ok=True)
    output_metadata_path = os.path.join(track_output_dir, "metadata.json")
    with open(output_metadata_path, "w") as f:
        json.dump(result_metadata, f, indent=4)

    print(f"✅ 已儲存至 {output_metadata_path}")

print("\n🎉 所有 track 資料夾處理完成！")