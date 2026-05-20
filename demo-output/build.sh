#!/bin/bash
# Demo Video Build Script
# Usage: bash build.sh

set -e

OUTPUT_DIR="$(pwd)"
SCENES_DIR="$OUTPUT_DIR/scenes"
NARRATION_DIR="$OUTPUT_DIR/narration"
FRAMES_DIR="$OUTPUT_DIR/frames"
AUDIO_DIR="$OUTPUT_DIR/audio"

echo "🎬 Cloud-Native Bookstore Demo Video Builder"
echo "============================================"

# Create directories
mkdir -p "$FRAMES_DIR" "$AUDIO_DIR"

# Check dependencies
check_cmd() {
  if ! command -v "$1" &> /dev/null; then
    echo "❌ $1 not found. Please install it."
    return 1
  fi
  echo "✅ $1 found"
}

echo ""
echo "Checking dependencies..."
check_cmd python3 || exit 1
check_cmd ffmpeg || exit 1

# Optional: playwright and edge-tts
PLAYWRIGHT_AVAILABLE=false
EDGE_TTS_AVAILABLE=false

if python3 -c "import playwright" 2>/dev/null; then
  PLAYWRIGHT_AVAILABLE=true
  echo "✅ Playwright available"
else
  echo "⚠️  Playwright not available. Install: pip3 install playwright"
fi

if command -v edge-tts &> /dev/null; then
  EDGE_TTS_AVAILABLE=true
  echo "✅ edge-tts available"
else
  echo "⚠️  edge-tts not available. Install: pip3 install edge-tts"
fi

echo ""
echo "Step 1: Rendering HTML scenes to PNG frames..."
if [ "$PLAYWRIGHT_AVAILABLE" = true ]; then
  python3 << 'PYTHON_SCRIPT'
import asyncio
from playwright.async_api import async_playwright
import json

with open('scenes.json', 'r') as f:
    manifest = json.load(f)

async def render_scenes():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        for scene in manifest['scenes']:
            scene_file = scene['file']
            if scene_file.endswith('.html'):
                print(f"Rendering {scene['id']}...")
                await page.goto(f"file://{__import__('os').path.abspath(scene_file)}")
                await page.screenshot(path=f"frames/{scene['id']}.png", full_page=True)
        
        await browser.close()

asyncio.run(render_scenes())
PYTHON_SCRIPT
  echo "✅ HTML scenes rendered"
else
  echo "⚠️  Skipping HTML rendering. Manual step: Open each .html file in Chrome at 1920x1080 and screenshot."
fi

echo ""
echo "Step 2: Generating narration audio..."
if [ "$EDGE_TTS_AVAILABLE" = true ]; then
  python3 << 'PYTHON_SCRIPT'
import json
import os
import subprocess

with open('scenes.json', 'r') as f:
    manifest = json.load(f)

for scene in manifest['scenes']:
    narration = scene.get('narration', '')
    if narration:
        audio_file = f"audio/{scene['id']}.mp3"
        txt_file = f"narration/{scene['id']}.txt"
        
        # Write text file
        with open(txt_file, 'w') as f:
            f.write(narration)
        
        # Generate audio
        print(f"Generating audio for {scene['id']}...")
        subprocess.run([
            'edge-tts', 
            '--text', narration,
            '--write-media', audio_file,
            '--voice', 'en-US-GuyNeural'
        ], check=True, capture_output=True)

print("✅ Audio generated")
PYTHON_SCRIPT
else
  echo "⚠️  Skipping audio generation. Text files written to narration/ for manual recording."
fi

echo ""
echo "Step 3: Video assembly with ffmpeg..."
echo ""
echo "Manual ffmpeg command to assemble (run after preparing frames and audio):"
echo ""
cat << 'FFMPEG_CMD'
# Example: Create a simple slideshow with crossfade
# Adjust timings based on scenes.json durations

ffmpeg -f lavfi -i color=c=black:s=1920x1080:r=30 -i frames/s01.png \
  -filter_complex "[0:v][1:v]overlay=0:0" -t 5 -c:v libx264 frames/s01.mp4

# For each scene, create a video segment:
# ffmpeg -loop 1 -i frames/SCENE.png -i audio/SCENE.mp3 \
#   -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
#   -shortest -pix_fmt yuv420p -t DURATION segments/SCENE.mp4

# Concatenate all segments:
# ffmpeg -f concat -i segments.txt -c copy output.mp4

FFMPEG_CMD

echo ""
echo "🎉 Build script complete!"
echo ""
echo "Next steps:"
echo "1. Render screen recordings for scenes marked 'screen-recording://'"
echo "2. Run the ffmpeg commands above to assemble final video"
echo "3. Add background music and final polish in video editor"
echo ""
echo "Output locations:"
echo "  - Frames: $FRAMES_DIR"
echo "  - Audio:  $AUDIO_DIR"
echo "  - Script: $OUTPUT_DIR/demo-script.md"
