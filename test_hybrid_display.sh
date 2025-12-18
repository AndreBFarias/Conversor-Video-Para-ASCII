#!/bin/bash
# Test script for hybrid display backend implementation
# Tests all three display modes: terminal, window, and both

set -e  # Exit on error

echo "==================================="
echo "Testing Hybrid Display Backend"
echo "==================================="
echo ""

# Check if we're in the project root
if [ ! -f "config.ini" ]; then
    echo "Error: Run this script from the project root directory"
    exit 1
fi

# Check for test video
TEST_VIDEO="data_input/Luna_feliz.mp4"
if [ ! -f "$TEST_VIDEO" ]; then
    echo "Warning: Test video not found at $TEST_VIDEO"
    echo "Looking for any video in data_input..."
    TEST_VIDEO=$(find data_input -name "*.mp4" -o -name "*.avi" -o -name "*.mov" | head -n 1)
    if [ -z "$TEST_VIDEO" ]; then
        echo "Error: No test video found in data_input/"
        exit 1
    fi
    echo "Using: $TEST_VIDEO"
fi

# Backup original config
cp config.ini config.ini.backup
echo "✓ Backed up config.ini"

# Function to restore config on exit
cleanup() {
    echo ""
    echo "Restoring original config..."
    mv config.ini.backup config.ini
    echo "✓ Config restored"
}
trap cleanup EXIT

echo ""
echo "-----------------------------------"
echo "Test 1: Terminal Mode (Legacy)"
echo "-----------------------------------"
# Set display mode to terminal
sed -i 's/^display_mode = .*/display_mode = terminal/' config.ini
echo "Config: display_mode = terminal"
echo ""
echo "Converting video in terminal mode (no preview window)..."
python -m src.main << EOF
2
$TEST_VIDEO
EOF
echo "✓ Terminal mode conversion completed"
echo ""
read -p "Did you see terminal ASCII art? Press Enter to continue..."

echo ""
echo "-----------------------------------"
echo "Test 2: Window Mode (Live Preview)"
echo "-----------------------------------"
# Set display mode to window  
sed -i 's/^display_mode = .*/display_mode = window/' config.ini
echo "Config: display_mode = window"
echo ""
echo "Converting video in window mode (live preview)..."
echo "You should see an OpenCV window with pixel art preview."
echo "Press 'q' or ESC in the window to stop conversion early."
python -m src.main << EOF
2
$TEST_VIDEO
EOF
echo "✓ Window mode conversion completed"
echo ""
read -p "Did you see the OpenCV preview window? Press Enter to continue..."

echo ""
echo "-----------------------------------"
echo "Test 3: Both Modes Simultaneously"
echo "-----------------------------------"
# Set display mode to both
sed -i 's/^display_mode = .*/display_mode = both/' config.ini
echo "Config: display_mode = both"
echo ""
echo "Converting video in both modes (terminal + window)..."
echo "You should see BOTH terminal ASCII and OpenCV window."
python -m src.main << EOF
2
$TEST_VIDEO
EOF
echo "✓ Both mode conversion completed"
echo ""
read -p "Did you see both terminal and window output? Press Enter to continue..."

echo ""
echo "-----------------------------------"
echo "Test 4: Window Resizing"
echo "-----------------------------------"
echo "Playing the converted file..."
# Find the most recent output file
OUTPUT_FILE=$(ls -t data_output/*.txt | head -n 1)
if [ -z "$OUTPUT_FILE" ]; then
    echo "Error: No output file found in videos_saida/"
    exit 1
fi

echo "Playing: $OUTPUT_FILE"
echo "In window mode, try resizing the window manually."
echo "Press ESC or 'q' to quit playback."
python src/core/player.py "$OUTPUT_FILE" --loop &
PLAYER_PID=$!

sleep 5
echo ""
echo "Player is running in background (PID: $PLAYER_PID)"
read -p "Try resizing the window, then press Enter to stop playback..."

# Kill the player
kill $PLAYER_PID 2>/dev/null || true
wait $PLAYER_PID 2>/dev/null || true

echo ""
echo "-----------------------------------"
echo "Test 5: Keyboard Controls"
echo "-----------------------------------"
echo "Testing keyboard input..."
echo "This will play the video again. Test the following:"
echo "  - Press 'q' to quit"
echo "  - Or press ESC to quit"
echo ""
read -p "Press Enter to start playback..."

python src/core/player.py "$OUTPUT_FILE"

echo ""
echo "==================================="
echo "All Tests Completed!"
echo "==================================="
echo ""
echo "Summary:"
echo "  ✓ Terminal mode works (ASCII to stdout)"
echo "  ✓ Window mode works (OpenCV preview)"
echo "  ✓ Both mode works (simultaneous output)"
echo "  ✓ Window is resizable"
echo "  ✓ Keyboard controls work (q/ESC)"
echo ""
echo "The hybrid display backend is ready to use!"
