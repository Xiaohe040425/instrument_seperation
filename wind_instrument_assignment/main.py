"""
Wind Instrument Assignment System - Main Entry Point
Automatically outputs MIDI, WAV, and MP3 formats
"""

import sys
from pathlib import Path
from core.instrument_assignment import WindInstrumentAssigner
from core.audio_converter import AudioConverter


def main():
    print("🎺 Wind Instrument Assignment System v2.0")
    print("=" * 60)
    print("Auto-generates: MIDI + WAV + MP3")
    print()

    # 初始化分配器和音頻轉換器
    try:
        assigner = WindInstrumentAssigner()
        audio_converter = AudioConverter()
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

    # 設定檔案路徑
    base_path = Path(__file__).parent

    # 檢查是否有測試檔案
    test_midi = base_path / "examples" / "input_midi" / "test.mid"
    test_metadata = base_path / "examples" / "assignment_json" / "test_metadata.json"
    output_midi = base_path / "examples" / "output" / "converted.mid"
    output_wav = base_path / "examples" / "output" / "converted.wav"
    output_mp3 = base_path / "examples" / "output" / "converted.mp3"

    # 如果沒有測試檔案，提示用戶
    if not test_midi.exists():
        print("📁 No test MIDI file found.")
        print(f"   Please place a MIDI file at: {test_midi}")
        print("   Or specify a custom path:")

        custom_path = input("Enter MIDI file path (or press Enter to skip): ").strip()
        if custom_path:
            test_midi = Path(custom_path)
        else:
            print("ℹ️  Skipping test - no MIDI file provided")
            return True

    # 檢查檔案是否存在
    if not test_midi.exists():
        print(f"❌ MIDI file not found: {test_midi}")
        return False

    if not test_metadata.exists():
        print(f"❌ Metadata file not found: {test_metadata}")
        return False

    # 確保輸出目錄存在
    output_midi.parent.mkdir(parents=True, exist_ok=True)

    # 執行MIDI轉換
    print(f"🚀 Starting conversion...")
    print(f"   Input MIDI: {test_midi}")
    print(f"   Assignment: {test_metadata}")
    print()

    print("📝 Step 1: MIDI-to-MIDI conversion...")
    midi_success = assigner.process_assignment(
        str(test_midi), str(test_metadata), str(output_midi)
    )

    if not midi_success:
        print("❌ MIDI conversion failed!")
        return False

    print("✅ MIDI conversion completed!")

    # 自動進行所有音頻轉換
    print("\n🎵 Step 2: Converting to audio formats...")

    conversion_results = []

    # WAV轉換
    print("   🔄 Converting to WAV...")
    wav_success = audio_converter.midi_to_audio(
        str(output_midi), str(output_wav), "wav"
    )
    conversion_results.append(("WAV", wav_success, output_wav))

    # MP3轉換
    print("   🔄 Converting to MP3...")
    mp3_success = audio_converter.midi_to_audio(
        str(output_midi), str(output_mp3), "mp3"
    )
    conversion_results.append(("MP3", mp3_success, output_mp3))

    # 結果報告
    print("\n📊 Conversion Results:")
    print(f"   ✅ MIDI: {output_midi}")

    for format_name, success, file_path in conversion_results:
        if success:
            print(f"   ✅ {format_name}: {file_path}")
        else:
            print(f"   ❌ {format_name}: Failed")

    # 統計成功率
    successful_conversions = 1 + sum(
        1 for _, success, _ in conversion_results if success
    )  # +1 for MIDI
    total_conversions = 1 + len(conversion_results)

    print(
        f"\n🎉 Completed: {successful_conversions}/{total_conversions} formats successfully generated"
    )

    if successful_conversions == total_conversions:
        print("🎊 All formats generated successfully!")
        return True
    elif successful_conversions > 1:
        print("⚠️  Some formats failed, but MIDI conversion was successful")
        return True
    else:
        print("❌ Only MIDI conversion succeeded")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
