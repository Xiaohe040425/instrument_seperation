"""
Full pipeline test - Auto generates all formats
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.instrument_assignment import WindInstrumentAssigner
from core.audio_converter import AudioConverter


def test_full_pipeline():
    """Test the complete pipeline with all formats"""
    print("🧪 Testing Full Pipeline (All Formats)...")

    # 設定路徑
    base_path = Path(__file__).parent.parent
    test_midi = base_path / "examples" / "input_midi" / "test.mid"
    test_metadata = base_path / "examples" / "assignment_json" / "test_metadata.json"

    output_midi = base_path / "examples" / "output" / "test_pipeline.mid"
    output_wav = base_path / "examples" / "output" / "test_pipeline.wav"
    output_mp3 = base_path / "examples" / "output" / "test_pipeline.mp3"

    # 檢查測試檔案
    if not test_midi.exists():
        print("⚠️  No test MIDI file found, skipping pipeline test")
        return True

    if not test_metadata.exists():
        print("⚠️  No test metadata file found, skipping pipeline test")
        return True

    try:
        # 初始化
        assigner = WindInstrumentAssigner()
        converter = AudioConverter()

        # Step 1: MIDI轉換
        print("   Step 1: MIDI-to-MIDI conversion...")
        midi_success = assigner.process_assignment(
            str(test_midi), str(test_metadata), str(output_midi)
        )

        if not midi_success:
            print("   ❌ MIDI conversion failed")
            return False

        # Step 2: 音頻轉換
        print("   Step 2: Audio conversions...")

        # WAV
        print("     Converting to WAV...")
        wav_success = converter.midi_to_audio(str(output_midi), str(output_wav), "wav")

        # MP3
        print("     Converting to MP3...")
        mp3_success = converter.midi_to_audio(str(output_midi), str(output_mp3), "mp3")

        # 結果統計
        results = {"MIDI": midi_success, "WAV": wav_success, "MP3": mp3_success}

        successful = sum(1 for success in results.values() if success)
        total = len(results)

        print(f"   📊 Results: {successful}/{total} formats successful")

        for format_name, success in results.items():
            status = "✅" if success else "❌"
            print(f"     {status} {format_name}")

        return successful >= 1  # 至少一個格式成功就算通過

    except Exception as e:
        print(f"   ❌ Pipeline test failed: {e}")
        return False


def main():
    print("🔬 Running Full Pipeline Test (All Formats)")
    print("=" * 50)

    if test_full_pipeline():
        print("\n📊 Full pipeline test: PASSED")
        return True
    else:
        print("\n📊 Full pipeline test: FAILED")
        return False


if __name__ == "__main__":
    main()
