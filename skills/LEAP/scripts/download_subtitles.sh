#!/bin/bash
# Download subtitles from a YouTube video.
# Usage: ./download_subtitles.sh <YouTube_URL> [output_directory]
# Prefer human-authored subtitles; fall back to automatically generated subtitles.
# Language priority: Chinese > English > other languages.
#
# Dependency: yt-dlp (https://github.com/yt-dlp/yt-dlp)
#   brew install yt-dlp    # macOS
#   pip install yt-dlp     # cross-platform

set -e

URL="$1"
OUTPUT_DIR="${2:-.}"

if [ -z "$URL" ]; then
    echo "Usage: ./download_subtitles.sh <YouTube_URL> [output_directory]"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo ">>> Checking available subtitles..."
yt-dlp --list-subs --no-download "$URL" 2>/dev/null | tail -20

echo ""
echo ">>> Attempting to download human-authored subtitles (Chinese first)..."

# Attempt 1: human-authored Chinese subtitles.
if yt-dlp --write-subs --sub-langs "zh-Hans,zh-Hant,zh,zh-CN,zh-TW" --sub-format srt --skip-download -o "$OUTPUT_DIR/%(title)s" "$URL" 2>/dev/null; then
    FOUND=$(find "$OUTPUT_DIR" -name "*.srt" -newer /tmp/.ytdlp_marker 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        echo "✅ Download complete: $FOUND"
        exit 0
    fi
fi

# Attempt 2: human-authored English subtitles.
echo ">>> No human-authored Chinese subtitles found; trying English..."
if yt-dlp --write-subs --sub-langs "en,en-US,en-GB" --sub-format srt --skip-download -o "$OUTPUT_DIR/%(title)s" "$URL" 2>/dev/null; then
    FOUND=$(find "$OUTPUT_DIR" -name "*.srt" -mmin -1 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        echo "✅ Download complete: $FOUND"
        exit 0
    fi
fi

# Attempt 3: automatically generated subtitles, preferring Chinese.
echo ">>> No human-authored subtitles found; trying automatically generated subtitles..."
if yt-dlp --write-auto-subs --sub-langs "zh-Hans,zh,en" --sub-format srt --skip-download -o "$OUTPUT_DIR/%(title)s" "$URL" 2>/dev/null; then
    FOUND=$(find "$OUTPUT_DIR" -name "*.srt" -o -name "*.vtt" 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        echo "✅ Automatic subtitle download complete: $FOUND"
        exit 0
    fi
fi

echo "❌ No usable subtitles found"
exit 1
