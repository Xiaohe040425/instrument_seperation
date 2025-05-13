import os
import json
import numpy as np
import matplotlib.pyplot as plt
import subprocess  # 用於執行外部 Python 腳本

# ANSI 顏色程式碼 (用於終端輸出)
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"


def calculate_breathing_suitability(notes):
    """Calculates the breathing suitability scores for a list of notes."""

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

    return positions, suitability_scores


def calculate_technical_difficulty(notes):
    """Calculates the technical difficulty scores for a list of notes."""

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

    return positions, difficulty_scores


def analyze_breathing_suitability(
    notes, output_path, avg_breathing, q1_breathing, q3_breathing
):
    """
    Analyzes the breathing suitability of a sequence of notes and plots
    the results with average and quartile lines.

    Args:
        notes (list): A list of note data.
        output_path (str): The path to save the generated plot.
        avg_breathing (float): Average breathing suitability score.
        q1_breathing (float): 25th percentile of breathing suitability scores.
        q3_breathing (float): 75th percentile of breathing suitability scores.
    """

    positions, suitability_scores = calculate_breathing_suitability(notes)

    plt.figure(figsize=(10, 5))
    plt.plot(positions, suitability_scores)
    plt.axhline(
        y=avg_breathing, color="red", linestyle="-", label=f"Avg: {avg_breathing:.2f}"
    )
    plt.axhline(
        y=q1_breathing, color="blue", linestyle="--", label=f"25th: {q1_breathing:.2f}"
    )
    plt.axhline(
        y=q3_breathing, color="green", linestyle="--", label=f"75th: {q3_breathing:.2f}"
    )
    plt.title("Breathing Suitability Analysis\n(Higher score = more suitable)")
    plt.xlabel("Position (seconds)")
    plt.ylabel("Suitability Score")
    plt.legend()  # 顯示圖例
    plt.savefig(output_path)
    plt.close()


def analyze_technical_difficulty(
    notes, output_path, avg_difficulty, q1_difficulty, q3_difficulty
):
    """
    Analyzes the technical difficulty of a sequence of notes and plots
    the results with average and quartile lines.

    Args:
        notes (list): A list of note data.
        output_path (str): The path to save the generated plot.
        avg_difficulty (float): Average technical difficulty score.
        q1_difficulty (float): 25th percentile of technical difficulty scores.
        q3_difficulty (float): 75th percentile of technical difficulty scores.
    """

    positions, difficulty_scores = calculate_technical_difficulty(notes)

    plt.figure(figsize=(10, 5))
    plt.plot(positions, difficulty_scores)
    plt.axhline(
        y=avg_difficulty, color="red", linestyle="-", label=f"Avg: {avg_difficulty:.2f}"
    )
    plt.axhline(
        y=q1_difficulty,
        color="blue",
        linestyle="--",
        label=f"25th: {q1_difficulty:.2f}",
    )
    plt.axhline(
        y=q3_difficulty,
        color="green",
        linestyle="--",
        label=f"75th: {q3_difficulty:.2f}",
    )
    plt.title("Technical Difficulty Analysis\n(Higher score = more difficult)")
    plt.xlabel("Position (seconds)")
    plt.ylabel("Difficulty Score")
    plt.legend()  # 顯示圖例
    plt.savefig(output_path)
    plt.close()


def process_track_folder(
    converted_track_folder_path,
    output_root,
    avg_breathing,
    q1_breathing,
    q3_breathing,
    avg_difficulty,
    q1_difficulty,
    q3_difficulty,
):
    """
    Processes all SXX.json files within a given track folder and returns
    a dictionary of analysis results keyed by filename.
    """
    track_folder_name = os.path.basename(converted_track_folder_path)
    output_folder_name = track_folder_name + "_features"
    output_folder_path = os.path.join(output_root, output_folder_name)
    os.makedirs(output_folder_path, exist_ok=True)

    analysis_results = {}

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
                    if not isinstance(notes_data, list) or not notes_data:
                        print(f"[警告] {json_path} does not contain valid note data, skipping")
                        continue
                    notes_data = notes_data[0]
            except FileNotFoundError:
                print(f"[警告] 找不到 {json_path}，略過")
                continue
            except json.JSONDecodeError:
                print(f"[警告] {json_path} is not a valid JSON file, skipping")
                continue

            # Calculate and store the mean values with the filename as key
            breathing_positions, breathing_scores = calculate_breathing_suitability(notes_data)
            avg_breathing_score = np.mean(breathing_scores) if len(breathing_scores) > 0 else 0

            difficulty_positions, difficulty_scores = calculate_technical_difficulty(notes_data)
            avg_difficulty_score = np.mean(difficulty_scores) if len(difficulty_scores) > 0 else 0

            analysis_results[filename] = {
                "breath": avg_breathing_score,
                "difficulty": avg_difficulty_score,
            }

            # Plot with global averages and quartiles
            analyze_breathing_suitability(
                notes_data,
                output_breathing_path,
                avg_breathing,
                q1_breathing,
                q3_breathing,
            )
            analyze_technical_difficulty(
                notes_data,
                output_difficulty_path,
                avg_difficulty,
                q1_difficulty,
                q3_difficulty,
            )

            print(f"✅ 已處理 {filename}")

    return analysis_results


if __name__ == "__main__":
    converted_root = "./converted_json"  # 修改為你的 converted_json 資料夾路徑
    output_root = "./output"  # 輸出資料夾的根路徑
    os.makedirs(output_root, exist_ok=True)

    # 執行 aggregate_analysis.py 進行資料彙總
    subprocess.run(["python", "./code/aggregate_analyze.py"], check=True)

    # Load aggregated statistics
    with open(os.path.join(output_root, "avg_breath.json"), "r") as f:
        avg_breath_data = json.load(f)

    with open(os.path.join(output_root, "avg_difficult.json"), "r") as f:
        avg_difficult_data = json.load(f)

    # Extract stats for easier use
    avg_breathing = avg_breath_data["average"]
    q1_breathing = avg_breath_data["25th_percentile"]
    q3_breathing = avg_breath_data["75th_percentile"]
    avg_difficulty = avg_difficult_data["average"]
    q1_difficulty = avg_difficult_data["25th_percentile"]
    q3_difficulty = avg_difficult_data["75th_percentile"]

    print("\n📊 所有 Track 的分析結果：")
    for track_folder in os.listdir(converted_root):
        converted_track_folder_path = os.path.join(converted_root, track_folder)
        if (
            os.path.isdir(converted_track_folder_path)
            and track_folder.startswith("Track")
        ):
            print(f"\n🎵 {track_folder}:")
            analysis_results = process_track_folder(
                converted_track_folder_path,
                output_root,
                avg_breathing,
                q1_breathing,
                q3_breathing,
                avg_difficulty,
                q1_difficulty,
                q3_difficulty,
            )

            for filename in os.listdir(converted_track_folder_path):
                if filename.startswith("S") and filename.endswith(".json"):
                    print(f"  - {filename}:")
                    if filename in analysis_results:
                        print(
                            f"    Breath: {analysis_results[filename]['breath']:.4f} "
                            f" (Avg: {RED}{avg_breathing:.4f}{RESET}, "
                            f"Q1: {BLUE}{q1_breathing:.4f}{RESET}, "
                            f"Q3: {GREEN}{q3_breathing:.4f}{RESET}) "
                        )
                        print(
                            f"    Diff: {analysis_results[filename]['difficulty']:.4f} "
                            f" (Avg: {RED}{avg_difficulty:.4f}{RESET}, "
                            f"Q1: {BLUE}{q1_difficulty:.4f}{RESET}, "
                            f"Q3: {GREEN}{q3_difficulty:.4f}{RESET}) "
                        )
                    else:
                        print(f"    (分析失敗或跳過)")

    print("\n🎉 分析完成！")