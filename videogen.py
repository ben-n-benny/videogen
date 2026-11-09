#!/usr/bin/env python3
"""
VideoGen: High-Retention 9:16 1080p (1080x1920) FFmpeg Short Video Creation Engine
Designed for History, Documentary, and Commentary Shorts (TikTok / Reels / YouTube Shorts).

High-Retention Engineering Features:
1. 3-Second Scroll-Stopper Hook Engine:
   - Instant `0.0s` cold open (automatic voiceover leading/trailing silence stripping)
   - Animated Hook Headline Banner (`hook_headline`) with scale-punch entrance in the first 2.8s
   - Opening exposure flash + whip-zoom + sub-bass boom (`builtin:boom`) at `t=0.0s`
2. Visual Pattern Interrupts (Every ~3 Seconds):
   - Multi-media B-roll arrays per scene (`"media": ["img1.png", "img2.png"]`)
   - Automatic Mid-Scene Jump-Cut Punch-In (`1.18x` instant zoom + flash + subtle SFX) on scenes > 4.0s
   - Camera shake (`shake_zoom`) & 2x-supersampled jitter-free Ken Burns motion
3. Semantic Power-Word Captions (`libass`):
   - Fast 3-to-4 word chunks synced to voiceover cadence
   - Automatic semantic coloring & scale pop:
     * Numbers / Dates / Stats -> Electric Cyan / Gold (`118%` pop)
     * Power / Shock / Conflict Words -> Fiery Crimson (`120%` pop)
     * Active Spoken Word -> Bright Gold (`112%` pop) over slightly dimmed context words
4. Broadcast Audio & Built-In Procedural SFX Engine:
   - Voiceover presence EQ + compression + configurable `vo_speed` (`atempo`)
   - Built-in procedural SFX (`builtin:boom`, `builtin:whoosh`, `builtin:riser`, `builtin:shutter`, `builtin:tick`, `builtin:hit`)
   - Background music with automatic sidechain ducking under voiceover
5. Retention Progress Bar & Seamless Loop Pacing:
   - Animated progress bar overlay and tight zero-dead-air transitions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Semantic Power Words & Theme Presets
# ---------------------------------------------------------------------------

POWER_DANGER_WORDS = {
    "WAR", "WARS", "EXPLODED", "ERUPTION", "ERUPTED", "FROZE", "FROZEN", "DIED",
    "DEATH", "DEAD", "KILL", "KILLED", "SHATTERING", "SHATTERED", "DESTROYED",
    "BLIZZARD", "BLIZZARDS", "SNOW", "FIRE", "BLOOD", "NEVER", "FRANKENSTEIN",
    "SHORTEST", "LARGEST", "FASTEST", "SECRET", "DARK", "STORMS", "BOMBARDMENT",
    "COUP", "SEIZED", "COLLAPSED", "EXTINCTION", "APOCALYPSE", "NIGHTMARE",
    "IMPOSSIBLE", "SHOCKING", "FOREVER", "CATASTROPHE", "VOLCANO", "VOLCANIC",
}

THEME_PRESETS: Dict[str, Dict[str, Any]] = {
    "history": {
        "default_fit": "blur_pad",
        "default_effect": "auto",
        "default_grade": "vintage",
        "vignette": True,
        "transition": "fadeblack",
        "transition_duration": 0.28,
        "retention": {
            "enabled": True,
            "trim_vo_silence": True,
            "vo_speed": 1.0,
            "vo_eq_boost": True,
            "hook_flash": True,
            "hook_banner_duration": 2.8,
            "auto_pattern_interrupt": True,
            "pattern_interrupt_threshold": 4.2,
            "progress_bar": True,
            "progress_bar_color": "#FFD700",
            "loop_ending": True,
        },
        "caption_style": {
            "font_name": "Impact",
            "font_size": 80,
            "primary_color": "#E8E8E8",
            "highlight_color": "#FFD700",      # Gold active word
            "power_color": "#FF3B30",          # Fiery crimson for conflict/shock words
            "number_color": "#00F0FF",         # Cyan pop for years/numbers/dates
            "outline_color": "#000000",
            "back_color": "#80000000",
            "outline": 6,
            "shadow": 4,
            "margin_v": 350,
            "uppercase": True,
            "mode": "word_highlight",
            "semantic_colors": True,
            "max_words_per_chunk": 3,
        },
        "badge_style": {
            "font_name": "Georgia",
            "font_size": 40,
            "primary_color": "#F5E6C8",
            "outline_color": "#000000",
            "back_color": "#C814100C",
            "outline": 3,
            "margin_v": 135,
        },
        "hook_style": {
            "font_name": "Impact",
            "font_size": 70,
            "primary_color": "#FFFFFF",
            "accent_color": "#FFD700",
            "box_color": "#D8101095",          # Deep crimson banner box (ASS BBGGRR)
            "margin_v": 235,
        },
    },
    "commentary": {
        "default_fit": "blur_pad",
        "default_effect": "auto",
        "default_grade": "cinematic",
        "vignette": False,
        "transition": "cut",
        "transition_duration": 0.20,
        "retention": {
            "enabled": True,
            "trim_vo_silence": True,
            "vo_speed": 1.0,
            "vo_eq_boost": True,
            "hook_flash": True,
            "hook_banner_duration": 2.6,
            "auto_pattern_interrupt": True,
            "pattern_interrupt_threshold": 3.8,
            "progress_bar": True,
            "progress_bar_color": "#00FF88",
            "loop_ending": True,
        },
        "caption_style": {
            "font_name": "Arial Black",
            "font_size": 80,
            "primary_color": "#EAEAEA",
            "highlight_color": "#00FF88",
            "power_color": "#FF2E54",
            "number_color": "#FFE600",
            "outline_color": "#000000",
            "back_color": "#80000000",
            "outline": 6,
            "shadow": 4,
            "margin_v": 360,
            "uppercase": True,
            "mode": "word_highlight",
            "semantic_colors": True,
            "max_words_per_chunk": 3,
        },
        "badge_style": {
            "font_name": "Arial",
            "font_size": 40,
            "primary_color": "#FFFFFF",
            "outline_color": "#000000",
            "back_color": "#B4000000",
            "outline": 3,
            "margin_v": 135,
        },
        "hook_style": {
            "font_name": "Impact",
            "font_size": 72,
            "primary_color": "#FFFFFF",
            "accent_color": "#00FF88",
            "box_color": "#D8000000",
            "margin_v": 235,
        },
    },
    "documentary": {
        "default_fit": "cover",
        "default_effect": "auto",
        "default_grade": "cinematic",
        "vignette": True,
        "transition": "dissolve",
        "transition_duration": 0.32,
        "retention": {
            "enabled": True,
            "trim_vo_silence": True,
            "vo_speed": 1.0,
            "vo_eq_boost": True,
            "hook_flash": True,
            "hook_banner_duration": 2.8,
            "auto_pattern_interrupt": True,
            "pattern_interrupt_threshold": 4.5,
            "progress_bar": True,
            "progress_bar_color": "#FFE066",
            "loop_ending": True,
        },
        "caption_style": {
            "font_name": "Trebuchet MS",
            "font_size": 68,
            "primary_color": "#F0F0F0",
            "highlight_color": "#FFE066",
            "power_color": "#FF5544",
            "number_color": "#55E6FF",
            "outline_color": "#000000",
            "back_color": "#96000000",
            "outline": 5,
            "shadow": 3,
            "margin_v": 320,
            "uppercase": False,
            "mode": "word_highlight",
            "semantic_colors": True,
            "max_words_per_chunk": 4,
        },
        "badge_style": {
            "font_name": "Trebuchet MS",
            "font_size": 40,
            "primary_color": "#FFD700",
            "outline_color": "#000000",
            "back_color": "#B4000000",
            "outline": 3,
            "margin_v": 135,
        },
        "hook_style": {
            "font_name": "Trebuchet MS",
            "font_size": 64,
            "primary_color": "#FFFFFF",
            "accent_color": "#FFE066",
            "box_color": "#D8101010",
            "margin_v": 235,
        },
    },
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}

KEN_BURNS_CYCLE = [
    "zoom_in",
    "pan_right",
    "zoom_out",
    "pan_left",
    "zoom_in_top",
    "pan_down",
]

XFADE_TRANSITIONS = {
    "fade": "fade",
    "fadeblack": "fadeblack",
    "fadewhite": "fadewhite",
    "dissolve": "dissolve",
    "wipeleft": "wipeleft",
    "wiperight": "wiperight",
    "wipeup": "wipeup",
    "wipedown": "wipedown",
    "slideleft": "slideleft",
    "slideright": "slideright",
    "slideup": "slideup",
    "slidedown": "slidedown",
    "smoothleft": "smoothleft",
    "smoothright": "smoothright",
    "circleopen": "circleopen",
    "circleclose": "circleclose",
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class CaptionEvent:
    start: float
    end: float
    text: str
    style: str = "Default"
    layer: int = 0


@dataclass
class AudioEvent:
    path: Path
    start_time: float
    volume: float


@dataclass
class ResolvedScene:
    index: int
    scene_id: str
    raw: Dict[str, Any]
    media_paths: List[Path]
    is_image_list: List[bool]
    fit_mode: str
    effect: str
    grade: str
    vignette: bool
    darken: float
    voiceover_path: Optional[Path]
    voiceover_duration: float
    pad_before: float
    pad_after: float
    clip_duration: float      # Total visual duration of this scene clip (D_i)
    start_time: float         # Global start time in final video (S_i)
    end_time: float           # Global end time in final video (S_i + D_i)
    voiceover_start: float    # Global start time when voiceover begins
    transition_in: str        # Transition from previous scene into this scene
    transition_duration: float
    sfx_events: List[AudioEvent]
    badge_text: Optional[str]
    hook_flash: bool
    pattern_interrupt: bool
    interrupt_offset: float   # Seconds into the scene where mid-scene jump-cut happens
    rendered_clip_path: Optional[Path] = None


# ---------------------------------------------------------------------------
# Utilities, Built-in SFX Synth, & Voiceover Optimizer
# ---------------------------------------------------------------------------

def run_cmd(cmd: List[str], cwd: Optional[Path] = None, desc: str = "") -> subprocess.CompletedProcess:
    """Execute a subprocess command and raise a clear error if it fails."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        err_tail = "\n".join(result.stderr.splitlines()[-25:])
        raise RuntimeError(
            f"Command failed ({desc or cmd[0]}):\n"
            f"Command: {' '.join(cmd)}\n"
            f"Error output:\n{err_tail}"
        )
    return result


def probe_duration(path: Path) -> float:
    """Return exact media duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    res = run_cmd(cmd, desc=f"ffprobe duration on {path.name}")
    val = res.stdout.strip()
    if not val or val == "N/A":
        raise ValueError(f"Could not determine duration for media file: {path}")
    return float(val)


def ensure_builtin_sfx(name: str, cache_dir: Path) -> Path:
    """
    Generate procedural retention sound effects on demand using FFmpeg lavfi.
    Supported names:
      - builtin:boom     (Deep cinematic sub-bass impact for hooks & twists)
      - builtin:whoosh   (Crisp transition air whoosh)
      - builtin:riser    (Tension pitch riser before a reveal)
      - builtin:shutter  (Crisp archival cut / jump-cut click)
      - builtin:tick     (Subtle clock tick for mid-scene pattern interrupts)
      - builtin:hit      (Dramatic mid-frequency percussive hit)
    """
    clean = name.replace("builtin:", "").strip().lower()
    out_wav = cache_dir / f"sfx_builtin_{clean}.wav"
    if out_wav.exists():
        return out_wav

    if clean == "boom":
        # Sub-bass pitch drop + warm punch
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.75*sin(2*PI*(85*exp(-2.2*t)+34)*t)*exp(-2.2*t)+0.25*random(0)*exp(-14*t)':s=48000:d=1.1",
            "-af", "lowpass=f=190,afade=t=in:st=0:d=0.01,afade=t=out:st=0.6:d=0.5",
            str(out_wav),
        ]
    elif clean == "riser":
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.35*sin(2*PI*(120+480*t*t)*t)*(t/0.75)':s=48000:d=0.75",
            "-af", "bandpass=f=600:width_type=h:w=500,afade=t=in:st=0:d=0.25,afade=t=out:st=0.62:d=0.13",
            str(out_wav),
        ]
    elif clean == "shutter":
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "anoisesrc=d=0.14:c=white:r=48000:a=0.45",
            "-af", "bandpass=f=1800:width_type=h:w=1200,afade=t=in:st=0:d=0.005,afade=t=out:st=0.03:d=0.11",
            str(out_wav),
        ]
    elif clean == "tick":
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.45*sin(2*PI*1150*t)*exp(-45*t)':s=48000:d=0.09",
            str(out_wav),
        ]
    elif clean == "hit":
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.65*sin(2*PI*110*t)*exp(-6*t)+0.35*random(0)*exp(-18*t)':s=48000:d=0.55",
            "-af", "lowpass=f=650,afade=t=out:st=0.25:d=0.30",
            str(out_wav),
        ]
    else:  # default "whoosh"
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "anoisesrc=d=0.32:c=pink:r=48000:a=0.42",
            "-af", "bandpass=f=580:width_type=h:w=420,afade=t=in:st=0:d=0.10,afade=t=out:st=0.14:d=0.18",
            str(out_wav),
        ]

    run_cmd(cmd, desc=f"Synthesize builtin SFX '{clean}'")
    return out_wav


NEURAL_VOICE_PRESETS: Dict[str, str] = {
    "christopher": "en-US-ChristopherNeural",       # Deep, authoritative documentary narrator
    "andrew": "en-US-AndrewMultilingualNeural",     # Ultra-natural warm human storyteller
    "brian": "en-US-BrianMultilingualNeural",       # Crisp, conversational commentary voice
    "eric": "en-US-EricNeural",                     # Grounded narrative voice
    "guy": "en-US-GuyNeural",                       # Engaging American male narrator
    "ryan": "en-GB-RyanNeural",                     # British BBC-style documentary narrator
    "aria": "en-US-AriaNeural",                     # Expressive female narrator
}


def optimize_voiceover_audio(
    src_audio: Path,
    cache_dir: Path,
    trim_silence: bool = True,
    vo_speed: float = 1.0,
    eq_boost: bool = True,
    force: bool = False,
) -> Path:
    """
    Process a scene voiceover for natural human studio warmth & high retention:
    - Strip only leading/trailing dead air (`silenceremove`) while preserving natural mid-sentence breaths
    - Apply studio broadcast condenser-mic EQ (75Hz highpass, 135Hz chest warmth, 950Hz de-box, 3.6kHz presence)
    - Add subtle studio room reflection (`aecho`) and optical-style dynamic leveling
    """
    stat = src_audio.stat()
    sig = f"{src_audio.resolve()}_{stat.st_mtime_ns}_{stat.st_size}_{trim_silence}_{vo_speed:.3f}_{eq_boost}_v2"
    h = hashlib.md5(sig.encode("utf-8")).hexdigest()[:12]
    out_wav = cache_dir / f"vo_opt_{src_audio.stem}_{h}.wav"
    if out_wav.exists() and not force:
        return out_wav

    af_chain: List[str] = ["aresample=48000"]
    if trim_silence:
        af_chain.append("silenceremove=start_periods=1:start_duration=0.01:start_threshold=-46dB")
        af_chain.append("areverse")
        af_chain.append("silenceremove=start_periods=1:start_duration=0.02:start_threshold=-46dB")
        af_chain.append("areverse")

    if abs(vo_speed - 1.0) > 0.005:
        clamped_speed = max(0.80, min(1.35, vo_speed))
        af_chain.append(f"atempo={clamped_speed:.3f}")

    if eq_boost:
        af_chain.append("highpass=f=75")
        af_chain.append("equalizer=f=135:t=q:w=1.1:g=2.4")
        af_chain.append("equalizer=f=950:t=q:w=1.5:g=-1.2")
        af_chain.append("equalizer=f=3600:t=q:w=1.0:g=1.8")
        af_chain.append("aecho=0.8:0.88:12:0.05")
        af_chain.append("acompressor=threshold=-18dB:ratio=2.2:attack=18:release=180:makeup=1.4")

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src_audio),
        "-af", ",".join(af_chain),
        "-c:a", "pcm_s16le", "-ar", "48000",
        str(out_wav),
    ]
    run_cmd(cmd, desc=f"Optimize voiceover {src_audio.name}")
    return out_wav


def hex_to_ass_color(hex_str: str) -> str:
    """Convert #RRGGBB or #AARRGGBB hex string to ASS color format &HAABBGGRR."""
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 6:
        r, g, b = clean[0:2], clean[2:4], clean[4:6]
        return f"&H00{b}{g}{r}".upper()
    elif len(clean) == 8:
        a, r, g, b = clean[0:2], clean[2:4], clean[4:6], clean[6:8]
        return f"&H{a}{b}{g}{r}".upper()
    raise ValueError(f"Invalid hex color '{hex_str}'. Use #RRGGBB or #AARRGGBB.")


def format_ass_time(seconds: float) -> str:
    """Format seconds as ASS timestamp H:MM:SS.cc (centiseconds)."""
    seconds = max(0.0, seconds)
    total_cs = int(round(seconds * 100))
    cs = total_cs % 100
    total_sec = total_cs // 100
    s = total_sec % 60
    total_min = total_sec // 60
    m = total_min % 60
    h = total_min // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def escape_ass_text(text: str) -> str:
    """Escape special characters for ASS dialogue lines."""
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def synthesize_tts_fallback(
    text: str,
    out_wav: Path,
    voice_rate: int = 1,
    voice_name: str = "christopher",
    pitch: str = "-2Hz",
) -> Path:
    """
    Synthesize realistic human neural voiceover audio using `edge-tts` (Microsoft Azure
    Neural Voices like `en-US-ChristopherNeural` and `en-US-AndrewMultilingualNeural`).
    Falls back to offline Windows System.Speech only if neural synthesis is unavailable.
    """
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    resolved_voice = NEURAL_VOICE_PRESETS.get(voice_name.lower(), voice_name)
    rate_pct = f"+{max(0, int(voice_rate) * 4)}%" if int(voice_rate) >= 0 else f"{int(voice_rate) * 4}%"

    try:
        import asyncio
        import edge_tts

        tmp_mp3 = out_wav.with_suffix(".neural_tmp.mp3")

        async def _run_edge() -> None:
            comm = edge_tts.Communicate(text=text, voice=resolved_voice, rate=rate_pct, pitch=pitch)
            await comm.save(str(tmp_mp3))

        asyncio.run(_run_edge())
        if tmp_mp3.exists() and tmp_mp3.stat().st_size > 256:
            run_cmd(
                [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(tmp_mp3),
                    "-c:a", "pcm_s16le", "-ar", "48000",
                    str(out_wav),
                ],
                desc=f"Convert neural TTS {tmp_mp3.name} to 48kHz WAV",
            )
            tmp_mp3.unlink(missing_ok=True)
            return out_wav
    except Exception as exc:
        print(f"  [TTS Notice] edge-tts unavailable ({exc}), falling back to Windows System.Speech.")

    escaped_text = text.replace("'", "''").replace('"', '`"')
    escaped_out = str(out_wav.resolve()).replace("'", "''")
    ps_script = (
        "Add-Type -AssemblyName System.Speech; "
        "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$synth.Rate = {int(voice_rate)}; "
        f"$synth.SetOutputToWaveFile('{escaped_out}'); "
        f"$synth.Speak('{escaped_text}'); "
        "$synth.Dispose();"
    )
    run_cmd(
        ["powershell", "-NoProfile", "-Command", ps_script],
        desc=f"Synthesize TTS for '{text[:30]}...'",
    )
    return out_wav


# ---------------------------------------------------------------------------
# High-Retention Caption & Hook Banner Generator (ASS / libass)
# ---------------------------------------------------------------------------

def classify_word_highlight(
    word: str,
    caption_style: Dict[str, Any],
) -> Tuple[str, int]:
    """
    Determine the highlight ASS color and scale percentage for an active spoken word:
    - Numbers / Years / Times (e.g. "1816", "38", "9:00") -> `number_color` (#00F0FF) @ 118%
    - Power / Conflict / Shock words (e.g. "EXPLODED", "WAR", "FROZE") -> `power_color` (#FF3B30) @ 120%
    - Standard active word -> `highlight_color` (#FFD700) @ 112%
    """
    hi_default = hex_to_ass_color(caption_style.get("highlight_color", "#FFD700"))
    if not caption_style.get("semantic_colors", True):
        return hi_default, 112

    clean_upper = re.sub(r"[^\w]", "", word).upper()
    has_digit = any(ch.isdigit() for ch in clean_upper)
    if has_digit:
        num_col = hex_to_ass_color(caption_style.get("number_color", "#00F0FF"))
        return num_col, 118

    # Also check hyphenated sub-tokens (e.g., "38-MINUTE", "BLOOD-RED")
    tokens = {re.sub(r"[^\w]", "", t).upper() for t in word.split("-")}
    tokens.add(clean_upper)
    if tokens & POWER_DANGER_WORDS:
        pow_col = hex_to_ass_color(caption_style.get("power_color", "#FF3B30"))
        return pow_col, 120

    return hi_default, 112


def split_text_into_chunks(text: str, max_words: int = 3) -> List[List[str]]:
    """
    Split text into fast-paced short-form chunks (default 3 words max),
    breaking naturally on punctuation so phrases feel punchy and rhythmic.
    """
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    if not words:
        return []

    chunks: List[List[str]] = []
    current: List[str] = []

    for w in words:
        current.append(w)
        ends_punct = bool(re.search(r"[,.;:!?—\-]$", w))
        if len(current) >= max_words or (ends_punct and len(current) >= 2):
            chunks.append(current)
            current = []

    if current:
        chunks.append(current)
    return chunks


def word_weight(word: str) -> float:
    """Estimate relative spoken duration weight of a word based on length and punctuation pauses."""
    clean = re.sub(r"[^\w]", "", word)
    base = max(2.2, float(len(clean)))
    if re.search(r"[.!?]$", word):
        base += 3.2
    elif re.search(r"[,;:—\-]$", word):
        base += 1.8
    return base


def build_scene_caption_events(
    scene_raw: Dict[str, Any],
    caption_start: float,
    caption_end: float,
    caption_style: Dict[str, Any],
) -> List[CaptionEvent]:
    """Generate high-retention ASS CaptionEvents for a single scene."""
    events: List[CaptionEvent] = []
    uppercase = bool(caption_style.get("uppercase", True))
    mode = caption_style.get("mode", "word_highlight")
    max_words = int(caption_style.get("max_words_per_chunk", 3))
    pri_color = hex_to_ass_color(caption_style.get("primary_color", "#E8E8E8"))

    explicit_captions = scene_raw.get("captions")
    if isinstance(explicit_captions, list) and explicit_captions:
        for item in explicit_captions:
            if isinstance(item, dict) and item.get("text"):
                rel_s = float(item.get("start", 0.0))
                rel_e = float(item.get("end", max(rel_s + 0.5, caption_end - caption_start)))
                raw_txt = str(item["text"]).strip()
                if uppercase:
                    raw_txt = raw_txt.upper()
                escaped = escape_ass_text(raw_txt)
                styled_txt = r"{\fad(45,45)\fscx114\fscy114\t(0,75,\fscx100\fscy100)}" + escaped
                events.append(
                    CaptionEvent(
                        start=caption_start + rel_s,
                        end=min(caption_end + 0.15, caption_start + rel_e),
                        text=styled_txt,
                        style="Default",
                        layer=2,
                    )
                )
        return events

    caption_text = scene_raw.get("caption")
    if caption_text is None:
        caption_text = scene_raw.get("voiceover_text", "")
    caption_text = str(caption_text).strip()
    if not caption_text:
        return events

    chunks = split_text_into_chunks(caption_text, max_words=max_words)
    if not chunks:
        return events

    total_duration = max(0.2, caption_end - caption_start)
    all_weights = [sum(word_weight(w) for w in chunk) for chunk in chunks]
    total_weight = sum(all_weights) or 1.0

    cursor = caption_start
    for chunk, c_weight in zip(chunks, all_weights):
        chunk_dur = total_duration * (c_weight / total_weight)
        chunk_start = cursor
        chunk_end = cursor + chunk_dur
        cursor = chunk_end

        display_words = [w.upper() if uppercase else w for w in chunk]

        if mode == "word_highlight":
            w_weights = [word_weight(w) for w in chunk]
            w_total = sum(w_weights) or 1.0
            w_cursor = chunk_start
            for idx, w_weight in enumerate(w_weights):
                w_dur = chunk_dur * (w_weight / w_total)
                w_start = w_cursor
                w_end = w_cursor + w_dur
                w_cursor = w_end

                parts: List[str] = []
                for j, word_str in enumerate(display_words):
                    esc_w = escape_ass_text(word_str)
                    if j == idx:
                        active_col, scale_pct = classify_word_highlight(word_str, caption_style)
                        # Pop active word from scale_pct down to 108% over 80ms
                        parts.append(
                            f"{{\\1c{active_col}\\fscx{scale_pct}\\fscy{scale_pct}"
                            f"\\t(0,80,\\fscx108\\fscy108)}}{esc_w}{{\\1c{pri_color}\\fscx100\\fscy100}}"
                        )
                    else:
                        parts.append(esc_w)

                if len(parts) >= 3 and sum(len(w) for w in display_words) > 14:
                    mid = (len(parts) + 1) // 2
                    line_str = " ".join(parts[:mid]) + r"\N" + " ".join(parts[mid:])
                else:
                    line_str = " ".join(parts)

                # Slight chunk entrance pop on the very first word of each chunk
                prefix = r"{\fscx105\fscy105\t(0,65,\fscx100\fscy100)}" if idx == 0 else ""
                events.append(
                    CaptionEvent(
                        start=w_start,
                        end=w_end,
                        text=prefix + line_str,
                        style="Default",
                        layer=2,
                    )
                )
        else:
            escaped_words = [escape_ass_text(w) for w in display_words]
            if len(escaped_words) >= 4:
                mid = len(escaped_words) // 2
                line_str = " ".join(escaped_words[:mid]) + r"\N" + " ".join(escaped_words[mid:])
            else:
                line_str = " ".join(escaped_words)

            styled = r"{\fad(50,50)\fscx110\fscy110\t(0,85,\fscx100\fscy100)}" + line_str
            events.append(
                CaptionEvent(
                    start=chunk_start,
                    end=chunk_end,
                    text=styled,
                    style="Default",
                    layer=2,
                )
            )

    return events


def parse_srt_file(srt_path: Path, uppercase: bool = False) -> List[CaptionEvent]:
    """Parse an external .srt file into CaptionEvents."""
    content = srt_path.read_text(encoding="utf-8-sig", errors="replace")
    blocks = re.split(r"\n\s*\n", content.strip())
    events: List[CaptionEvent] = []
    time_re = re.compile(
        r"(\d+):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d+):(\d{2}):(\d{2})[,.](\d{3})"
    )

    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        m = time_re.search(lines[0])
        text_lines = lines[1:]
        if not m and len(lines) >= 3:
            m = time_re.search(lines[1])
            text_lines = lines[2:]
        if not m:
            continue

        s_h, s_m, s_s, s_ms, e_h, e_m, e_s, e_ms = [int(x) for x in m.groups()]
        start = s_h * 3600 + s_m * 60 + s_s + s_ms / 1000.0
        end = e_h * 3600 + e_m * 60 + e_s + e_ms / 1000.0
        raw_txt = " ".join(text_lines)
        raw_txt = re.sub(r"<[^>]+>", "", raw_txt)
        if uppercase:
            raw_txt = raw_txt.upper()
        escaped = escape_ass_text(raw_txt)
        styled = r"{\fad(50,50)\fscx108\fscy108\t(0,80,\fscx100\fscy100)}" + escaped
        events.append(CaptionEvent(start=start, end=end, text=styled, style="Default", layer=2))

    return events


def write_ass_file(
    ass_path: Path,
    width: int,
    height: int,
    caption_style: Dict[str, Any],
    badge_style: Dict[str, Any],
    hook_style: Dict[str, Any],
    events: List[CaptionEvent],
) -> None:
    """Write a complete ASS subtitle script with Default, Badge, and HookBanner styles."""
    font_name = caption_style.get("font_name", "Impact")
    font_size = int(caption_style.get("font_size", 80))
    pri_col = hex_to_ass_color(caption_style.get("primary_color", "#E8E8E8"))
    sec_col = hex_to_ass_color(caption_style.get("highlight_color", "#FFD700"))
    out_col = hex_to_ass_color(caption_style.get("outline_color", "#000000"))
    back_col = hex_to_ass_color(caption_style.get("back_color", "#80000000"))
    outline = int(caption_style.get("outline", 6))
    shadow = int(caption_style.get("shadow", 4))
    margin_v = int(caption_style.get("margin_v", 350))
    alignment = int(caption_style.get("alignment", 2))

    b_font = badge_style.get("font_name", "Georgia")
    b_size = int(badge_style.get("font_size", 40))
    b_pri = hex_to_ass_color(badge_style.get("primary_color", "#F5E6C8"))
    b_out = hex_to_ass_color(badge_style.get("outline_color", "#000000"))
    b_back = hex_to_ass_color(badge_style.get("back_color", "#C814100C"))
    b_outline = int(badge_style.get("outline", 3))
    b_margin_v = int(badge_style.get("margin_v", 135))

    h_font = hook_style.get("font_name", "Impact")
    h_size = int(hook_style.get("font_size", 70))
    h_pri = hex_to_ass_color(hook_style.get("primary_color", "#FFFFFF"))
    h_acc = hex_to_ass_color(hook_style.get("accent_color", "#FFD700"))
    h_box = hex_to_ass_color(hook_style.get("box_color", "#D8101095"))
    h_margin_v = int(hook_style.get("margin_v", 235))

    header = f"""[Script Info]
Title: VideoGen High-Retention 9x16 Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{pri_col},{sec_col},{out_col},{back_col},-1,0,0,0,100,100,1,0,1,{outline},{shadow},{alignment},75,75,{margin_v},1
Style: Badge,{b_font},{b_size},{b_pri},{b_pri},{b_out},{b_back},-1,0,0,0,100,100,2,0,3,{b_outline},0,8,70,70,{b_margin_v},1
Style: HookBanner,{h_font},{h_size},{h_pri},{h_acc},{h_box},{h_box},-1,0,0,0,100,100,2,0,3,14,0,8,65,65,{h_margin_v},1
Style: Callout,Consolas,34,&H00FFE680,&H00FFE680,&H0018120A,&HC818120A,-1,0,0,0,100,100,1,0,3,10,0,7,0,0,0,1
Style: ProgressBar,Arial,20,&H0000D7FF,&H0000D7FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [header.rstrip()]
    for ev in sorted(events, key=lambda e: (e.start, e.layer)):
        if ev.end <= ev.start:
            continue
        s_str = format_ass_time(ev.start)
        e_str = format_ass_time(ev.end)
        lines.append(f"Dialogue: {ev.layer},{s_str},{e_str},{ev.style},,0,0,0,,{ev.text}")

    ass_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Visual Filter, Pattern Interrupts, & Scene Renderer
# ---------------------------------------------------------------------------

def build_color_grade_filter(grade: str, vignette: bool, darken: float) -> str:
    """Return FFmpeg video filter chain for color grading, brightness adjustment, and vignette."""
    filters: List[str] = []
    grade = (grade or "none").lower()

    if grade in ("vintage", "history"):
        filters.append("eq=contrast=1.10:saturation=0.82:brightness=-0.01")
        filters.append("colorbalance=rs=0.06:gs=0.01:bs=-0.05:rm=0.04:gm=0.01:bm=-0.04")
    elif grade == "sepia":
        filters.append("colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131")
        filters.append("eq=contrast=1.08:brightness=-0.01")
    elif grade in ("bw", "blackandwhite", "noir"):
        filters.append("hue=s=0")
        filters.append("eq=contrast=1.20:brightness=-0.01")
    elif grade in ("cinematic", "commentary"):
        filters.append("eq=contrast=1.12:saturation=1.15:brightness=-0.01")
        filters.append("colorbalance=rs=-0.03:bs=0.04:rh=0.04:bh=-0.02")

    if abs(darken) > 1e-4:
        filters.append(f"eq=brightness={-abs(darken):.3f}")

    if vignette:
        filters.append("vignette=PI/5.5")

    return ",".join(filters)


def build_ken_burns_zoompan(
    effect: str,
    frames: int,
    width: int,
    height: int,
    fps: int,
    hook_flash: bool = False,
    interrupt_frame: int = 0,
) -> str:
    """
    Build a 2x-supersampled FFmpeg `zoompan` filter string with optional:
    - `hook_flash` whip-zoom + camera shake in the first 10 frames (0.33s)
    - `interrupt_frame` mid-scene instant 1.16x Jump-Cut Punch-In pattern interrupt!
    """
    n = max(2, frames)
    effect = (effect or "zoom_in").lower()

    # Mid-scene jump-cut multiplier: steps up by +15% zoom at `interrupt_frame`
    if interrupt_frame > 0:
        punch_mult = f"*if(gte(on,{interrupt_frame}),1.15,1.0)"
    else:
        punch_mult = ""

    # Opening hook whip-zoom boost in the first 9 frames
    if hook_flash:
        hook_boost = "+0.22*exp(-on/3.2)"
        shake_x = "+16*sin(on*2.1)*exp(-on/4.5)"
        shake_y = "+12*cos(on*2.5)*exp(-on/4.5)"
    else:
        hook_boost = ""
        shake_x = ""
        shake_y = ""

    if effect == "zoom_in":
        base_z = f"(1.0+0.16*(on/{n}){hook_boost}){punch_mult}"
        x_expr = f"iw/2-(iw/zoom/2){shake_x}"
        y_expr = f"ih/2-(ih/zoom/2){shake_y}"
    elif effect == "zoom_in_top":
        base_z = f"(1.0+0.16*(on/{n}){hook_boost}){punch_mult}"
        x_expr = f"iw/2-(iw/zoom/2){shake_x}"
        y_expr = f"ih/3.2-(ih/zoom/3.2){shake_y}"
    elif effect == "zoom_out":
        base_z = f"(1.18-0.16*(on/{n}){hook_boost}){punch_mult}"
        x_expr = f"iw/2-(iw/zoom/2){shake_x}"
        y_expr = f"ih/2-(ih/zoom/2){shake_y}"
    elif effect == "pan_right":
        base_z = f"(1.15{hook_boost}){punch_mult}"
        x_expr = f"(iw-iw/zoom)*(on/{n}){shake_x}"
        y_expr = f"ih/2-(ih/zoom/2){shake_y}"
    elif effect == "pan_left":
        base_z = f"(1.15{hook_boost}){punch_mult}"
        x_expr = f"(iw-iw/zoom)*(1-on/{n}){shake_x}"
        y_expr = f"ih/2-(ih/zoom/2){shake_y}"
    elif effect == "pan_down":
        base_z = f"(1.15{hook_boost}){punch_mult}"
        x_expr = f"iw/2-(iw/zoom/2){shake_x}"
        y_expr = f"(ih-ih/zoom)*(on/{n}){shake_y}"
    elif effect == "pan_up":
        base_z = f"(1.15{hook_boost}){punch_mult}"
        x_expr = f"iw/2-(iw/zoom/2){shake_x}"
        y_expr = f"(ih-ih/zoom)*(1-on/{n}){shake_y}"
    elif effect == "shake_zoom":
        base_z = f"(1.04+0.16*(on/{n}){hook_boost}){punch_mult}"
        x_expr = f"iw/2-(iw/zoom/2)+18*sin(on*1.9)*exp(-on/12)"
        y_expr = f"ih/2-(ih/zoom/2)+14*cos(on*2.3)*exp(-on/12)"
    else:
        base_z = f"(1.0{hook_boost}){punch_mult}"
        x_expr = f"iw/2-(iw/zoom/2){shake_x}"
        y_expr = f"ih/2-(ih/zoom/2){shake_y}"

    return f"zoompan=z='{base_z}':x='{x_expr}':y='{y_expr}':d={frames}:s={width}x{height}:fps={fps}"


def prepare_still_canvas(
    image_path: Path,
    canvas_path: Path,
    width: int,
    height: int,
    fit_mode: str,
) -> Path:
    """Pre-render a 2x-supersampled (2160x3840) 9:16 composite frame from a still image."""
    up_w = width * 2
    up_h = height * 2

    if fit_mode == "blur_pad":
        fg_w = int(up_w * 0.94) // 2 * 2
        fg_h = int(up_h * 0.86) // 2 * 2
        vf = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={up_w}:{up_h}:force_original_aspect_ratio=increase,"
            f"crop={up_w}:{up_h},boxblur=60:4,eq=brightness=-0.08:saturation=0.90[bg_out];"
            f"[fg]scale={fg_w}:{fg_h}:force_original_aspect_ratio=decrease,"
            f"scale='trunc(iw/2)*2':'trunc(ih/2)*2',"
            f"pad='iw+12':'ih+12':6:6:color=0xFFFFFF30[fg_out];"
            f"[bg_out][fg_out]overlay=(W-w)/2:(H-h)/2,setsar=1"
        )
    elif fit_mode == "contain":
        vf = (
            f"[0:v]scale={up_w}:{up_h}:force_original_aspect_ratio=decrease,"
            f"pad={up_w}:{up_h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
        )
    else:  # "cover"
        vf = (
            f"[0:v]scale={up_w}:{up_h}:force_original_aspect_ratio=increase,"
            f"crop={up_w}:{up_h},setsar=1"
        )

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(image_path),
        "-filter_complex", vf,
        "-frames:v", "1",
        str(canvas_path),
    ]
    run_cmd(cmd, desc=f"Prepare 9:16 canvas for {image_path.name}")
    return canvas_path


def render_single_segment(
    media_path: Path,
    is_image: bool,
    seg_duration: float,
    fit_mode: str,
    effect: str,
    grade: str,
    vignette: bool,
    darken: float,
    hook_flash: bool,
    interrupt_offset: float,
    trim_start: float,
    width: int,
    height: int,
    fps: int,
    out_clip: Path,
    cache_dir: Path,
    force_rebuild: bool = False,
) -> Path:
    """Render an individual visual segment (either a whole scene or one B-roll sub-cut)."""
    frames = max(2, int(round(seg_duration * fps)))
    interrupt_frame = int(round(interrupt_offset * fps)) if interrupt_offset > 0 else 0
    grade_chain = build_color_grade_filter(grade, vignette, darken)

    # Exposure flash filter for hook open or mid-scene jump-cut pattern interrupt
    flash_filters: List[str] = []
    if hook_flash:
        flash_filters.append("eq=brightness='0.32*exp(-t*9)':eval=frame")
    if interrupt_offset > 0:
        flash_filters.append(
            f"eq=brightness='if(between(t,{interrupt_offset:.3f},{interrupt_offset+0.14:.3f}),0.18,0)':eval=frame"
        )

    if is_image:
        stat = media_path.stat()
        c_hash = hashlib.md5(
            f"{media_path.resolve()}_{stat.st_mtime_ns}_{width}_{height}_{fit_mode}".encode("utf-8")
        ).hexdigest()[:12]
        canvas_path = cache_dir / f"canvas_{media_path.stem}_{c_hash}.jpg"
        if not canvas_path.exists() or force_rebuild:
            prepare_still_canvas(media_path, canvas_path, width, height, fit_mode)

        zp_filter = build_ken_burns_zoompan(
            effect=effect,
            frames=frames,
            width=width,
            height=height,
            fps=fps,
            hook_flash=hook_flash,
            interrupt_frame=interrupt_frame,
        )
        vf_parts = [zp_filter, "setsar=1"]
        if grade_chain:
            vf_parts.append(grade_chain)
        vf_parts.extend(flash_filters)
        vf_parts.append("format=yuv420p")

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(canvas_path),
            "-vf", ",".join(vf_parts),
            "-t", f"{seg_duration:.4f}",
            "-r", str(fps),
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            str(out_clip),
        ]
        run_cmd(cmd, desc=f"Render image segment {media_path.name}")
    else:
        if fit_mode == "blur_pad":
            fg_w = int(width * 0.94) // 2 * 2
            fg_h = int(height * 0.86) // 2 * 2
            base_graph = (
                f"[0:v]split=2[bg][fg];"
                f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},boxblur=35:3,eq=brightness=-0.08:saturation=0.90[bg_out];"
                f"[fg]scale={fg_w}:{fg_h}:force_original_aspect_ratio=decrease,"
                f"scale='trunc(iw/2)*2':'trunc(ih/2)*2'[fg_out];"
                f"[bg_out][fg_out]overlay=(W-w)/2:(H-h)/2,fps={fps},setsar=1"
            )
        elif fit_mode == "contain":
            base_graph = (
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,fps={fps},setsar=1"
            )
        else:
            base_graph = (
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},fps={fps},setsar=1"
            )

        if grade_chain:
            base_graph += f",{grade_chain}"
        for ff in flash_filters:
            base_graph += f",{ff}"
        base_graph += ",format=yuv420p[vout]"

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-stream_loop", "-1",
        ]
        if trim_start > 0:
            cmd += ["-ss", f"{trim_start:.3f}"]
        cmd += [
            "-i", str(media_path),
            "-filter_complex", base_graph,
            "-map", "[vout]",
            "-t", f"{seg_duration:.4f}",
            "-r", str(fps),
            "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            str(out_clip),
        ]
        run_cmd(cmd, desc=f"Render video segment {media_path.name}")

    return out_clip


def render_scene_clip(
    scene: ResolvedScene,
    width: int,
    height: int,
    fps: int,
    cache_dir: Path,
    force_rebuild: bool = False,
) -> Path:
    """
    Render a scene clip (supporting either a single media asset with optional mid-scene
    jump-cut pattern interrupt, OR an array of B-roll media assets cut rapidly within the scene).
    """
    media_sigs = [
        f"{p.resolve()}:{p.stat().st_mtime_ns}:{p.stat().st_size}" for p in scene.media_paths
    ]
    sig_data = {
        "media": media_sigs,
        "fit_mode": scene.fit_mode,
        "effect": scene.effect,
        "grade": scene.grade,
        "vignette": scene.vignette,
        "darken": round(scene.darken, 4),
        "duration": round(scene.clip_duration, 4),
        "hook_flash": scene.hook_flash,
        "pattern_interrupt": scene.pattern_interrupt,
        "interrupt_offset": round(scene.interrupt_offset, 4),
        "width": width,
        "height": height,
        "fps": fps,
        "trim_start": scene.raw.get("trim_start", 0.0),
    }
    sig_hash = hashlib.sha256(json.dumps(sig_data, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    out_clip = cache_dir / f"scene_{scene.index:03d}_{sig_hash}.mp4"

    if out_clip.exists() and not force_rebuild:
        scene.rendered_clip_path = out_clip
        return out_clip

    if len(scene.media_paths) == 1:
        render_single_segment(
            media_path=scene.media_paths[0],
            is_image=scene.is_image_list[0],
            seg_duration=scene.clip_duration,
            fit_mode=scene.fit_mode,
            effect=scene.effect,
            grade=scene.grade,
            vignette=scene.vignette,
            darken=scene.darken,
            hook_flash=scene.hook_flash,
            interrupt_offset=scene.interrupt_offset if scene.pattern_interrupt else 0.0,
            trim_start=float(scene.raw.get("trim_start", 0.0)),
            width=width,
            height=height,
            fps=fps,
            out_clip=out_clip,
            cache_dir=cache_dir,
            force_rebuild=force_rebuild,
        )
    else:
        # Multi-B-roll sub-cuts inside a single voiceover scene
        num_sub = len(scene.media_paths)
        sub_dur = scene.clip_duration / num_sub
        sub_clips: List[Path] = []
        for k, (m_path, is_img) in enumerate(zip(scene.media_paths, scene.is_image_list)):
            sub_out = cache_dir / f"scene_{scene.index:03d}_sub{k}_{sig_hash}.mp4"
            sub_eff = KEN_BURNS_CYCLE[(scene.index + k) % len(KEN_BURNS_CYCLE)] if scene.effect == "auto" else scene.effect
            render_single_segment(
                media_path=m_path,
                is_image=is_img,
                seg_duration=sub_dur,
                fit_mode=scene.fit_mode,
                effect=sub_eff,
                grade=scene.grade,
                vignette=scene.vignette,
                darken=scene.darken,
                hook_flash=(scene.hook_flash and k == 0),
                interrupt_offset=0.0,
                trim_start=0.0,
                width=width,
                height=height,
                fps=fps,
                out_clip=sub_out,
                cache_dir=cache_dir,
                force_rebuild=force_rebuild,
            )
            sub_clips.append(sub_out)

        concat_list = cache_dir / f"sub_concat_{scene.index:03d}.txt"
        concat_list.write_text(
            "\n".join(f"file '{p.resolve().as_posix()}'" for p in sub_clips) + "\n",
            encoding="utf-8",
        )
        run_cmd(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-c", "copy",
                str(out_clip),
            ],
            desc=f"Concat B-roll sub-cuts for scene {scene.index}",
        )

    scene.rendered_clip_path = out_clip
    return out_clip


# ---------------------------------------------------------------------------
# Master Pipeline Orchestrator
# ---------------------------------------------------------------------------

class VideoProjectBuilder:
    def __init__(self, manifest_path: Path, force_rebuild: bool = False):
        self.manifest_path = manifest_path.resolve()
        self.project_dir = self.manifest_path.parent
        self.force_rebuild = force_rebuild

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.config: Dict[str, Any] = json.load(f)

        self.title = self.config.get("title", self.project_dir.name)
        self.theme_name = self.config.get("theme", "history").lower()
        self.theme = json.loads(json.dumps(THEME_PRESETS.get(self.theme_name, THEME_PRESETS["history"])))

        # Merge user style & retention overrides
        for section in ("caption_style", "badge_style", "hook_style", "retention"):
            if section in self.config and isinstance(self.config[section], dict):
                self.theme[section].update(self.config[section])

        self.retention = self.theme["retention"]
        res = self.config.get("resolution", [1080, 1920])
        self.width = int(res[0])
        self.height = int(res[1])
        self.fps = int(self.config.get("fps", 30))

        out_rel = self.config.get("output", "output/final_short.mp4")
        self.output_path = self._resolve_path(out_rel)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        self.work_dir = self.project_dir / ".videogen_cache"
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, p: str | Path) -> Path:
        path = Path(p)
        if path.is_absolute():
            return path
        candidate = (self.project_dir / path).resolve()
        if candidate.exists():
            return candidate
        ws_candidate = Path.cwd() / path
        if ws_candidate.exists():
            return ws_candidate.resolve()
        return candidate

    def _resolve_sfx(self, sfx_spec: str) -> Path:
        if sfx_spec.startswith("builtin:"):
            return ensure_builtin_sfx(sfx_spec, self.work_dir)
        path = self._resolve_path(sfx_spec)
        if not path.exists():
            raise FileNotFoundError(f"SFX file not found: {path}")
        return path

    def resolve_timeline(self) -> Tuple[List[ResolvedScene], float]:
        """
        Inspect all scenes, optimize/trim voiceovers for zero dead air, configure visual
        pattern interrupts, and compute exact global timestamps [S_i, S_i + D_i].
        """
        raw_scenes = self.config.get("scenes", [])
        if not raw_scenes:
            raise ValueError("Project manifest must contain a non-empty 'scenes' array.")

        ret_enabled = bool(self.retention.get("enabled", True))
        trim_silence = ret_enabled and bool(self.retention.get("trim_vo_silence", True))
        vo_speed = float(self.retention.get("vo_speed", 1.05)) if ret_enabled else 1.0
        vo_eq = ret_enabled and bool(self.retention.get("vo_eq_boost", True))

        default_fit = self.config.get("default_fit", self.theme["default_fit"])
        default_effect = self.config.get("default_effect", self.theme["default_effect"])
        default_grade = self.config.get("default_grade", self.theme["default_grade"])
        default_vignette = bool(self.config.get("vignette", self.theme["vignette"]))
        default_trans = self.config.get("transition", self.theme["transition"])
        default_trans_dur = float(self.config.get("transition_duration", self.theme["transition_duration"]))

        preliminary: List[Dict[str, Any]] = []
        for idx, s_raw in enumerate(raw_scenes):
            scene_id = str(s_raw.get("id", f"scene_{idx+1:02d}"))
            media_spec = s_raw.get("media") or s_raw.get("image") or s_raw.get("video")
            if not media_spec:
                raise ValueError(f"Scene #{idx+1} ('{scene_id}') is missing 'media' path.")

            media_list_raw = media_spec if isinstance(media_spec, list) else [media_spec]
            media_paths: List[Path] = []
            is_image_list: List[bool] = []
            for m_str in media_list_raw:
                mp = self._resolve_path(m_str)
                if not mp.exists():
                    raise FileNotFoundError(f"Scene #{idx+1} ('{scene_id}') media file not found: {mp}")
                ext = mp.suffix.lower()
                is_img = ext in IMAGE_EXTENSIONS
                if not is_img and ext not in VIDEO_EXTENSIONS:
                    raise ValueError(f"Unsupported media file extension '{ext}' in scene '{scene_id}'.")
                media_paths.append(mp)
                is_image_list.append(is_img)

            # Resolve & optimize voiceover
            raw_vo_path: Optional[Path] = None
            if s_raw.get("voiceover"):
                raw_vo_path = self._resolve_path(s_raw["voiceover"])
                if not raw_vo_path.exists():
                    raise FileNotFoundError(f"Scene #{idx+1} ('{scene_id}') voiceover not found: {raw_vo_path}")
            elif s_raw.get("voiceover_text") and bool(self.config.get("auto_tts", True)):
                tts_text = str(s_raw["voiceover_text"]).strip()
                if tts_text:
                    v_name = str(s_raw.get("tts_voice", self.config.get("tts_voice", "christopher")))
                    v_pitch = str(s_raw.get("tts_pitch", self.config.get("tts_pitch", "-2Hz")))
                    txt_hash = hashlib.md5(f"{tts_text}_{v_name}_{v_pitch}".encode("utf-8")).hexdigest()[:10]
                    tts_wav = self.work_dir / f"tts_{idx:03d}_{txt_hash}.wav"
                    if not tts_wav.exists() or self.force_rebuild:
                        synthesize_tts_fallback(
                            tts_text,
                            tts_wav,
                            voice_rate=int(self.config.get("tts_rate", 1)),
                            voice_name=v_name,
                            pitch=v_pitch,
                        )
                    raw_vo_path = tts_wav

            vo_path: Optional[Path] = None
            vo_dur = 0.0
            scene_speed = float(s_raw.get("vo_speed", vo_speed))
            if raw_vo_path:
                if ret_enabled or abs(scene_speed - 1.0) > 0.005:
                    vo_path = optimize_voiceover_audio(
                        raw_vo_path,
                        self.work_dir,
                        trim_silence=trim_silence,
                        vo_speed=scene_speed,
                        eq_boost=vo_eq,
                        force=self.force_rebuild,
                    )
                else:
                    vo_path = raw_vo_path
                vo_dur = probe_duration(vo_path)

            # Tighter padding for high retention (instant cold open on scene 0)
            default_pad_before = 0.03 if idx == 0 else 0.06
            default_pad_after = 0.10 if (idx == len(raw_scenes) - 1 and self.retention.get("loop_ending", True)) else 0.14
            pad_before = float(s_raw.get("pad_before", default_pad_before))
            pad_after = float(s_raw.get("pad_after", default_pad_after))

            explicit_dur = s_raw.get("duration")
            if explicit_dur is not None and explicit_dur != "auto":
                base_dur = max(float(explicit_dur), vo_dur + pad_before + pad_after)
            elif vo_dur > 0:
                base_dur = vo_dur + pad_before + pad_after
            elif not is_image_list[0]:
                base_dur = probe_duration(media_paths[0])
            else:
                base_dur = 3.5

            trans_in = str(s_raw.get("transition", default_trans if idx > 0 else "cut")).lower()
            if idx == 0:
                trans_in = "cut"
            trans_dur = float(s_raw.get("transition_duration", default_trans_dur)) if trans_in != "cut" else 0.0

            preliminary.append({
                "idx": idx,
                "scene_id": scene_id,
                "raw": s_raw,
                "media_paths": media_paths,
                "is_image_list": is_image_list,
                "vo_path": vo_path,
                "vo_dur": vo_dur,
                "pad_before": pad_before,
                "pad_after": pad_after,
                "base_dur": base_dur,
                "trans_in": trans_in,
                "trans_dur": trans_dur,
            })

        resolved: List[ResolvedScene] = []
        cursor = 0.0
        auto_pi = ret_enabled and bool(self.retention.get("auto_pattern_interrupt", True))
        pi_thresh = float(self.retention.get("pattern_interrupt_threshold", 4.2))

        for i, item in enumerate(preliminary):
            s_raw = item["raw"]
            next_trans_dur = preliminary[i + 1]["trans_dur"] if (i + 1 < len(preliminary)) else 0.0
            clip_duration = item["base_dur"] + next_trans_dur

            start_time = cursor
            end_time = start_time + clip_duration
            vo_start = start_time + item["pad_before"]

            fit_mode = str(s_raw.get("fit", default_fit)).lower()
            effect = str(s_raw.get("effect", default_effect)).lower()
            if effect == "auto":
                effect = KEN_BURNS_CYCLE[i % len(KEN_BURNS_CYCLE)]

            grade = str(s_raw.get("grade", default_grade)).lower()
            vignette = bool(s_raw.get("vignette", default_vignette))
            darken = float(s_raw.get("darken", 0.04))

            # Hook flash on Scene 0 (or if explicitly requested)
            hook_flash = bool(
                s_raw.get("hook_flash", (i == 0 and ret_enabled and self.retention.get("hook_flash", True)))
            )

            # Mid-scene pattern interrupt (instant 1.15x jump-cut punch-in at 50% of scene)
            has_single_still = len(item["media_paths"]) == 1 and item["is_image_list"][0]
            pattern_interrupt = bool(
                s_raw.get("pattern_interrupt", auto_pi and has_single_still and item["base_dur"] >= pi_thresh)
            )
            interrupt_offset = round(item["base_dur"] * 0.50, 3) if pattern_interrupt else 0.0

            # Collect scene SFX + retention SFX (opening hook boom, transition whoosh, mid-scene jump-cut click)
            sfx_events: List[AudioEvent] = []
            if hook_flash and i == 0 and not s_raw.get("sfx"):
                sfx_events.append(
                    AudioEvent(
                        path=self._resolve_sfx("builtin:boom"),
                        start_time=0.0,
                        volume=0.38,
                    )
                )

            if s_raw.get("sfx"):
                sfx_events.append(
                    AudioEvent(
                        path=self._resolve_sfx(str(s_raw["sfx"])),
                        start_time=start_time,
                        volume=float(s_raw.get("sfx_volume", 0.35)),
                    )
                )
            elif i > 0 and ret_enabled:
                # Subtle automatic transition whoosh on scene changes when no explicit SFX was supplied
                sfx_events.append(
                    AudioEvent(
                        path=self._resolve_sfx("builtin:whoosh"),
                        start_time=start_time,
                        volume=0.20,
                    )
                )

            if pattern_interrupt and ret_enabled:
                sfx_events.append(
                    AudioEvent(
                        path=self._resolve_sfx("builtin:shutter"),
                        start_time=start_time + interrupt_offset,
                        volume=0.18,
                    )
                )

            badge_text = s_raw.get("badge") or s_raw.get("header")

            resolved.append(
                ResolvedScene(
                    index=i,
                    scene_id=item["scene_id"],
                    raw=s_raw,
                    media_paths=item["media_paths"],
                    is_image_list=item["is_image_list"],
                    fit_mode=fit_mode,
                    effect=effect,
                    grade=grade,
                    vignette=vignette,
                    darken=darken,
                    voiceover_path=item["vo_path"],
                    voiceover_duration=item["vo_dur"],
                    pad_before=item["pad_before"],
                    pad_after=item["pad_after"],
                    clip_duration=clip_duration,
                    start_time=start_time,
                    end_time=end_time,
                    voiceover_start=vo_start,
                    transition_in=item["trans_in"],
                    transition_duration=item["trans_dur"],
                    sfx_events=sfx_events,
                    badge_text=str(badge_text).strip() if badge_text else None,
                    hook_flash=hook_flash,
                    pattern_interrupt=pattern_interrupt,
                    interrupt_offset=interrupt_offset,
                )
            )

            cursor = start_time + item["base_dur"]

        total_duration = resolved[-1].end_time if resolved else 0.0

        if self.config.get("global_voiceover"):
            g_vo = self._resolve_path(self.config["global_voiceover"])
            if g_vo.exists():
                g_dur = probe_duration(g_vo) + 0.25
                if g_dur > total_duration and resolved:
                    extra = g_dur - total_duration
                    resolved[-1].clip_duration += extra
                    resolved[-1].end_time += extra
                    total_duration = g_dur

        return resolved, total_duration

    def _build_scene_motion_graphics_events(
        self,
        sc: ResolvedScene,
        default_overlay_fx: str = "embers",
    ) -> List[CaptionEvent]:
        """
        Generate real-time vector motion graphics (`libass` \\move, \\p1, \\blur) for a scene:
        - `overlay_fx`:
            * "embers": Rising glowing orange/gold embers & atmospheric dust motes
            * "snow" / "ash": Falling snow/ash flakes with horizontal wind drift
            * "radar_hud": Animated sonar/radar sweep rings, corner reticle brackets, and scan line
            * "blueprint_hud": Technical schematic corner ticks, cyan scan bar, and pulsing nodes
        - `callout`: Animated lower/side telemetry or historical stat card sliding onto screen
        """
        events: List[CaptionEvent] = []
        width, height = self.width, self.height
        fx = str(sc.raw.get("overlay_fx", default_overlay_fx)).strip().lower()
        s_start = sc.start_time
        s_end = sc.end_time
        dur = max(0.5, s_end - s_start)

        seed_val = (sc.index + 1) * 9173
        def _rand(idx: int) -> float:
            x = math.sin(seed_val + idx * 12.9898) * 43758.5453
            return x - math.floor(x)

        if fx in ("embers", "sparks"):
            num_particles = 28
            for p in range(num_particles):
                p_dur = 2.4 + _rand(p * 3) * 2.2
                t0 = s_start + (_rand(p * 3 + 1) * max(0.1, dur - 0.8))
                t1 = min(s_end, t0 + p_dur)
                if t1 - t0 < 0.4:
                    continue
                x0 = int(60 + _rand(p * 5) * (width - 120))
                y0 = int(height * (0.45 + _rand(p * 7) * 0.50))
                x1 = x0 + int((_rand(p * 11) - 0.45) * 180)
                y1 = max(80, y0 - int(220 + _rand(p * 13) * 340))
                sz = int(6 + _rand(p * 17) * 8)
                col = "&H0045FF&" if p % 2 == 0 else "&H00A5FF&"
                draw_str = (
                    f"{{\\an7\\move({x0},{y0},{x1},{y1})\\fad(300,450)\\1c{col}\\3c{col}"
                    f"\\1a&H35&\\3a&H70&\\bord4\\blur5\\shad0\\p1}}"
                    f"m 0 0 l {sz} 0 {sz} {sz} 0 {sz}{{\\p0}}"
                )
                events.append(CaptionEvent(start=t0, end=t1, text=draw_str, style="ProgressBar", layer=1))

        elif fx in ("snow", "ash"):
            num_particles = 32
            for p in range(num_particles):
                p_dur = 2.6 + _rand(p * 3) * 2.0
                t0 = s_start + (_rand(p * 3 + 1) * max(0.1, dur - 0.8))
                t1 = min(s_end, t0 + p_dur)
                if t1 - t0 < 0.4:
                    continue
                x0 = int(40 + _rand(p * 5) * (width - 80))
                y0 = int(height * (_rand(p * 7) * 0.65))
                x1 = x0 - int(60 + _rand(p * 11) * 140)
                y1 = min(height - 60, y0 + int(260 + _rand(p * 13) * 360))
                sz = int(6 + _rand(p * 17) * 7)
                col = "&HFFF5E8&" if fx == "snow" else "&HC8D2DC&"
                draw_str = (
                    f"{{\\an7\\move({x0},{y0},{x1},{y1})\\fad(250,350)\\1c{col}"
                    f"\\1a&H45&\\bord0\\blur3\\shad0\\p1}}"
                    f"m 0 0 l {sz} 0 {sz} {sz} 0 {sz}{{\\p0}}"
                )
                events.append(CaptionEvent(start=t0, end=t1, text=draw_str, style="ProgressBar", layer=1))

        elif fx in ("radar_hud", "blueprint_hud"):
            hud_col = "&H88FF00&" if fx == "radar_hud" else "&HFFF000&"
            scan_cursor = s_start + 0.1
            while scan_cursor < s_end - 0.5:
                scan_end = min(s_end, scan_cursor + 2.4)
                scan_line = (
                    f"{{\\an7\\move(60,260,60,{height - 360})\\fad(200,250)\\1c{hud_col}\\1a&H85&\\bord2\\3c{hud_col}\\3a&HB0&\\blur3\\p1}}"
                    f"m 0 0 l {width - 120} 0 {width - 120} 3 0 3{{\\p0}}"
                )
                events.append(CaptionEvent(start=scan_cursor, end=scan_end, text=scan_line, style="ProgressBar", layer=1))
                scan_cursor += 2.6

            tl_bracket = (
                f"{{\\an7\\move(25,205,48,225,0,220)\\fad(150,200)\\1c{hud_col}\\1a&H30&\\bord0\\shad0\\p1}}"
                f"m 0 0 l 65 0 65 5 5 5 5 65 0 65{{\\p0}}"
            )
            br_bracket = (
                f"{{\\an7\\move({width-25},{height-225},{width-113},{height-290},0,220)\\fad(150,200)\\1c{hud_col}\\1a&H30&\\bord0\\shad0\\p1}}"
                f"m 60 0 l 65 0 65 65 0 65 0 60 60 60{{\\p0}}"
            )
            events.append(CaptionEvent(start=s_start + 0.05, end=s_end - 0.05, text=tl_bracket, style="ProgressBar", layer=1))
            events.append(CaptionEvent(start=s_start + 0.05, end=s_end - 0.05, text=br_bracket, style="ProgressBar", layer=1))

            pulse_cursor = s_start + 0.2
            cx, cy = width // 2, int(height * 0.46)
            while pulse_cursor < s_end - 0.6:
                p_end = min(s_end, pulse_cursor + 1.35)
                reticle = (
                    f"{{\\an5\\pos({cx},{cy})\\fad(80,450)\\1a&HFF&\\3c{hud_col}\\3a&H55&\\bord3\\blur1"
                    f"\\fscx70\\fscy70\\t(0,1200,\\fscx155\\fscy155)\\p1}}"
                    f"m -70 -70 l 70 -70 70 70 -70 70{{\\p0}}"
                )
                events.append(CaptionEvent(start=pulse_cursor, end=p_end, text=reticle, style="ProgressBar", layer=1))
                pulse_cursor += 1.45

        callout_txt = sc.raw.get("callout")
        if callout_txt:
            c_start = s_start + 0.35
            c_end = max(c_start + 1.0, s_end - 0.30)
            esc_c = escape_ass_text(str(callout_txt).strip().upper())
            cy_pos = height - 610
            callout_line = (
                f"{{\\an7\\move(-320,{cy_pos},68,{cy_pos},0,220)\\fad(80,180)}}"
                f"  ▸ {esc_c}  "
            )
            events.append(CaptionEvent(start=c_start, end=c_end, text=callout_line, style="Callout", layer=3))

        return events

    def generate_subtitles(
        self,
        scenes: List[ResolvedScene],
        ass_path: Path,
        total_duration: float,
    ) -> Path:
        """Build the master ASS subtitle file with semantic captions, badges, Hook Banner, and animated ProgressBar."""
        events: List[CaptionEvent] = []
        cap_style = self.theme["caption_style"]
        default_fx = str(self.config.get("default_overlay_fx", "embers"))

        # Add per-scene moving graphics & telemetry callouts
        for sc in scenes:
            events.extend(self._build_scene_motion_graphics_events(sc, default_overlay_fx=default_fx))

        if self.config.get("subtitles_file"):
            srt_path = self._resolve_path(self.config["subtitles_file"])
            if not srt_path.exists():
                raise FileNotFoundError(f"Subtitles file not found: {srt_path}")
            events.extend(parse_srt_file(srt_path, uppercase=bool(cap_style.get("uppercase", True))))
        else:
            for sc in scenes:
                if sc.voiceover_duration > 0:
                    c_start = sc.voiceover_start
                    c_end = sc.voiceover_start + sc.voiceover_duration
                else:
                    c_start = sc.start_time + sc.pad_before
                    c_end = sc.end_time - sc.pad_after - (
                        scenes[sc.index + 1].transition_duration if sc.index + 1 < len(scenes) else 0.0
                    )
                events.extend(build_scene_caption_events(sc.raw, c_start, c_end, cap_style))

        # Top historical/commentary badges
        for sc in scenes:
            if sc.badge_text:
                b_start = sc.start_time + 0.05
                b_end = sc.end_time - (
                    scenes[sc.index + 1].transition_duration if sc.index + 1 < len(scenes) else 0.05
                )
                esc_badge = escape_ass_text(sc.badge_text.upper())
                styled_badge = r"{\fad(120,120)}" + f"  {esc_badge}  "
                events.append(
                    CaptionEvent(
                        start=b_start,
                        end=b_end,
                        text=styled_badge,
                        style="Badge",
                        layer=3,
                    )
                )

        # 3-Second Scroll-Stopper Hook Banner (`hook_headline` or derived from project title)
        if bool(self.retention.get("enabled", True)):
            hook_headline = (
                self.config.get("hook_headline")
                or (scenes[0].raw.get("hook_headline") if scenes else None)
                or self.title
            )
            if hook_headline:
                hook_dur = min(
                    float(self.retention.get("hook_banner_duration", 2.8)),
                    scenes[0].end_time - 0.2 if scenes else 2.8,
                )
                esc_hook = escape_ass_text(str(hook_headline).strip().upper())
                styled_hook = (
                    r"{\fad(0,180)\fscx130\fscy130\t(0,130,\fscx100\fscy100)}"
                    + f"  {esc_hook}  "
                )
                events.append(
                    CaptionEvent(
                        start=0.0,
                        end=hook_dur,
                        text=styled_hook,
                        style="HookBanner",
                        layer=4,
                    )
                )

            # Animated Vector Retention Progress Bar along bottom edge
            if bool(self.retention.get("progress_bar", True)) and total_duration > 0:
                pb_col = hex_to_ass_color(str(self.retention.get("progress_bar_color", "#FFD700")))
                bar_h = 14
                bar_y = self.height - bar_h
                # Dark track bar + sliding active progress bar from x=-width to x=0
                track_draw = (
                    f"{{\\an7\\pos(0,{bar_y})\\1c&H000000&\\1a&H60&\\bord0\\shad0\\p1}}"
                    f"m 0 0 l {self.width} 0 {self.width} {bar_h} 0 {bar_h}{{\\p0}}"
                )
                fill_draw = (
                    f"{{\\an7\\move({-self.width},{bar_y},0,{bar_y})\\1c{pb_col}\\bord0\\shad0\\p1}}"
                    f"m 0 0 l {self.width} 0 {self.width} {bar_h} 0 {bar_h}{{\\p0}}"
                )
                events.append(
                    CaptionEvent(start=0.0, end=total_duration, text=track_draw, style="ProgressBar", layer=5)
                )
                events.append(
                    CaptionEvent(start=0.0, end=total_duration, text=fill_draw, style="ProgressBar", layer=6)
                )

        write_ass_file(
            ass_path=ass_path,
            width=self.width,
            height=self.height,
            caption_style=cap_style,
            badge_style=self.theme["badge_style"],
            hook_style=self.theme["hook_style"],
            events=events,
        )
        return ass_path

    def build_master_audio(
        self,
        scenes: List[ResolvedScene],
        total_duration: float,
        out_audio: Path,
    ) -> Path:
        """Assemble master stereo 48kHz audio track with voiceovers, retention SFX, and ducked BGM."""
        inputs: List[str] = [
            "-f", "lavfi", "-t", f"{total_duration:.4f}", "-i", "anullsrc=r=48000:cl=stereo"
        ]
        vo_labels: List[str] = ["[0:a]"]
        sfx_labels: List[str] = []
        input_idx = 1

        if self.config.get("global_voiceover"):
            g_vo = self._resolve_path(self.config["global_voiceover"])
            inputs += ["-i", str(g_vo)]
            vo_labels.append(f"[{input_idx}:a]")
            input_idx += 1

        filter_parts: List[str] = []
        for sc in scenes:
            if sc.voiceover_path and sc.voiceover_duration > 0:
                delay_ms = max(0, int(round(sc.voiceover_start * 1000)))
                inputs += ["-i", str(sc.voiceover_path)]
                lbl = f"[vo_{sc.index}]"
                vo_vol = float(sc.raw.get("voiceover_volume", 1.0))
                filter_parts.append(
                    f"[{input_idx}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                    f"volume={vo_vol:.3f},adelay={delay_ms}|{delay_ms}{lbl}"
                )
                vo_labels.append(lbl)
                input_idx += 1

            for sfx_idx, ev in enumerate(sc.sfx_events):
                sfx_delay_ms = max(0, int(round(ev.start_time * 1000)))
                inputs += ["-i", str(ev.path)]
                lbl = f"[sfx_{sc.index}_{sfx_idx}]"
                filter_parts.append(
                    f"[{input_idx}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                    f"volume={ev.volume:.3f},adelay={sfx_delay_ms}|{sfx_delay_ms}{lbl}"
                )
                sfx_labels.append(lbl)
                input_idx += 1

        filter_parts.append(
            f"{''.join(vo_labels)}amix=inputs={len(vo_labels)}:duration=first:dropout_transition=0:normalize=0,"
            f"alimiter=limit=0.95[vo_bus]"
        )

        mix_buses = ["[vo_bus]"]

        if sfx_labels:
            filter_parts.append(
                f"{''.join(sfx_labels)}amix=inputs={len(sfx_labels)}:duration=longest:dropout_transition=0:normalize=0[sfx_bus]"
            )
            mix_buses.append("[sfx_bus]")

        bgm_cfg = self.config.get("background_music")
        if bgm_cfg:
            if isinstance(bgm_cfg, str):
                bgm_path = self._resolve_path(bgm_cfg)
                bgm_vol = float(self.config.get("bgm_volume", 0.15))
                bgm_duck = True
            else:
                bgm_path = self._resolve_path(bgm_cfg["path"])
                bgm_vol = float(bgm_cfg.get("volume", 0.15))
                bgm_duck = bool(bgm_cfg.get("ducking", True))

            if not bgm_path.exists():
                raise FileNotFoundError(f"Background music file not found: {bgm_path}")

            inputs += ["-stream_loop", "-1", "-i", str(bgm_path)]
            fade_out_start = max(0.0, total_duration - 1.2)
            bgm_chain = (
                f"[{input_idx}:a]atrim=0:{total_duration:.4f},asetpts=PTS-STARTPTS,"
                f"aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                f"volume={bgm_vol:.3f},"
                f"afade=t=in:st=0:d=0.4,afade=t=out:st={fade_out_start:.4f}:d=1.2"
            )
            if bgm_duck and len(vo_labels) > 1:
                filter_parts[-1 if not sfx_labels else -2] = filter_parts[-1 if not sfx_labels else -2].replace(
                    "[vo_bus]", "[vo_raw]"
                )
                filter_parts.append("[vo_raw]asplit=2[vo_bus][vo_sc]")
                filter_parts.append(f"{bgm_chain}[bgm_pre]")
                filter_parts.append(
                    "[bgm_pre][vo_sc]sidechaincompress=threshold=0.025:ratio=4:attack=30:release=300[bgm_bus]"
                )
            else:
                filter_parts.append(f"{bgm_chain}[bgm_bus]")
            mix_buses.append("[bgm_bus]")

        if len(mix_buses) == 1:
            filter_parts.append(f"{mix_buses[0]}atrim=0:{total_duration:.4f}[aout]")
        else:
            filter_parts.append(
                f"{''.join(mix_buses)}amix=inputs={len(mix_buses)}:duration=first:dropout_transition=0:normalize=0,"
                f"alimiter=limit=0.96,atrim=0:{total_duration:.4f}[aout]"
            )

        filter_complex = ";".join(filter_parts)
        cmd = (
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
            + inputs
            + [
                "-filter_complex", filter_complex,
                "-map", "[aout]",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                str(out_audio),
            ]
        )
        run_cmd(cmd, desc="Assemble master audio track")
        return out_audio

    def stitch_and_render(
        self,
        scenes: List[ResolvedScene],
        ass_path: Path,
        master_audio: Path,
        total_duration: float,
    ) -> Path:
        """
        Combine all rendered scene clips with transitions, burn in the styled `.ass` subtitles,
        render the animated retention progress bar, and mux into the final 1080x1920 MP4.
        """
        local_ass = self.work_dir / "captions.ass"
        if ass_path.resolve() != local_ass.resolve():
            shutil.copyfile(ass_path, local_ass)
        rel_ass = local_ass.relative_to(self.project_dir).as_posix()

        post_vf = f"ass={rel_ass},format=yuv420p"

        has_xfade = any(sc.transition_in != "cut" and sc.transition_duration > 0 for sc in scenes[1:])

        if not has_xfade or len(scenes) == 1:
            concat_txt = self.work_dir / "concat_list.txt"
            concat_lines = [f"file '{sc.rendered_clip_path.resolve().as_posix()}'" for sc in scenes]
            concat_txt.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", str(concat_txt),
                "-i", str(master_audio),
                "-vf", post_vf,
                "-map", "0:v", "-map", "1:a",
                "-t", f"{total_duration:.4f}",
                "-r", str(self.fps),
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                "-movflags", "+faststart",
                str(self.output_path),
            ]
            run_cmd(cmd, cwd=self.project_dir, desc="Stitch scenes and burn captions")
            return self.output_path

        inputs: List[str] = []
        for sc in scenes:
            inputs += ["-i", str(sc.rendered_clip_path)]
        audio_input_idx = len(scenes)
        inputs += ["-i", str(master_audio)]

        xfade_chains: List[str] = []
        prev_label = "[0:v]"
        for i in range(1, len(scenes)):
            sc = scenes[i]
            out_lbl = f"[vx_{i}]"
            if sc.transition_in != "cut" and sc.transition_duration > 0:
                xf_name = XFADE_TRANSITIONS.get(sc.transition_in, "fade")
                offset = max(0.0, sc.start_time)
                xfade_chains.append(
                    f"{prev_label}[{i}:v]xfade=transition={xf_name}:"
                    f"duration={sc.transition_duration:.4f}:offset={offset:.4f}{out_lbl}"
                )
            else:
                xfade_chains.append(
                    f"{prev_label}[{i}:v]concat=n=2:v=1:a=0{out_lbl}"
                )
            prev_label = out_lbl

        xfade_chains.append(f"{prev_label}{post_vf}[vfinal]")
        filter_complex = ";".join(xfade_chains)

        cmd = (
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
            + inputs
            + [
                "-filter_complex", filter_complex,
                "-map", "[vfinal]",
                "-map", f"{audio_input_idx}:a",
                "-t", f"{total_duration:.4f}",
                "-r", str(self.fps),
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                "-movflags", "+faststart",
                str(self.output_path),
            ]
        )
        run_cmd(cmd, cwd=self.project_dir, desc="Stitch scenes with xfade transitions and burn captions")
        return self.output_path

    def print_timeline_summary(self, scenes: List[ResolvedScene], total_duration: float) -> None:
        print("=" * 88)
        print(f" VideoGen Project  : {self.title}")
        print(f" Format & Theme    : {self.width}x{self.height} (9:16 1080p) @ {self.fps}fps | Theme: {self.theme_name}")
        print(
            f" Retention Engine  : {'ENABLED' if self.retention.get('enabled', True) else 'OFF'} "
            f"(VO Speed: {self.retention.get('vo_speed', 1.0)}x | Silence Trim | Hook Banner | Mid-Scene Jump-Cuts)"
        )
        print(f" Output Path       : {self.output_path}")
        print("-" * 88)
        print(f" {'#':<3} {'Scene ID':<16} {'Timeline (s)':<16} {'VO (s)':<8} {'Fit':<9} {'Effect':<12} {'Interrupt':<11} {'Trans'}")
        print("-" * 88)
        for sc in scenes:
            t_range = f"{sc.start_time:5.2f} -> {sc.end_time:5.2f}"
            vo_str = f"{sc.voiceover_duration:5.2f}s" if sc.voiceover_duration > 0 else "  -   "
            pi_str = f"@{sc.interrupt_offset:4.1f}s" if sc.pattern_interrupt else (
                f"{len(sc.media_paths)} cuts" if len(sc.media_paths) > 1 else "  -  "
            )
            print(
                f" {sc.index+1:<3} {sc.scene_id[:16]:<16} {t_range:<16} {vo_str:<8} "
                f"{sc.fit_mode:<9} {sc.effect:<12} {pi_str:<11} {sc.transition_in}"
            )
        print("-" * 88)
        print(f" Total Video Duration: {total_duration:.2f} seconds ({len(scenes)} scenes)")
        print("=" * 88)

    def generate_youtube_metadata(self, scenes: List[ResolvedScene], total_duration: float) -> Path:
        """
        Generate a ready-to-paste `youtube_metadata.txt` in the project's `output/` directory,
        optimized for YouTube Shorts, TikTok, and Instagram Reels CTR, watch-time loop velocity,
        comment engagement, and subscriber conversion.
        """
        yt_cfg = self.config.get("youtube_metadata", {}) or {}
        hook_str = str(self.config.get("hook_headline", self.title)).strip()

        # 1. High-CTR Title Variations (under 55 chars + #shorts)
        titles = yt_cfg.get("titles")
        if not titles:
            titles = [
                f"{self.title} 😱 #shorts",
                f"{hook_str.title()} (True Story) #shorts",
                f"Why Nobody Talks About {self.title} #shorts",
                f"The Craziest Moment in History: {self.title} #shorts",
                f"How {self.title} Changed History Forever #shorts",
            ]

        # 2. Full narration transcript for SEO indexing
        narration_lines = [
            str(sc.raw.get("caption") or sc.raw.get("voiceover_text") or "").strip()
            for sc in scenes
        ]
        narration_lines = [ln for ln in narration_lines if ln]
        first_hook_line = narration_lines[0] if narration_lines else self.title
        full_transcript = " ".join(narration_lines)

        # 3. Scene Timestamps / Chapters
        chapter_lines: List[str] = []
        for sc in scenes:
            mm = int(sc.start_time) // 60
            ss = int(sc.start_time) % 60
            label = sc.badge_text or sc.scene_id.replace("_", " ").title()
            chapter_lines.append(f"{mm:02d}:{ss:02d} - {label.title()}")

        # 4. Pinned Comment Options (Drives comment reading -> background video looping -> >120% APV)
        pinned_comments = yt_cfg.get("pinned_comments") or [
            f"📌 What part of {self.title} shocked you the most? Drop your thoughts below 👇 And SUBSCRIBE for daily hidden history!",
            f"📌 Should they make a movie about {self.title}? Comment YES or NO below 👇 (Subscribe so you don't miss Part 2!)",
            f"📌 Wildest historical rabbit hole of the week. Which history topic should we cover next? Comment below & Subscribe! 🔔",
        ]

        # 5. Hashtags & Studio Tags
        hashtags = yt_cfg.get(
            "hashtags",
            "#shorts #history #documentary #historyfacts #viral #storytime #didyouknow #education #commentary #historical",
        )
        tags_list = yt_cfg.get("tags") or [
            self.title,
            hook_str.title(),
            "history shorts",
            "crazy history facts",
            "hidden history",
            "documentary shorts",
            "history commentary",
            "true historical stories",
            "history explained",
            "military history",
            "world history",
            "did you know history",
            "viral history shorts",
            "youtube shorts history",
        ]
        tags_csv = ", ".join(tags_list)

        meta_path = self.output_path.parent / "youtube_metadata.txt"
        content = f"""================================================================================
 YOUTUBE SHORTS / TIKTOK / REELS — VIRAL METADATA & SUBSCRIBER CONVERSION PACK
 Project : {self.title}
 Video   : {self.output_path.name} ({self.width}x{self.height} 9:16 1080p | {total_duration:.1f}s)
================================================================================

--------------------------------------------------------------------------------
 1. HIGH-CTR TITLE OPTIONS (Pick #1 to start; swap to #2 if CTR < 7% after 2 hrs)
--------------------------------------------------------------------------------
[Option 1 - Top Recommended]
{titles[0]}

[Option 2 - Curiosity Gap]
{titles[1] if len(titles) > 1 else titles[0]}

[Option 3 - Question / Intrigue Hook]
{titles[2] if len(titles) > 2 else titles[0]}

[Option 4 - Extreme / Superlative Hook]
{titles[3] if len(titles) > 3 else titles[0]}

[Option 5 - Alternate Search SEO Title]
{titles[4] if len(titles) > 4 else titles[0]}


--------------------------------------------------------------------------------
 2. YOUTUBE DESCRIPTION (Copy & Paste Entire Block Below)
--------------------------------------------------------------------------------
{first_hook_line}

🔥 Subscribe for daily high-retention History & Commentary Shorts! 👉 [INSERT CHANNEL SUBSCRIBE LINK]

In this short documentary, we break down {self.title} — one of the most unbelievable true stories in history:
"{full_transcript}"

⏱️ TIMESTAMPS / CHAPTERS:
{chr(10).join(chapter_lines)}

💬 QUESTION OF THE DAY:
Which historical event should we animate next? Let us know in the comments!

{hashtags}


--------------------------------------------------------------------------------
 3. PINNED COMMENT STRATEGY (CRITICAL FOR 120%+ RETENTION & SUBSCRIBERS)
 * Why this works: Viewers reading & replying to your pinned comment keep the
   Short looping in the background, pushing Average Percentage Viewed > 100%!
--------------------------------------------------------------------------------
[Pinned Comment Option A - Engagement + Subscribe CTA]
{pinned_comments[0]}

[Pinned Comment Option B - Yes/No Debate Trigger]
{pinned_comments[1] if len(pinned_comments) > 1 else pinned_comments[0]}

[Pinned Comment Option C - Topic Request Funnel]
{pinned_comments[2] if len(pinned_comments) > 2 else pinned_comments[0]}


--------------------------------------------------------------------------------
 4. YOUTUBE STUDIO TAGS (Copy & Paste into "Tags" Box — Comma-Separated)
--------------------------------------------------------------------------------
{tags_csv}


--------------------------------------------------------------------------------
 5. TIKTOK / INSTAGRAM REELS CAPTION (Copy & Paste)
--------------------------------------------------------------------------------
{first_hook_line} 🤯🔥 Follow for more crazy untold history!
{hashtags}


--------------------------------------------------------------------------------
 6. UPLOAD & SUBSCRIBER GROWTH CHECKLIST
--------------------------------------------------------------------------------
- Thumbnail Frame : Select a frame between 00:01 and 00:03 where the Hook Banner
                    ("{hook_str}") is visible for maximum Shorts Shelf CTR.
- Related Video   : In YouTube Studio -> "Related Video", link this Short to your
                    highest-converting Short or long-form video to chain session watch-time.
- First 5 Mins    : Immediately post & PIN Comment Option A above right after publishing.
================================================================================
"""
        meta_path.write_text(content, encoding="utf-8")
        return meta_path

    def build(self) -> Path:
        scenes, total_duration = self.resolve_timeline()
        self.print_timeline_summary(scenes, total_duration)

        print("\n[1/5] Rendering 9:16 1080p scenes with hook flash & mid-scene pattern interrupts...")
        for sc in scenes:
            names = ", ".join(p.name for p in sc.media_paths)
            print(f"  -> Scene {sc.index+1}/{len(scenes)}: {sc.scene_id} ({names})")
            render_scene_clip(sc, self.width, self.height, self.fps, self.work_dir, self.force_rebuild)

        print("[2/5] Generating semantic power-word ASS captions, badges & 3s hook banner...")
        ass_path = self.work_dir / "captions.ass"
        self.generate_subtitles(scenes, ass_path, total_duration)

        print("[3/5] Mixing EQ-boosted voiceovers, procedural retention SFX & ducked BGM...")
        master_audio = self.work_dir / "master_audio.m4a"
        self.build_master_audio(scenes, total_duration, master_audio)

        print("[4/5] Stitching transitions, progress bar & burning captions into 1080x1920 MP4...")
        final_video = self.stitch_and_render(scenes, ass_path, master_audio, total_duration)

        print("[5/5] Generating viral YouTube Shorts / TikTok SEO metadata text file...")
        meta_path = self.generate_youtube_metadata(scenes, total_duration)

        print(f"\n[DONE] High-retention video & YouTube metadata created at:\n  Video    : {final_video}\n  Metadata : {meta_path}\n")
        return final_video


# ---------------------------------------------------------------------------
# Project Scaffolding (`init`)
# ---------------------------------------------------------------------------

def scaffold_new_project(project_dir: Path, theme: str = "history") -> Path:
    """Create a new project folder structure with a high-retention template project.json."""
    project_dir = project_dir.resolve()
    (project_dir / "assets" / "images").mkdir(parents=True, exist_ok=True)
    (project_dir / "assets" / "videos").mkdir(parents=True, exist_ok=True)
    (project_dir / "assets" / "voiceovers").mkdir(parents=True, exist_ok=True)
    (project_dir / "assets" / "audio").mkdir(parents=True, exist_ok=True)
    (project_dir / "output").mkdir(parents=True, exist_ok=True)

    template = {
        "title": project_dir.name.replace("_", " ").title(),
        "hook_headline": "THE HISTORY THEY NEVER TAUGHT YOU",
        "theme": theme,
        "resolution": [1080, 1920],
        "fps": 30,
        "output": "output/final_short.mp4",
        "auto_tts": True,
        "tts_rate": 1,
        "background_music": None,
        "retention": {
            "enabled": True,
            "trim_vo_silence": True,
            "vo_speed": 1.05,
            "hook_flash": True,
            "hook_banner_duration": 2.8,
            "auto_pattern_interrupt": True,
            "progress_bar": True
        },
        "scenes": [
            {
                "id": "hook",
                "badge": "HISTORY SHORT • PART 1",
                "media": "assets/images/scene_01.jpg",
                "voiceover": None,
                "voiceover_text": "What if one single mistake changed the entire course of human history in thirty-eight minutes?",
                "fit": "cover",
                "effect": "zoom_in",
                "grade": "vintage",
                "transition": "cut",
                "sfx": "builtin:boom"
            }
        ]
    }
    manifest_path = project_dir / "project.json"
    manifest_path.write_text(json.dumps(template, indent=2), encoding="utf-8")
    print(f"Created new high-retention '{theme}' project template at: {manifest_path}")
    return manifest_path


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="VideoGen: High-Retention 9:16 1080p FFmpeg Short Video Builder"
    )
    sub = parser.add_subparsers(dest="command")

    p_build = sub.add_parser("build", help="Render a 9:16 1080p video from a project.json manifest")
    p_build.add_argument(
        "manifest",
        nargs="?",
        default="projects/year_without_summer/project.json",
        help="Path to project.json (default: projects/year_without_summer/project.json)",
    )
    p_build.add_argument("--force", action="store_true", help="Ignore scene cache and re-render all clips")

    p_val = sub.add_parser("validate", help="Validate assets and print timeline table without rendering")
    p_val.add_argument("manifest", help="Path to project.json")

    p_meta = sub.add_parser("metadata", help="Generate viral YouTube Shorts / TikTok metadata text file")
    p_meta.add_argument("manifest", help="Path to project.json")

    p_init = sub.add_parser("init", help="Scaffold a new video project folder")
    p_init.add_argument("path", help="Folder path for new project (e.g., projects/roman_empire)")
    p_init.add_argument(
        "--theme",
        choices=["history", "commentary", "documentary"],
        default="history",
        help="Visual & caption preset theme",
    )

    if len(sys.argv) == 1:
        args = parser.parse_args(["build", "projects/baltic_fleet_1905/project.json"])
    elif sys.argv[1] not in ("build", "validate", "metadata", "init", "-h", "--help"):
        args = parser.parse_args(["build"] + sys.argv[1:])
    else:
        args = parser.parse_args()

    if args.command == "init":
        scaffold_new_project(Path(args.path), theme=args.theme)
    elif args.command == "validate":
        builder = VideoProjectBuilder(Path(args.manifest))
        scenes, total = builder.resolve_timeline()
        builder.print_timeline_summary(scenes, total)
        print("\nValidation passed! All media and audio files are ready.")
    elif args.command == "metadata":
        builder = VideoProjectBuilder(Path(args.manifest))
        scenes, total = builder.resolve_timeline()
        meta_path = builder.generate_youtube_metadata(scenes, total)
        print(f"Generated YouTube metadata at: {meta_path}")
    elif args.command == "build":
        builder = VideoProjectBuilder(Path(args.manifest), force_rebuild=args.force)
        builder.build()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
