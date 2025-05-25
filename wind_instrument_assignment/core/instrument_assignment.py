"""
Wind Instrument Assignment Main Module
Handles instrument assignment and transposition for MIDI files
"""

import pretty_midi
import json
import sys
import os
from pathlib import Path

# Ensure modules in the same directory can be found
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import MIDI processor
try:
    from midi_processor import MidiProcessor

    print("✅ Successfully imported MidiProcessor")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


class WindInstrumentAssigner:
    def __init__(self, config_path=None):
        """Initialize the assigner"""
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent / "config" / "instruments_config.json"
            )

        self.config = self.load_config(config_path)
        self.midi_processor = MidiProcessor()
        print("✅ WindInstrumentAssigner initialized successfully")

    def load_config(self, config_path):
        """Load instrument configuration"""
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_assignment_metadata(self, json_path):
        """Load assignment metadata.json"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"📋 Loaded assignment metadata UUID: {data.get('UUID', 'Unknown')}")
            return data

    def process_single_assignment(self, original_instrument, target_instrument_name):
        """Process a single instrument assignment"""
        if target_instrument_name not in self.config["instruments"]:
            print(f"❌ Unknown target instrument: {target_instrument_name}")
            return None

        target_config = self.config["instruments"][target_instrument_name]
        print(f"🎯 Processing assignment to: → {target_config['description']}")

        # Transpose
        transposed_instrument = self.midi_processor.transpose_instrument(
            original_instrument, target_config["transposition_semitones"]
        )

        # Set instrument program
        final_instrument = self.midi_processor.set_instrument_program(
            transposed_instrument, target_config["program_number"]
        )

        # Check range
        self.midi_processor.check_instrument_range(
            final_instrument, target_config["range_low"], target_config["range_high"]
        )

        return final_instrument

    def process_assignment(self, midi_path, metadata_path, output_path):
        """Main processing function"""
        print("🚀 Starting instrument assignment...")

        # Load MIDI and assignment data
        midi_data = self.midi_processor.load_midi(midi_path)
        if midi_data is None:
            return False

        metadata = self.load_assignment_metadata(metadata_path)
        stems = metadata.get("stems", {})

        # Create a new MIDI object
        output_midi = pretty_midi.PrettyMIDI()

        # Process each stem assignment
        for stem_id, assignment in stems.items():
            track_index = int(stem_id[1:])  # S00 -> 0, S01 -> 1

            if track_index >= len(midi_data.instruments):
                print(f"⚠️  Track index {track_index} out of range, skipping")
                continue

            original_instrument = midi_data.instruments[track_index]
            target_name = assignment["assigned_instrument"]

            print(
                f"\n📎 Processing {stem_id}: {assignment['original_inst_class']} → {target_name}"
            )

            # If it's drums, copy directly
            if target_name.lower() == "drums":
                output_midi.instruments.append(original_instrument)
                print("🥁 Drums copied directly")
                continue

            # Process wind instrument assignment
            processed_instrument = self.process_single_assignment(
                original_instrument, target_name
            )
            if processed_instrument:
                output_midi.instruments.append(processed_instrument)

        # Save the result
        try:
            output_midi.write(output_path)
            print(f"💾 Successfully saved to: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return False


# Simple test
if __name__ == "__main__":
    assigner = WindInstrumentAssigner()
    print("🎺 Wind instrument assignment module test completed")
