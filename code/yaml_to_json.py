import yaml
import json

# 輸入與輸出檔案路徑
yaml_path = "./babyslakh_16k/track00020/metadata.yaml"
json_path = "./features_json/track00020_features/metadata.json"

# 讀取 YAML
with open(yaml_path, 'r') as f:
    data = yaml.safe_load(f)

# 寫入 JSON
with open(json_path, 'w') as f:
    json.dump(data, f, indent=2)

print("轉換完成：metadata.yaml → metadata.json")
