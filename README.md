# VideoGen — High-Retention 9:16 1080p FFmpeg Short Video System

A declarative, single-command FFmpeg pipeline built for **History**, **Documentary**, and **Commentary** short-form videos (`1080x1920`, 9:16 vertical, H.264 + AAC) with built-in **viewer retention engineering**.

---

## High-Retention Features Built Into `videogen.py`

1. **3-Second Scroll-Stopper Hook Engine**:
   - **Zero Dead-Air Cold Open (`trim_vo_silence: true`)**: Automatically strips leading and trailing silence from voiceovers (`silenceremove`) so the first spoken word hits at `0.03s`.
   - **Hook Headline Banner (`hook_headline`)**: Renders a bold crimson/gold banner in the upper-center safe zone during the first `2.8s` with a `130% -> 100%` scale-punch entrance.
   - **Opening Exposure Flash & Whip-Zoom (`hook_flash: true`)**: Starts Scene 1 with a rapid whip-zoom, camera shake, exposure flash, and sub-bass impact (`builtin:boom`).
2. **Visual Pattern Interrupts Every ~3 Seconds**:
   - **Automatic Mid-Scene Jump-Cuts (`auto_pattern_interrupt: true`)**: Any single-image scene longer than `4.0s` automatically performs an instant `1.15x` jump-cut punch-in at the midpoint with a brief flash and subtle camera shutter click (`builtin:shutter`), cutting average shot length in half.
   - **Multi-Media B-Roll Arrays (`"media": ["img1.png", "img2.png"]`)**: Supply multiple images/videos in a single scene and `videogen.py` automatically cuts between them across the voiceover duration.
   - **Camera Shake (`"effect": "shake_zoom"`)**: High-impact decaying camera shake for explosions, battles, and dramatic reveals.
3. **Semantic Power-Word Captions (`libass`)**:
   - **Fast 3-Word Chunks (`max_words_per_chunk: 3`)**: Rapid caption cadence keeps the viewer's eyes locked to the center-lower third.
   - **Semantic Color Coding (`semantic_colors: true`)**:
     - **Numbers / Dates / Years** (e.g., `1816`, `38`, `9:00`) pop in **Electric Cyan (`#00F0FF`)** at `118%` scale.
     - **Power / Conflict / Shock Words** (e.g., `EXPLODED`, `WAR`, `FROZE`, `DIED`, `BLIZZARDS`, `FRANKENSTEIN`) pop in **Fiery Crimson (`#FF3B30`)** at `120%` scale.
     - **Standard Active Words** highlight in **Gold (`#FFD700`)** at `112%` scale while surrounding words in the chunk stay light gray (`#EAEAEA`).
4. **Broadcast Audio & Built-In Procedural SFX Library**:
   - **Vocal Presence Boost & Pacing (`vo_speed: 1.06`, `vo_eq_boost: true`)**: Applies `atempo` speed-up, `160Hz` warmth + `3.2kHz` articulation EQ, and dynamic compression (`acompressor`).
   - **Built-In SFX Synth (`builtin:*`)**: Trigger sound design without external audio files using `"sfx": "builtin:boom"`, `"builtin:whoosh"`, `"builtin:riser"`, `"builtin:shutter"`, `"builtin:tick"`, or `"builtin:hit"`.
   - **Auto-Ducked Background Music**: Sidechain compression ducks BGM whenever the narrator speaks.
5. **Animated Retention Progress Bar (`progress_bar: true`)**:
   - Renders a sleek animated gold/neon progress bar along the bottom edge of the 9:16 frame.

---

## Quick Start

### 1. Build the Included Projects
```powershell
# Build "1816: The Year Without a Summer" (5 scenes, AI oil paintings + animated blizzard video):
.\run.ps1 projects/year_without_summer/project.json

# Build "The 38-Minute War (Zanzibar, 1896)":
.\run.ps1 projects/history_demo/project.json
```

### 2. Scaffold a New Video Project
```powershell
python videogen.py init projects/new_topic --theme history
# Themes: history | commentary | documentary
```

### 3. Validate Timeline & Assets (Without Rendering)
```powershell
python videogen.py validate projects/year_without_summer/project.json
```
