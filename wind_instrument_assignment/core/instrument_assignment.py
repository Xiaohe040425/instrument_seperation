"""
管樂器分配主模組
處理MIDI檔案的樂器分配和移調
"""

import pretty_midi
import json
from pathlib import Path


class WindInstrumentAssigner:
    def __init__(self, config_path=None):
        """初始化分配器"""
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent / "config" / "instruments_config.json"
            )

        self.config = self.load_config(config_path)
        print("✅ 管樂器分配器初始化完成")

    def load_config(self, config_path):
        """載入樂器配置"""
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_assignment_metadata(self, json_path):
        """載入分配metadata.json"""
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def process_assignment(self, midi_path, metadata_path, output_path):
        """主要處理函數 - 目前只是框架"""
        print(f"📁 載入MIDI: {midi_path}")
        print(f"📁 載入分配資料: {metadata_path}")
        print(f"📁 輸出路徑: {output_path}")
        print("⚠️  實際處理邏輯待實作...")
        return True


# 簡單測試
if __name__ == "__main__":
    assigner = WindInstrumentAssigner()
    print("🎺 管樂器分配模組測試完成")
