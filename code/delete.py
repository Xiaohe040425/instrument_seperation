import os

def remove_all_src_json(base_dir):
    # 遍歷所有 Track000xx 資料夾
    for track_folder in os.listdir(base_dir):
        track_path = os.path.join(base_dir, track_folder)
        
        if os.path.isdir(track_path):
            all_src_json = os.path.join(track_path, 'all_src.json')
            
            # 檢查 all_src.json 檔案是否存在
            if os.path.isfile(all_src_json):
                print(f"Deleting {all_src_json}...")
                os.remove(all_src_json)  # 刪除 all_src.json 檔案
                print(f"Deleted {all_src_json}")
            else:
                print(f"{all_src_json} does not exist.")
    
# 設定根目錄
base_directory = './features_json/'

# 執行刪除操作
remove_all_src_json(base_directory)
