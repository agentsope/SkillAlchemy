#!/usr/bin/env python3
"""
Convert SRT/VTT subtitle files into clean plain-text transcripts.
Remove timestamps, sequence numbers, duplicate lines, and HTML tags to produce
directly readable text.

Usage:
    python3 srt_to_transcript.py input.srt [output.txt]
    python3 srt_to_transcript.py input.vtt [output.txt]

If no output file is specified, the default is input_transcript.txt.
"""

import sys
import re
from pathlib import Path


def clean_srt(content: str) -> str:
    """Clean subtitles in SRT format."""
    lines = content.strip().split('\n')
    texts = []

    for line in lines:
        line = line.strip()
        # Skip sequence-number lines containing only digits.
        if re.match(r'^\d+$', line):
            continue
        # Skip timestamp lines.
        if re.match(r'\d{2}:\d{2}:\d{2}', line):
            continue
        # Skip blank lines.
        if not line:
            continue
        # Remove HTML tags.
        line = re.sub(r'<[^>]+>', '', line)
        # Remove VTT positioning markers.
        line = re.sub(r'align:.*$|position:.*$', '', line).strip()
        if line:
            texts.append(line)

    # Deduplicate consecutive lines, which are common in automatic captions.
    deduped = []
    for text in texts:
        if not deduped or text != deduped[-1]:
            deduped.append(text)

    # Merge short consecutive sentences into paragraphs. Start a new paragraph
    # after terminal punctuation or a sufficiently long accumulated passage.
    result = []
    current = []

    for text in deduped:
        current.append(text)
        # Form a paragraph when the accumulated text is long enough or the
        # current subtitle ends with terminal punctuation.
        joined = ' '.join(current)
        if len(joined) > 200 or re.search(r'[.!?]$', text):
            result.append(joined)
            current = []

    if current:
        result.append(' '.join(current))

    return '\n\n'.join(result)


def clean_vtt(content: str) -> str:
    """Clean VTT subtitles by removing VTT metadata, then applying SRT logic."""
    # Remove the WEBVTT header.
    content = re.sub(r'^WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
    # Remove NOTE blocks.
    content = re.sub(r'NOTE.*?\n\n', '', content, flags=re.DOTALL)
    return clean_srt(content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 srt_to_transcript.py <input.srt|input.vtt> [output.txt]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        sys.exit(1)

    # Select the default output filename.
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.parent / f"{input_path.stem}_transcript.txt"

    # Read the source and detect its format.
    content = input_path.read_text(encoding='utf-8')

    if input_path.suffix.lower() == '.vtt' or content.startswith('WEBVTT'):
        transcript = clean_vtt(content)
    else:
        transcript = clean_srt(content)

    output_path.write_text(transcript, encoding='utf-8')

    # Report output statistics.
    word_count = len(transcript)
    line_count = transcript.count('\n') + 1
    print(f"✅ Conversion complete: {output_path}")
    print(f"   Characters: {word_count}  Paragraphs: {line_count}")


if __name__ == '__main__':
    main()
