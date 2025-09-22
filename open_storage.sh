#!/bin/bash
# TTS Storage Helper Script

echo "🎵 TTS Storage Helper"
echo "===================="

# Open storage folder in Finder
echo "Opening storage folder in Finder..."
open "$(pwd)/storage/"

# Show latest MP3 files
echo ""
echo "📁 Latest MP3 files:"
ls -lt storage/*.mp3 | head -5

# Get the latest file
LATEST_FILE=$(ls -t storage/*.mp3 | head -1)
if [ -n "$LATEST_FILE" ]; then
    echo ""
    echo "🎯 Latest file: $LATEST_FILE"
    
    # Copy to Downloads
    BASENAME=$(basename "$LATEST_FILE" .mp3 | cut -d'-' -f1)
    cp "$LATEST_FILE" "$HOME/Downloads/${BASENAME}.mp3"
    echo "✅ Copied to Downloads as: ${BASENAME}.mp3"
    
    # Open Downloads folder
    echo "📂 Opening Downloads folder..."
    open "$HOME/Downloads/"
else
    echo "❌ No MP3 files found in storage"
fi