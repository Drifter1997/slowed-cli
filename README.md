# ✦ Slowed + Reverb Studio CLI ✦

A self-contained terminal studio for searching YouTube songs, auto-tuning slowed & reverb DSP, and exporting high-fidelity 320kbps MP3s.

## How to Run

Directly from anywhere in your terminal:
```bash
~/Music/slowed/slowed
```

Or navigate to the directory:
```bash
cd ~/Music/slowed
./slowed
```

*(Optional)* To run `slowed` from any directory without typing the full path, add an alias to your `~/.bashrc` or `~/.zshrc`:
```bash
alias slowed="~/Music/slowed/slowed"
```

## Features

- **Terminal YouTube Search**: Search for songs or artists and pick from interactive results with durations and channel names.
- **Direct URL Support**: Paste any YouTube link directly to skip searching.
- **Smart DSP Auto-Tuning**: Analyzes song BPM, brightness, and dynamics with `librosa` to calculate the optimal speed reduction and reverb mix.
- **Vibe Presets**:
  - ✨ *Auto-Tuned* (AI Dynamic BPM & Brightness match)
  - 🌌 *Ethereal & Dreamy* (0.82x speed, 42% reverb, wide stereo)
  - 🌃 *Nightdrive / Chill* (0.86x speed, 30% reverb, punchy)
  - 🌊 *Deep Slow & Heavy Reverb* (0.78x speed, 50% reverb)
  - ⚙️ *Custom Manual Settings*
- **Studio-Grade DSP**: Uses Spotify's `pedalboard` 32-bit floating-point audio engine with high-pass bass protection to keep 808s and kicks clean.
- **320kbps MP3 Export**: Encodes with `ffmpeg`, embedding YouTube thumbnail artwork and ID3 metadata tags.
- **Clean & Isolated**: Everything (Python virtualenv, DSP libraries, temporary cache) lives in `~/Music/slowed/`. Output tracks are saved directly to `~/Music/slowed/`.
