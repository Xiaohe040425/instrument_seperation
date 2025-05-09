import os
import pretty_midi
import json

INPUT_DIR = "./babyslakh_16k"
OUTPUT_DIR = "./converted_json"

def midi_to_json(midi_path):
    pm = pretty_midi.PrettyMIDI(midi_path)
    notes = []
    for instr in pm.instruments:
        if instr.is_drum:
            continue
        for note in instr.notes:
            notes.append({
                "pitch_class": note.pitch % 12,
                "octave": note.pitch // 12,
                "duration": round(note.end - note.start, 5),
                "position": round(note.start, 5)
            })
    notes.sort(key=lambda x: x["position"])
    return [notes] if notes else []

for track_folder in os.listdir(INPUT_DIR):
    track_path = os.path.join(INPUT_DIR, track_folder)
    midi_folder = os.path.join(track_path, "MIDI")

    if not os.path.isdir(midi_folder):
        continue

    output_folder = os.path.join(OUTPUT_DIR, track_folder)
    os.makedirs(output_folder, exist_ok=True)

    for midi_file in os.listdir(midi_folder):
        if not midi_file.endswith(".mid") and not midi_file.endswith(".midi"):
            continue

        midi_path = os.path.join(midi_folder, midi_file)
        json_filename = midi_file.replace(".mid", ".json").replace(".midi", ".json")
        json_path = os.path.join(output_folder, json_filename)

        try:
            phrases = midi_to_json(midi_path)
            with open(json_path, "w") as f:
                json.dump(phrases, f, indent=2)
            print(f"✓ 轉換成功: {track_folder}/{json_filename}")
        except Exception as e:
            print(f"✗ 轉換失敗: {midi_path}，錯誤：{e}")
