"""
Test for Import Issues
"""

import sys
from pathlib import Path

print("🔍 Python version:", sys.version)
print("🔍 Current working directory:", Path.cwd())

# Try to import and inspect module contents
try:
    import midi_processor

    print("✅ Successfully imported midi_processor module")
    print("🔍 Module attributes:", dir(midi_processor))

    # Check if MidiProcessor class exists
    if hasattr(midi_processor, "MidiProcessor"):
        print("✅ Found MidiProcessor class")
        from midi_processor import MidiProcessor

        print("✅ Successfully imported MidiProcessor class")
    else:
        print("❌ MidiProcessor class not found in the module")

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback

    traceback.print_exc()
