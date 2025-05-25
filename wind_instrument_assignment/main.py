"""
Wind Instrument Assignment System - Main Entry Point
"""

import sys
from pathlib import Path
from core.instrument_assignment import WindInstrumentAssigner


def main():
    print("🎺 Wind Instrument Assignment System")
    print("=" * 50)

    # 初始化分配器
    try:
        assigner = WindInstrumentAssigner()
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

    # 設定檔案路徑
    base_path = Path(__file__).parent

    # 檢查是否有測試檔案
    test_midi = base_path / "examples" / "input_midi" / "test.mid"
    test_metadata = base_path / "examples" / "assignment_json" / "test_metadata.json"
    output_file = base_path / "examples" / "output" / "converted.mid"

    # 如果沒有測試MIDI檔案，提示用戶
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
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 執行轉換
    print(f"\n🚀 Starting conversion...")
    print(f"   Input MIDI: {test_midi}")
    print(f"   Assignment: {test_metadata}")
    print(f"   Output: {output_file}")

    success = assigner.process_assignment(
        str(test_midi), str(test_metadata), str(output_file)
    )

    if success:
        print("\n✅ Conversion completed successfully!")
        print(f"   Check output file: {output_file}")
    else:
        print("\n❌ Conversion failed!")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
