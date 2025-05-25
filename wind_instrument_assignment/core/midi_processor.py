"""
MIDI Processing Module
Handles MIDI file loading, transposition, range checking, etc.
"""

import pretty_midi
import numpy as np


class MidiProcessor:
    def __init__(self):
        print("✅ MIDI Processor initialized")

    def load_midi(self, midi_path):
        """Load MIDI file"""
        try:
            midi_data = pretty_midi.PrettyMIDI(midi_path)
            print(f"📁 Successfully loaded MIDI: {len(midi_data.instruments)} tracks")
            return midi_data
        except Exception as e:
            print(f"❌ MIDI loading failed: {e}")
            return None

    def transpose_instrument(self, instrument, semitones):
        """Transpose instrument track"""
        if semitones == 0:
            return instrument

        # Create new instrument object
        new_instrument = pretty_midi.Instrument(
            program=instrument.program, is_drum=instrument.is_drum, name=instrument.name
        )

        # Transpose all notes
        for note in instrument.notes:
            new_pitch = note.pitch + semitones
            # Ensure pitch is within MIDI range (0-127)
            if 0 <= new_pitch <= 127:
                new_note = pretty_midi.Note(
                    velocity=note.velocity,
                    pitch=new_pitch,
                    start=note.start,
                    end=note.end,
                )
                new_instrument.notes.append(new_note)
            else:
                print(f"⚠️  Note {note.pitch} out of range after transposition, skipped")

        print(
            f"🎵 Transposed {semitones} semitones, processed {len(new_instrument.notes)} notes"
        )
        return new_instrument

    def check_instrument_range(self, instrument, range_low, range_high):
        """Check instrument range"""
        out_of_range_notes = []

        for note in instrument.notes:
            if note.pitch < range_low or note.pitch > range_high:
                out_of_range_notes.append(note.pitch)

        if out_of_range_notes:
            print(
                f"⚠️  Found {len(out_of_range_notes)} notes out of range ({range_low}-{range_high})"
            )
            print(f"   Out of range notes: {set(out_of_range_notes)}")

        return out_of_range_notes

    def set_instrument_program(self, instrument, program_number):
        """Set instrument program (sound)"""
        instrument.program = program_number
        print(f"🎺 Set instrument program: {program_number}")
        return instrument


# Simple test
if __name__ == "__main__":
    processor = MidiProcessor()
    print("🎼 MIDI processing module test completed")
