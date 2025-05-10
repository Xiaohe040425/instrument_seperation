import os
import json
import numpy as np
import matplotlib.pyplot as plt


def analyze_breathing_suitability(notes, output_path):
    """
    Analyzes the breathing suitability of a sequence of notes.

    Args:
        notes (list): A list of note data.
        output_path (str): The path to save the generated plot.
    """
    positions = []
    suitability_scores = []
    max_pause = 0

    for i in range(1, len(notes)):
        pause_duration = (
            notes[i]["position"] - notes[i - 1]["position"] - notes[i - 1]["duration"]
        )
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
    plt.title("Breathing Suitability Analysis\n(Higher score = more suitable)")  # 加入文字說明
    plt.xlabel("Position (seconds)")  # 加入單位
    plt.ylabel("Suitability Score")
    plt.savefig(output_path)
    plt.close()


def analyze_technical_difficulty(notes, output_path):
    """
    Analyzes the technical difficulty of a sequence of notes.

    Args:
        notes (list): A list of note data.
        output_path (str): The path to save the generated plot.
    """
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
        difficulty_scores = np.array(difficulty_scores) / (
            max_pitch_change + max_density
        )
    else:
        difficulty_scores = np.zeros_like(difficulty_scores)

    plt.figure(figsize=(10, 5))
    plt.plot(positions, difficulty_scores)
    plt.title("Technical Difficulty Analysis\n(Higher score = more difficult)")  # 加入文字說明
    plt.xlabel("Position (seconds)")  # 加入單位
    plt.ylabel("Difficulty Score")
    plt.savefig(output_path)
    plt.close()


def process_track_folder(converted_track_folder_path, output_root):
    """
    Processes all SXX.json files within a given track folder.

    Args:
        converted_track_folder_path (str): Path to the track folder in converted_json.
        output_root (str): Root path for output files.
    """
    track_folder_name = os.path.basename(converted_track_folder_path)
    output_folder_name = track_folder_name + "_features"
    output_folder_path = os.path.join(output_root, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)

    for filename in os.listdir(converted_track_folder_path):
        if filename.startswith("S") and filename.endswith(".json"):
            stem_id = filename.replace(".json", "")
            json_path = os.path.join(converted_track_folder_path, filename)
            output_breathing_path = os.path.join(
                output_folder_path, f"{stem_id}_breathing.png"
            )
            output_difficulty_path = os.path.join(
                output_folder_path, f"{stem_id}_difficulty.png"
            )

            try:
                with open(json_path, "r") as f:
                    notes_data = json.load(f)
                    if not isinstance(notes_data, list) or not notes_data:  # Check if notes_data is a list and not empty
                        print(f"[警告] {json_path} does not contain valid note data, skipping")
                        continue
                    notes_data = notes_data[0]
            except FileNotFoundError:
                print(f"[警告] 找不到 {json_path}，略過")
                continue
            except json.JSONDecodeError:
                print(f"[警告] {json_path} is not a valid JSON file, skipping")
                continue

            analyze_breathing_suitability(notes_data, output_breathing_path)
            analyze_technical_difficulty(notes_data, output_difficulty_path)
            print(f"✅ 已處理 {filename}")


if __name__ == "__main__":
    converted_root = "./converted_json"  # 修改為你的 converted_json 資料夾路徑
    output_root = "./output"  # 輸出資料夾的根路徑
    os.makedirs(output_root, exist_ok=True)

    for track_folder in os.listdir(converted_root):
        converted_track_folder_path = os.path.join(converted_root, track_folder)
        if (
            os.path.isdir(converted_track_folder_path)
            and track_folder.startswith("Track")
        ):
            print(f"\n🔍 處理中: {track_folder}")
            process_track_folder(converted_track_folder_path, output_root)

    print("\n🎉 所有 Track 資料夾處理完成！")