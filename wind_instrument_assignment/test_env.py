import pretty_midi
import numpy as np
import json

print("✅ pretty_midi 版本:", pretty_midi.__version__)
print("✅ numpy 版本:", np.__version__)
print("✅ 環境設置完成！")

# 簡單測試 pretty_midi 功能
try:
    # 創建一個空的MIDI物件
    midi = pretty_midi.PrettyMIDI()
    print("✅ pretty_midi 功能正常")
except Exception as e:
    print("❌ pretty_midi 測試失敗:", e)
