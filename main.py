#!/usr/bin/env python3
"""
Slowed + Reverb Studio CLI
Search YouTube with in-terminal visual thumbnails, download, auto-tune DSP, and export 320kbps MP3s.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import soundfile as sf
import yt_dlp
import librosa
from pedalboard import Pedalboard, Reverb, HighpassFilter, Gain
from pedalboard.io import AudioFile
import questionary
from questionary import Choice
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from PIL import Image

console = Console()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR
TMP_DIR = BASE_DIR / ".tmp"

TMP_DIR.mkdir(parents=True, exist_ok=True)


def print_banner():
    banner_text = Text()
    banner_text.append("✦ ", style="bold magenta")
    banner_text.append("SLOWED + REVERB STUDIO", style="bold cyan")
    banner_text.append(" ✦\n", style="bold magenta")
    banner_text.append("YouTube Terminal Search (Visual Cards) & High-Fidelity Audio DSP", style="dim white")

    console.print(
        Panel(
            banner_text,
            border_style="cyan",
            expand=False,
            padding=(1, 3),
        )
    )


def format_duration(seconds):
    if not seconds:
        return "LIVE / Unknown"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def get_thumbnail_url(entry: dict) -> str:
    """Extracts thumbnail URL from search entry."""
    video_id = entry.get("id")
    thumbs = entry.get("thumbnails") or []
    if thumbs:
        for t in reversed(thumbs):
            if t.get("url"):
                return t["url"]
    if video_id:
        return f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
    return entry.get("thumbnail") or ""


def render_thumbnail_art(thumb_url: str, width: int = 22, height: int = 7) -> str:
    """Fetches and renders thumbnail character art with standard symbols mode."""
    if not thumb_url:
        return " [No Thumbnail] "
    try:
        req = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            img_data = response.read()

        res = subprocess.run(
            ["chafa", f"--size={width}x{height}", "--format=symbols", "-"],
            input=img_data,
            capture_output=True,
        )
        if res.returncode == 0 and res.stdout:
            return res.stdout.decode("utf-8", errors="replace").strip("\n")
    except Exception:
        pass

    return f"[{width}x{height} preview]"


def search_youtube_with_thumbnails(query: str, max_results: int = 5) -> list:
    """Searches YouTube and fetches video info + rendered thumbnails in parallel."""
    with console.status("[bold cyan]Searching YouTube & generating thumbnails...", spinner="dots"):
        ydl_opts = {
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                res = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                entries = [e for e in res.get("entries", []) if e]
        except Exception as e:
            console.print(f"[bold red]Search Error:[/bold red] {e}")
            return []

        if not entries:
            return []

        # Concurrently fetch thumbnail ASCII/ANSI renderings
        thumb_urls = [get_thumbnail_url(e) for e in entries]
        with ThreadPoolExecutor(max_workers=5) as executor:
            rendered_thumbs = list(executor.map(render_thumbnail_art, thumb_urls))

        for entry, thumb_art in zip(entries, rendered_thumbs):
            entry["rendered_thumbnail"] = thumb_art

        return entries


def display_search_cards(entries: list):
    """Displays search results with visual thumbnail cards."""
    console.print("\n[bold cyan]🎬 Search Results:[/bold cyan]\n")
    for i, entry in enumerate(entries, 1):
        title = entry.get("title", "Untitled")
        channel = entry.get("uploader", "Unknown Channel")
        dur = format_duration(entry.get("duration"))
        vid_id = entry.get("id", "")
        url = f"https://youtu.be/{vid_id}" if vid_id else ""
        thumb_art = entry.get("rendered_thumbnail", "")

        table = Table.grid(padding=(0, 2))
        table.add_column(justify="left", vertical="middle")
        table.add_column(justify="left", vertical="middle")

        info_text = Text()
        info_text.append(f"{title}\n", style="bold white")
        info_text.append("Channel: ", style="dim")
        info_text.append(f"{channel}\n", style="cyan")
        info_text.append("Duration: ", style="dim")
        info_text.append(f"{dur}  ", style="yellow")
        if url:
            info_text.append("•  Link: ", style="dim")
            info_text.append(f"{url}", style="blue underline")

        try:
            thumb_renderable = Text.from_ansi(thumb_art)
        except Exception:
            thumb_renderable = Text("[Thumbnail]")

        table.add_row(thumb_renderable, info_text)

        panel = Panel(
            table,
            title=f"[bold cyan][ {i} ][/bold cyan]",
            border_style="bright_blue",
            expand=False,
        )
        console.print(panel)


def download_audio_and_metadata(video_url: str, output_prefix: Path) -> dict:
    """Downloads audio to lossless WAV and retrieves metadata & thumbnail."""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_prefix) + ".%(ext)s",
        "writethumbnail": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)

    wav_file = output_prefix.with_suffix(".wav")

    # Locate downloaded thumbnail if present
    thumbnail_file = None
    for ext in [".jpg", ".png", ".webp"]:
        thumb_candidate = output_prefix.with_suffix(ext)
        if thumb_candidate.exists():
            thumbnail_file = thumb_candidate
            break

    return {
        "wav_path": wav_file,
        "title": info.get("title", "Unknown Track"),
        "uploader": info.get("uploader", "Unknown Artist"),
        "duration": info.get("duration", 0),
        "thumbnail_path": thumbnail_file,
    }


def analyze_audio(wav_path: Path) -> dict:
    """Analyzes tempo, brightness, and energy to calculate optimal DSP parameters."""
    with console.status("[bold magenta]🧠 Analyzing track dynamics (BPM, brightness, density)...", spinner="bouncingBar"):
        # Load up to first 90 seconds for fast analysis
        y, sr = librosa.load(str(wav_path), sr=22050, mono=True, duration=90)

        # 1. Estimate BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0] if isinstance(tempo, (np.ndarray, list)) else tempo)

        # 2. Spectral Centroid (Brightness)
        centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))

        # 3. RMS Energy (Density)
        rms = float(np.mean(librosa.feature.rms(y=y)))

        # --- AUTO PARAMETER RULES ---
        if bpm > 135:
            speed = 0.80
        elif bpm > 105:
            speed = 0.84
        elif bpm > 80:
            speed = 0.88
        else:
            speed = 0.92

        # Dynamic reverb wetness
        wet_level = float(np.clip(0.48 - (rms * 0.8), 0.20, 0.42))

        # Damping based on brightness
        damping = float(np.clip((centroid - 1500) / 3000, 0.35, 0.70))
        room_size = 0.65 if speed <= 0.85 else 0.55

        return {
            "bpm": round(bpm, 1),
            "speed": round(speed, 2),
            "wet_level": round(wet_level, 2),
            "room_size": round(room_size, 2),
            "damping": round(damping, 2),
        }


def process_dsp(
    input_wav: Path,
    output_wav: Path,
    speed: float,
    room_size: float,
    damping: float,
    wet_level: float,
    dry_level: float = 0.85,
):
    """Processes audio using Pedalboard with studio reverb and sample-rate pitch drop."""
    with AudioFile(str(input_wav)) as f:
        audio = f.read(f.frames)
        sr = f.samplerate

    new_sample_rate = int(sr * speed)

    # Studio DSP Board
    # Highpass filter protects 808/sub-bass from getting muddy in the reverb
    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=120),
        Reverb(
            room_size=room_size,
            damping=damping,
            wet_level=wet_level,
            dry_level=dry_level,
            width=1.0,
        ),
        Gain(gain_db=1.0),
    ])

    processed = board(audio, sr)

    # Prevent digital clipping
    max_val = np.max(np.abs(processed))
    if max_val > 0.98:
        processed = processed * (0.98 / max_val)

    sf.write(str(output_wav), processed.T, new_sample_rate, subtype="PCM_24")


def export_mp3(
    processed_wav: Path,
    output_mp3: Path,
    title: str,
    artist: str,
    thumbnail_path: Path = None,
):
    """Converts 24-bit WAV to 320kbps MP3 with embedded metadata & cover art."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(processed_wav),
    ]

    # Convert thumbnail to standard jpg if necessary
    cover_jpg = None
    if thumbnail_path and thumbnail_path.exists():
        try:
            if thumbnail_path.suffix.lower() in [".webp", ".png"]:
                im = Image.open(thumbnail_path).convert("RGB")
                cover_jpg = thumbnail_path.with_suffix(".cover.jpg")
                im.save(cover_jpg, "JPEG", quality=95)
                thumbnail_path = cover_jpg
        except Exception:
            pass

    if thumbnail_path and thumbnail_path.exists():
        cmd.extend(["-i", str(thumbnail_path)])
        cmd.extend([
            "-map", "0:a",
            "-map", "1:0",
            "-c:v", "mjpeg",
            "-disposition:v:0", "attached_pic",
        ])
    else:
        cmd.extend(["-map", "0:a"])

    cmd.extend([
        "-c:a", "libmp3lame",
        "-b:a", "320k",
        "-id3v2_version", "3",
        "-metadata", f"title={title} (Slowed + Reverb)",
        "-metadata", f"artist={artist}",
        "-metadata", "album=Slowed & Reverb",
        "-metadata", "genre=Slowed / Lo-Fi / Chill",
        str(output_mp3),
    ])

    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if cover_jpg and cover_jpg.exists():
        try:
            cover_jpg.unlink()
        except Exception:
            pass


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def select_preset_or_custom(auto_params: dict) -> dict:
    """Lets user choose auto-tuning, stylized presets, or custom sliders."""
    choices = [
        Choice(
            title=f"✨ Auto-Tuned (Smart DSP: ~{auto_params['bpm']} BPM → {auto_params['speed']}x speed, {int(auto_params['wet_level']*100)}% reverb)",
            value="auto",
        ),
        Choice(
            title="🌌 Ethereal & Dreamy (0.82x speed, 42% reverb, wide space)",
            value="dreamy",
        ),
        Choice(
            title="🌃 Nightdrive / Chill (0.86x speed, 30% reverb, crisp)",
            value="nightdrive",
        ),
        Choice(
            title="🌊 Deep Slow & Heavy Reverb (0.78x speed, 50% reverb, massive space)",
            value="deep",
        ),
        Choice(
            title="⚙️  Custom Manual Settings...",
            value="custom",
        ),
    ]

    choice = questionary.select(
        "Select Audio Profile:",
        choices=choices,
        style=questionary.Style([
            ("qmark", "fg:#00ffff bold"),
            ("question", "bold"),
            ("selected", "fg:#00ffaa bold"),
            ("pointer", "fg:#00ffff bold"),
        ]),
    ).ask()

    if choice == "auto":
        return auto_params
    elif choice == "dreamy":
        return {"speed": 0.82, "wet_level": 0.42, "room_size": 0.70, "damping": 0.45}
    elif choice == "nightdrive":
        return {"speed": 0.86, "wet_level": 0.30, "room_size": 0.55, "damping": 0.60}
    elif choice == "deep":
        return {"speed": 0.78, "wet_level": 0.50, "room_size": 0.80, "damping": 0.40}
    elif choice == "custom":
        speed_str = questionary.text("Enter speed factor (e.g. 0.85):", default="0.85").ask()
        reverb_str = questionary.text("Enter reverb level 0.0 - 1.0 (e.g. 0.35):", default="0.35").ask()
        room_str = questionary.text("Enter room size 0.0 - 1.0 (e.g. 0.60):", default="0.60").ask()
        return {
            "speed": float(speed_str),
            "wet_level": float(reverb_str),
            "room_size": float(room_str),
            "damping": 0.50,
        }
    return auto_params


def run():
    print_banner()

    while True:
        query = questionary.text(
            "Search YouTube (or paste URL / type 'q' to quit):",
            style=questionary.Style([
                ("qmark", "fg:#00ffff bold"),
                ("question", "bold"),
            ]),
        ).ask()

        if not query or query.strip().lower() in ["q", "quit", "exit"]:
            console.print("[dim]Goodbye![/dim]")
            sys.exit(0)

        query = query.strip()
        selected_url = None

        # Check if query is a direct URL
        if query.startswith("http://") or query.startswith("https://") or "youtube.com" in query or "youtu.be" in query:
            selected_url = query
        else:
            results = search_youtube_with_thumbnails(query, max_results=5)
            if not results:
                console.print("[yellow]No results found. Try a different search term.[/yellow]\n")
                continue

            # Render visual cards with clean thumbnails
            display_search_cards(results)

            choices = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "Untitled")
                channel = r.get("uploader", "Unknown Channel")
                dur = format_duration(r.get("duration"))
                choices.append(Choice(
                    title=f"[{i}] {title} ({channel} • {dur})",
                    value=r.get("url") or r.get("webpage_url") or r.get("id"),
                ))

            choices.append(Choice(title="🔍 Search again...", value="search_again"))
            choices.append(Choice(title="❌ Cancel", value="cancel"))

            selection = questionary.select(
                "Pick a song to convert:",
                choices=choices,
                style=questionary.Style([
                    ("qmark", "fg:#00ffff bold"),
                    ("question", "bold"),
                    ("selected", "fg:#00ffaa bold"),
                    ("pointer", "fg:#00ffff bold"),
                ]),
            ).ask()

            if not selection or selection == "cancel":
                continue
            if selection == "search_again":
                continue

            selected_url = selection
            if not selected_url.startswith("http"):
                selected_url = f"https://www.youtube.com/watch?v={selected_url}"

        # Work session
        session_id = f"job_{os.getpid()}"
        temp_prefix = TMP_DIR / session_id

        try:
            # 1. Download
            with console.status("[bold cyan]⏬ Fetching highest quality audio stream & artwork...", spinner="aesthetic"):
                data = download_audio_and_metadata(selected_url, temp_prefix)

            track_title = data["title"]
            track_artist = data["uploader"]
            wav_path = data["wav_path"]
            thumb_path = data["thumbnail_path"]

            console.print(f"\n[bold green]✓ Downloaded:[/bold green] [bold white]{track_title}[/bold white] by [cyan]{track_artist}[/cyan]")

            # 2. Audio Analysis
            auto_params = analyze_audio(wav_path)

            # 3. Parameter Selection
            dsp_settings = select_preset_or_custom(auto_params)

            # 4. Processing
            processed_wav = temp_prefix.with_name(f"{session_id}_processed.wav")
            with console.status("[bold cyan]🎛️ Processing audio with 32-bit float Studio DSP...", spinner="bouncingBar"):
                process_dsp(
                    input_wav=wav_path,
                    output_wav=processed_wav,
                    speed=dsp_settings["speed"],
                    room_size=dsp_settings["room_size"],
                    damping=dsp_settings["damping"],
                    wet_level=dsp_settings["wet_level"],
                )

            # 5. Export MP3 with embedded Cover Artwork
            clean_title = sanitize_filename(track_title)
            output_filename = f"{clean_title} (Slowed + Reverb).mp3"
            final_mp3 = OUTPUT_DIR / output_filename

            with console.status("[bold green]💾 Exporting 320kbps MP3 with ID3 tags & artwork...", spinner="dots"):
                export_mp3(
                    processed_wav=processed_wav,
                    output_mp3=final_mp3,
                    title=track_title,
                    artist=track_artist,
                    thumbnail_path=thumb_path,
                )

            # Success message
            table = Table(show_header=False, border_style="green", padding=(0, 2))
            table.add_row("Track", track_title)
            table.add_row("Artist", track_artist)
            table.add_row("Settings", f"Speed: {dsp_settings['speed']}x | Reverb: {int(dsp_settings['wet_level']*100)}% | Room: {dsp_settings['room_size']}")
            table.add_row("Format", "MP3 (320 kbps CBR)")
            table.add_row("Cover Art", "Embedded (High Quality)")
            table.add_row("Location", str(final_mp3))

            console.print(Panel(table, title="[bold green]✨ Conversion Complete! ✨[/bold green]", border_style="green"))

        except Exception as e:
            console.print(f"[bold red]❌ An error occurred:[/bold red] {e}")
        finally:
            # Cleanup temporary session files
            for p in TMP_DIR.glob(f"{session_id}*"):
                try:
                    if p.is_file():
                        p.unlink()
                except Exception:
                    pass

        console.print("\n" + "─" * 60 + "\n")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        console.print("\n[dim]Process interrupted. Exiting...[/dim]")
        sys.exit(0)
