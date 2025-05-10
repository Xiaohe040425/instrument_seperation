import os
import json
import numpy as np


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


def analyze_and_aggregate(converted_root, output_root):
    """
    Analyzes all MIDI files and aggregates breathing suitability and
    technical difficulty data.

    Args:
        converted_root (str): Root path to the converted JSON data.
        output_root (str): Root path for output files.
    """

    all_breathing_scores = []
    all_difficulty_scores = []

    for track_folder in os.listdir(converted_root):
        converted_track_folder_path = os.path.join(converted_root, track_folder)
        if os.path.isdir(converted_track_folder_path) and track_folder.startswith(
            "Track"
        ):
            for filename in os.listdir(converted_track_folder_path):
                if filename.startswith("S") and filename.endswith(".json"):
                    json_path = os.path.join(converted_track_folder_path, filename)
                    try:
                        with open(json_path, "r") as f:
                            notes_data = json.load(f)
                            if (
                                not isinstance(notes_data, list) or not notes_data
                            ):  # Check if notes_data is a list and not empty
                                print(
                                    f"[警告] {json_path} does not contain valid note data, skipping"
                                )
                                continue
                            notes_data = notes_data[0]
                    except FileNotFoundError:
                        print(f"[警告] 找不到 {json_path}，略過")
                        continue
                    except json.JSONDecodeError:
                        print(f"[警告] {json_path} is not a valid JSON file, skipping")
                        continue

                    _, breathing_scores = calculate_breathing_suitability(notes_data)
                    _, difficulty_scores = calculate_technical_difficulty(notes_data)

                    all_breathing_scores.extend(breathing_scores)
                    all_difficulty_scores.extend(difficulty_scores)

    # Calculate statistics for breathing scores, ignoring values less than 0.01
    valid_breathing_scores = [
        score for score in all_breathing_scores if score >= 0.01
    ]
    avg_breathing = (
        np.mean(valid_breathing_scores) if valid_breathing_scores else 0
    )  # Only calculate if there are valid scores
    sorted_breathing_scores = sorted(valid_breathing_scores)
    q1_breathing = (
        np.mean(
            sorted_breathing_scores[
                int(len(sorted_breathing_scores) * 0.2) : int(
                    len(sorted_breathing_scores) * 0.3
                )
            ]
        )
        if sorted_breathing_scores
        else 0
    )
    q3_breathing = (
        np.mean(
            sorted_breathing_scores[
                int(len(sorted_breathing_scores) * 0.7) : int(
                    len(sorted_breathing_scores) * 0.8
                )
            ]
        )
        if sorted_breathing_scores
        else 0
    )

    # Calculate statistics for difficulty scores (no change needed here)
    avg_difficulty = np.mean(all_difficulty_scores) if all_difficulty_scores else 0
    sorted_difficulty_scores = sorted(all_difficulty_scores)
    q1_difficulty = (
        np.mean(
            sorted_difficulty_scores[
                int(len(sorted_difficulty_scores) * 0.2) : int(
                    len(sorted_difficulty_scores) * 0.3
                )
            ]
        )
        if sorted_difficulty_scores
        else 0
    )
    q3_difficulty = (
        np.mean(
            sorted_difficulty_scores[
                int(len(sorted_difficulty_scores) * 0.7) : int(
                    len(sorted_difficulty_scores) * 0.8
                )
            ]
        )
        if sorted_difficulty_scores
        else 0
    )

    # Save statistics to JSON files
    with open(os.path.join(output_root, "avg_breath.json"), "w") as f:
        json.dump(
            {
                "average": avg_breathing,
                "25th_percentile": q1_breathing,
                "75th_percentile": q3_breathing,
            },
            f,
            indent=4,
        )

    with open(os.path.join(output_root, "avg_difficult.json"), "w") as f:
        json.dump(
            {
                "average": avg_difficulty,
                "25th_percentile": q1_difficulty,
                "75th_percentile": q3_difficulty,
            },
            f,
            indent=4,
        )


if __name__ == "__main__":
    converted_root = "./converted_json"  # 修改為你的 converted_json 資料夾路徑
    output_root = "./output"  # 輸出資料夾的根路徑
    analyze_and_aggregate(converted_root, output_root)
    print("🎉 統計資料彙總完成！")