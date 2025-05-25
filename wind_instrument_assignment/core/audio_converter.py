"""
Audio conversion module - Fixed file management
Converts MIDI files to audio formats (WAV, MP3)
"""

import pretty_midi
import numpy as np
from pathlib import Path
import soundfile as sf


class AudioConverter:
    def __init__(self, soundfont_path=None):
        """Initialize audio converter"""

        self.soundfont_path = soundfont_path
        self.sample_rate = 44100

        if soundfont_path is None:
            # 尋找預設的soundfont
            default_sf = (
                Path(__file__).parent.parent / "soundfonts" / "GeneralUser_GS.sf2"
            )
            if default_sf.exists():
                self.soundfont_path = str(default_sf)

        print(f"✅ Audio Converter initialized (pretty_midi synthesizer)")
        if self.soundfont_path:
            print(f"   SoundFont: {Path(self.soundfont_path).name}")

    def midi_to_wav_prettymidi(self, midi_path, output_path):
        """Convert MIDI to WAV using pretty_midi's synthesizer"""

        try:
            print(f"🔄 Converting MIDI to WAV...")
            print(f"   Input: {Path(midi_path).name}")
            print(f"   Output: {Path(output_path).name}")

            # 載入MIDI檔案
            midi_data = pretty_midi.PrettyMIDI(midi_path)

            # 使用pretty_midi合成器
            if self.soundfont_path and Path(self.soundfont_path).exists():
                try:
                    # 嘗試使用SoundFont
                    audio = midi_data.fluidsynth(
                        sf2_path=self.soundfont_path, fs=self.sample_rate
                    )
                    print("   ✅ Using custom SoundFont")
                except Exception as sf_error:
                    print(
                        f"   ⚠️  SoundFont failed ({sf_error}), using default synthesizer"
                    )
                    audio = midi_data.synthesize(fs=self.sample_rate)
            else:
                # 使用預設合成器
                audio = midi_data.synthesize(fs=self.sample_rate)
                print("   ✅ Using default synthesizer")

            # 檢查音頻是否為空
            if len(audio) == 0:
                print("   ❌ Generated audio is empty")
                return False

            # 正規化音量避免削峰
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val * 0.8

            # 確保輸出目錄存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 儲存WAV檔案
            sf.write(output_path, audio, self.sample_rate)

            # 驗證檔案是否真的被創建
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                print(f"   ✅ WAV conversion successful ({file_size} bytes)")
                return True
            else:
                print("   ❌ WAV file was not created")
                return False

        except Exception as e:
            print(f"   ❌ WAV conversion failed: {e}")
            return False

    def wav_to_mp3_simple(self, wav_path, mp3_path):
        """Convert WAV to MP3 - simplified without ffmpeg dependency"""
        try:
            print(f"🔄 Converting WAV to MP3 (simple method)...")

            # 暫時跳過MP3轉換，因為缺少ffmpeg
            print("   ⚠️  MP3 conversion requires ffmpeg")
            print("   💡 For now, please use the WAV file")
            return False

        except Exception as e:
            print(f"❌ MP3 conversion failed: {e}")
            return False

    def midi_to_audio(self, midi_path, output_path, format="wav"):
        """Convert MIDI to audio (WAV or MP3)"""

        midi_path = Path(midi_path)
        output_path = Path(output_path)

        if format.lower() == "wav":
            return self.midi_to_wav_prettymidi(str(midi_path), str(output_path))

        elif format.lower() == "mp3":
            # 先轉成WAV
            temp_wav = output_path.with_suffix(".wav")

            if self.midi_to_wav_prettymidi(str(midi_path), str(temp_wav)):
                # 暫時不刪除WAV檔案，直接返回成功但提示用戶
                print(f"   💡 WAV file created: {temp_wav}")
                print(f"   ⚠️  MP3 conversion skipped (requires ffmpeg)")
                print(f"   📁 Please use the WAV file for now")
                return False  # 返回False因為MP3確實沒有成功
            return False

        else:
            print(f"❌ Unsupported format: {format}")
            return False


# 測試
if __name__ == "__main__":
    converter = AudioConverter()
    print("🎵 Audio Converter test completed")
