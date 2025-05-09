import os
import pretty_midi
import json

# 定義提取 MIDI 特徵的函數
def extract_features_from_midi(midi_path):
    pm = pretty_midi.PrettyMIDI(midi_path)
    
    # 收集音符
    notes = [note for instr in pm.instruments for note in instr.notes]
    if not notes:
        return None
    
    # 提取 pitch_class, octave, duration, position
    pitches = [note.pitch for note in notes]
    durations = [note.end - note.start for note in notes]
    positions = [note.start for note in notes]

    # pitch_class 和 octave 的處理
    pitch_classes = [pitch % 12 for pitch in pitches]
    octaves = [pitch // 12 for pitch in pitches]

    features = {
        "min_pitch": min(pitches),
        "max_pitch": max(pitches),
        "avg_pitch": sum(pitches) / len(pitches),
        "avg_duration": sum(durations) / len(durations),
        "avg_position": sum(positions) / len(positions),
        "note_density": len(notes) / pm.get_end_time(),
        "pitch_classes": pitch_classes,
        "octaves": octaves
    }
    
    return features

# 定義一個函數來處理資料夾中的所有 MIDI 文件
def process_all_tracks(base_dir, output_dir):
    # 創建輸出資料夾（如果不存在）
    os.makedirs(output_dir, exist_ok=True)
    
    # 遍歷每個 Track 資料夾
    for track_folder in os.listdir(base_dir):
        track_path = os.path.join(base_dir, track_folder, "MIDI")
        
        if os.path.isdir(track_path):  # 確保是資料夾
            track_id = track_folder.split("Track")[1]
            track_output_dir = os.path.join(output_dir, f"Track{track_id}_features")
            os.makedirs(track_output_dir, exist_ok=True)
            
            # 遍歷該 Track 資料夾中的所有 MIDI 文件（假設文件名以 .mid 結尾）
            for midi_file in os.listdir(track_path):
                if midi_file.endswith(".mid"):
                    midi_path = os.path.join(track_path, midi_file)
                    
                    # 提取特徵
                    features = extract_features_from_midi(midi_path)
                    if features:
                        # 將結果保存為 JSON 格式
                        midi_filename = midi_file.replace(".mid", ".json")
                        features_path = os.path.join(track_output_dir, midi_filename)
                        with open(features_path, 'w') as f:
                            json.dump(features, f, indent=4)
                        print(f"Processed {midi_file} and saved features to {features_path}")

# 設定根目錄和輸出目錄
base_directory = './babyslakh_16k/'
output_directory = './features_json/'

# 開始處理所有 Track 資料夾
process_all_tracks(base_directory, output_directory)
