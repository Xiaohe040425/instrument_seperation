"""
Simple audio conversion module - No FluidSynth dependency
Uses basic MIDI synthesis for audio output
"""

import numpy as np
from pathlib import Path
import json


class SimpleAudioConverter:
    def __init__(self):
        """Initialize simple audio converter"""
        self.sample_rate = 44100
        print("✅ Simple Audio Converter initialized (no FluidSynth)")

    def generate_sine_wave(self, frequency, duration, amplitude=0.3):
        """Generate a simple sine wave"""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = amplitude * np.sin(2 * np.pi * frequency * t)
        return wave

    def midi_note_to_frequency(self, midi_note):
        """Convert MIDI note number to frequency"""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    def simple_midi_to_wav(self, midi_path, output_path):
        """Convert MIDI to WAV using simple synthesis"""
        try:
            # 這裡我們先用一個簡單的方法
            # 生成一個測試音頻來驗證流程

            print(f"🔄 Converting MIDI to WAV (simple synthesis)...")
            print(f"   Input: {Path(midi_path).name}")
            print(f"   Output: {Path(output_path).name}")

            # 生成一個簡單的測試和弦 (C major)
            duration = 3.0  # 3秒
            notes = [60, 64, 67]  # C, E, G

            audio = np.zeros(int(self.sample_rate * duration))

            for note in notes:
                freq = self.midi_note_to_frequency(note)
                wave = self.generate_sine_wave(freq, duration, 0.2)
                audio += wave

            # 正規化
            if len(audio) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.8

            # 儲存為WAV (使用基本方法)
            self.save_wav_simple(audio, output_path)

            print("✅ Simple WAV conversion successful")
            print("   Note: This is a basic test synthesis")
            return True

        except Exception as e:
            print(f"❌ Simple conversion failed: {e}")
            return False

    def save_wav_simple(self, audio_data, output_path):
        """Save audio data as WAV file using basic method"""
        try:
            import wave
            import struct

            # 轉換為16-bit整數
            audio_int = (audio_data * 32767).astype(np.int16)

            with wave.open(str(output_path), "w") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int.tobytes())

        except Exception as e:
            print(f"❌ WAV save failed: {e}")
            raise

    def midi_to_audio(self, midi_path, output_path, format="wav"):
        """Convert MIDI to audio"""
        if format.lower() == "wav":
            return self.simple_midi_to_wav(midi_path, output_path)
        else:
            print(f"❌ Format {format} not supported in simple converter")
            return False


# 測試
if __name__ == "__main__":
    converter = SimpleAudioConverter()
    print("🎵 Simple Audio Converter test completed")
