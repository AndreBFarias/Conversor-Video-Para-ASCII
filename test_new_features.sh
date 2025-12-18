#!/bin/bash
# Test script for new hybrid display improvements
# Tests ASCII-in-window rendering and interactive zoom controls

set -e  # Exit on error

echo "==========================================="
echo "🎮 Testing Hybrid Display Improvements"
echo "==========================================="
echo ""

# Check if we're in the project root
if [ ! -f "config.ini" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Check for test video output
TEST_FILE=$(find data_output -name "*.txt" -type f | head -n 1)
if [ -z "$TEST_FILE" ]; then
    echo "⚠️  No .txt files found in data_output/"
    echo "Let's convert a test video first..."
    
    # Find a test video
    TEST_VIDEO=$(find data_input -name "*.mp4" -o -name "*.avi" -o -name "*.mov" | head -n 1)
    if [ -z "$TEST_VIDEO" ]; then
        echo "❌ No test video found in data_input/"
        exit 1
    fi
    
    echo "📹 Converting: $TEST_VIDEO"
    # turbo
    python -m src.main <<EOF
2
$TEST_VIDEO
EOF
    
    # Find the newly created file
    TEST_FILE=$(find data_output -name "*.txt" -type f | head -n 1)
fi

echo "✅ Using test file: $TEST_FILE"
echo ""

# Backup original config
cp config.ini config.ini.backup
echo "✅ Backed up config.ini"

# Function to restore config on exit
cleanup() {
    echo ""
    echo "Restoring original config..."
    mv config.ini.backup config.ini
    echo "✅ Config restored"
}
trap cleanup EXIT

echo ""
echo "==========================================="
echo "Test 1: ASCII in Window Mode"
echo "==========================================="
echo ""

# Set display mode to window
sed -i 's/^display_mode = .*/display_mode = window/' config.ini
echo "Config: display_mode = window"
echo ""
echo "🎨 This will show ASCII art in an OpenCV window (not just terminal!)"
echo "Try these controls:"
echo "  [+] or [=] - Zoom in"
echo "  [-] - Zoom out"
echo "  [h] - Show help"
echo "  [q] or [ESC] - Quit"
echo ""
read -p "Press Enter to start playback..."

python -m src.core.player "$TEST_FILE" --loop &
PLAYER_PID=$!

echo ""
echo "Player running (PID: $PLAYER_PID)"
echo ""
read -p "Try the zoom controls (+/-), then press Enter to stop..."

# Kill the player
kill $PLAYER_PID 2>/dev/null || true
wait $PLAYER_PID 2>/dev/null || true

echo ""
echo "==========================================="
echo "Test 2: Interactive Zoom Demo"
echo "==========================================="
echo ""
echo "🔍 Now let's test zoom controls with a static image"
echo "You can use +/- keys to zoom in/out in real-time!"
echo ""
read -p "Press Enter to start..."

python -m src.core.player "$TEST_FILE"

echo ""
echo "==========================================="
echo "Test 3: Both Modes (Hybrid)"
echo "==========================================="
echo ""

# Set display mode to both
sed -i 's/^display_mode = .*/display_mode = both/' config.ini
echo "Config: display_mode = both"
echo ""
echo "🎭 You should see BOTH terminal ASCII AND window simultaneously!"
echo "Zoom controls work only in the window."
echo ""
read -p "Press Enter to start..."

python -m src.core.player "$TEST_FILE"

echo ""
echo "==========================================="
echo "✅ All Tests Completed!"
echo "==========================================="
echo ""
echo "Summary of New Features:"
echo "  ✅ ASCII art can now be displayed in OpenCV windows"
echo "  ✅ Interactive zoom controls (+/- keys, 1x to 20x)"
echo "  ✅ Works in all display modes (terminal/window/both)"
echo "  ✅ Real-time zoom adjustment during playback"
echo "  ✅ Help command (h key) for on-screen assistance"
echo ""
echo "🎉 The hybrid display system is fully enhanced!"
echo ""
