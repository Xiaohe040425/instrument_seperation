"""
Basic functionality test
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.midi_processor import MidiProcessor
from core.instrument_assignment import WindInstrumentAssigner


def test_midi_processor():
    """Test MIDI processor basic functions"""
    print("🧪 Testing MIDI Processor...")

    processor = MidiProcessor()

    # Test basic functionality without actual files
    print("✅ MIDI Processor instantiation successful")
    return True


def test_instrument_assigner():
    """Test instrument assigner basic functions"""
    print("🧪 Testing Instrument Assigner...")

    try:
        assigner = WindInstrumentAssigner()
        print("✅ Instrument Assigner instantiation successful")

        # Test configuration loading
        config = assigner.config
        instruments = config.get("instruments", {})
        print(f"✅ Loaded {len(instruments)} instrument configurations")

        for name, info in instruments.items():
            print(f"   - {name}: {info['description']}")

        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    print("🔬 Running Basic Functionality Tests")
    print("=" * 40)

    tests = [test_midi_processor, test_instrument_assigner]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test error: {e}\n")

    print(f"📊 Test Results: {passed}/{len(tests)} passed")
    return passed == len(tests)


if __name__ == "__main__":
    main()
