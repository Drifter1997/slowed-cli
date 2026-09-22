# 🎧 slowed-cli

> **Self-contained terminal audio studio for creating high-fidelity Slowed + Reverb music.**  
> Search YouTube, analyze BPM & dynamics, auto-tune DSP parameters with Spotify's `pedalboard` engine, and export 320kbps MP3s with embedded artwork.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Audio DSP](https://img.shields.io/badge/DSP-Pedalboard%20%2B%20Librosa-red.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Linux%20%2F%20macOS-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

---

## ✨ Features

- **🔍 Terminal YouTube Search**: Search songs and artists interactively with track durations and uploader metadata, or paste YouTube URLs directly.
- **🧠 Smart DSP Auto-Tuning**: Uses `librosa` spectral analysis to calculate exact track BPM, musical brightness, and dynamic range, automatically selecting optimal speed reduction and reverb wet/dry ratios.
- **🎛️ Studio-Grade DSP Engine**:
  - Powered by Spotify's `pedalboard` 32-bit floating-point audio DSP.
  - High-pass bass protection filter to keep sub-bass frequencies and 808 kicks clean without muddy reverb distortion.
  - Resampling with high-order interpolation for pristine pitch-shifting without metallic artifacts.
- **Presets & Manual Mode**:
  - ✨ **Auto-Tuned**: Smart dynamic BPM & brightness matching.
  - 🌌 **Ethereal & Dreamy**: 0.82x speed, 42% reverb, wide stereo expansion.
  - 🌃 **Nightdrive / Chill**: 0.86x speed, 30% reverb, punchy transient response.
  - 🌊 **Deep Slow & Heavy Reverb**: 0.78x speed, 50% reverb, cavernous decay.
  - ⚙️ **Custom Manual Mode**: Dial in speed, pitch factor, reverb room size, damping, and wet level interactively.
- **💾 High-Fidelity 320kbps MP3 Export**:
  - Encoded with `ffmpeg` at maximum bitrate (`-b:a 320k`).
  - Automatically fetches and embeds high-resolution YouTube thumbnail artwork and ID3 metadata.
- **⚡ Completely Isolated & Portable**:
  - Self-contained Python virtual environment and caching.
  - Zero pollution of your global system packages.

---

## 📦 Requirements

- **Linux** or **macOS**
- **Python 3.10+**
- **ffmpeg** (for audio demuxing and encoding)
- **yt-dlp** (for YouTube audio retrieval)

On Arch Linux:
```bash
sudo pacman -S ffmpeg yt-dlp python
```

---

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Drifter1997/slowed-cli.git ~/Music/slowed
   cd ~/Music/slowed
   ```

2. **Initialize virtual environment and install dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   chmod +x slowed main.py run.sh
   ```

3. **Global Access (Optional)**:
   Symlink `slowed` to your `~/.local/bin` for easy terminal access:
   ```bash
   ln -sf ~/Music/slowed/slowed ~/.local/bin/slowed
   ```

---

## ⌨️ Usage

Launch `slowed` from any terminal:
```bash
slowed
```

Or run directly from the project directory:
```bash
cd ~/Music/slowed && ./slowed
```

### Quick Workflow
1. Enter search query (e.g. `Joji - Die For You` or paste a YouTube URL).
2. Select your desired track from the interactive list.
3. Choose a preset (`Auto-Tuned`, `Ethereal`, `Nightdrive`, `Deep Slow`, or `Custom`).
4. Watch real-time DSP processing, stereo expansion, and high-pass filtering.
5. Export completed 320kbps MP3 with embedded artwork into the output directory.

---

## 📁 Repository Structure

```
slowed-cli/
├── main.py           # Core TUI, YouTube search, DSP pipeline, and export logic
├── slowed            # Executable launcher script
├── run.sh            # Alternative shell launcher
├── requirements.txt  # pedalboard, librosa, yt-dlp, numpy, soundfile
└── README.md
```

---

## 📄 License

MIT License. Built for music producers and terminal enthusiasts.
