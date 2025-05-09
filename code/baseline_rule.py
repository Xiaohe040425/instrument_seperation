import os
import json

# 根資料夾設定
features_root = "./features_json"
output_root = "./output"
os.makedirs(output_root, exist_ok=True)

# 樂器分類規則（根據 avg_pitch）
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
