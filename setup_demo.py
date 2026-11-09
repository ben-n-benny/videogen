#!/usr/bin/env python3
"""
Generates a complete sample History Short project in `projects/history_demo/`
including sample archival images (both 16:9 landscape and 9:16 portrait),
a sample video clip, voiceover WAV files, ambient background music, transition SFX,
and `project.json`.
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from videogen import run_cmd, synthesize_tts_fallback


def create_illustrated_card(
    path: Path,
    size: tuple[int, int],
    bg_top: tuple[int, int, int],
    bg_bottom: tuple[int, int, int],
    accent: tuple[int, int, int],
    era_label: str,
    main_title: str,
    subtitle: str,
    motif: str = "compass",
) -> None:
    """Create a rich, detailed historical illustration card using Pillow."""
    w, h = size
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    # Vertical gradient background
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(bg_top[0] * (1 - t) + bg_bottom[0] * t)
        g = int(bg_top[1] * (1 - t) + bg_bottom[1] * t)
        b = int(bg_top[2] * (1 - t) + bg_bottom[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Subtle grid / map lines
    step = max(60, min(w, h) // 12)
    grid_col = (
        min(255, bg_bottom[0] + 22),
        min(255, bg_bottom[1] + 22),
        min(255, bg_bottom[2] + 22),
    )
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=grid_col, width=1)
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=grid_col, width=1)

    cx, cy = w // 2, h // 2
    radius = int(min(w, h) * 0.28)

    # Central geometric emblem
    if motif == "clock":
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=accent, width=6)
        draw.ellipse([cx - radius + 18, cy - radius + 18, cx + radius - 18, cy + radius - 18], outline=accent, width=2)
        # Clock hands at 9:02 and 9:40
        draw.line([(cx, cy), (cx - int(radius * 0.55), cy)], fill=accent, width=8)
        draw.line([(cx, cy), (cx + int(radius * 0.45), cy - int(radius * 0.65))], fill=accent, width=5)
    elif motif == "ships":
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=accent, width=5)
        for offset in (-60, 20, 90):
            y_wave = cy + offset
            draw.arc([cx - radius + 30, y_wave - 20, cx + radius - 30, y_wave + 20], 0, 180, fill=accent, width=4)
    else:
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=accent, width=5)
        draw.polygon(
            [(cx, cy - radius + 15), (cx + 28, cy), (cx, cy + radius - 15), (cx - 28, cy)],
            outline=accent,
            width=4,
        )

    # Ornate double border frame
    pad = 28
    draw.rectangle([pad, pad, w - pad, h - pad], outline=accent, width=4)
    draw.rectangle([pad + 10, pad + 10, w - pad - 10, h - pad - 10], outline=accent, width=2)

    try:
        font_era = ImageFont.truetype("georgia.ttf", int(min(w, h) * 0.042))
        font_title = ImageFont.truetype("impact.ttf", int(min(w, h) * 0.075))
        font_sub = ImageFont.truetype("georgia.ttf", int(min(w, h) * 0.036))
    except Exception:
        font_era = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw.text((cx, int(h * 0.14)), era_label, fill=accent, font=font_era, anchor="mm")
    draw.text((cx, int(h * 0.50)), main_title, fill=(248, 242, 228), font=font_title, anchor="mm")
    draw.text((cx, int(h * 0.84)), subtitle, fill=(220, 210, 190), font=font_sub, anchor="mm")

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, quality=95)


def main() -> None:
    proj_dir = Path("projects/history_demo").resolve()
    img_dir = proj_dir / "assets" / "images"
    vid_dir = proj_dir / "assets" / "videos"
    vo_dir = proj_dir / "assets" / "voiceovers"
    aud_dir = proj_dir / "assets" / "audio"

    for d in (img_dir, vid_dir, vo_dir, aud_dir, proj_dir / "output"):
        d.mkdir(parents=True, exist_ok=True)

    print("1. Creating sample historical images (16:9 archival + 9:16 portrait)...")
    create_illustrated_card(
        img_dir / "01_zanzibar_palace_16x9.jpg",
        size=(1920, 1080),  # Landscape 16:9 to showcase `blur_pad`
        bg_top=(38, 26, 18),
        bg_bottom=(18, 12, 8),
        accent=(218, 175, 85),
        era_label="AUGUST 27, 1896 • SULTANATE OF ZANZIBAR",
        main_title="THE 38-MINUTE WAR",
        subtitle="Archival Plate I — Beit al-Hukm Palace Harbor",
        motif="clock",
    )

    create_illustrated_card(
        img_dir / "02_ultimatum_9x16.jpg",
        size=(1080, 1920),  # Full 9:16 portrait to showcase `cover`
        bg_top=(45, 22, 22),
        bg_bottom=(16, 10, 12),
        accent=(235, 185, 90),
        era_label="THE BRITISH ULTIMATUM",
        main_title="09:00 AM DEADLINE",
        subtitle="Sultan Khalid bin Barghash refuses to step down",
        motif="compass",
    )

    create_illustrated_card(
        img_dir / "04_aftermath_16x9.jpg",
        size=(1920, 1080),
        bg_top=(24, 34, 42),
        bg_bottom=(10, 15, 20),
        accent=(210, 180, 110),
        era_label="09:40 AM • CEASEFIRE",
        main_title="SHORTEST WAR IN HISTORY",
        subtitle="Lasted less than a single episode of television",
        motif="clock",
    )

    print("2. Creating sample archival B-roll video clip (scene 3)...")
    # Render a 5-second animated radar/naval sweep MP4 clip using FFmpeg
    naval_card = img_dir / "03_naval_base.jpg"
    create_illustrated_card(
        naval_card,
        size=(1600, 1000),
        bg_top=(18, 36, 48),
        bg_bottom=(8, 18, 26),
        accent=(190, 210, 230),
        era_label="ROYAL NAVY SQUADRON",
        main_title="5 WARSHIPS OPEN FIRE",
        subtitle="HMS St George & HMS Philomel in Zanzibar Harbor",
        motif="ships",
    )
    sample_vid = vid_dir / "03_naval_bombardment.mp4"
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-i", str(naval_card),
            "-vf", "zoompan=z='1.0+0.12*(on/150)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1600x1000:fps=30,format=yuv420p",
            "-t", "5", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            str(sample_vid),
        ],
        desc="Generate sample B-roll video clip",
    )

    print("3. Generating voiceover audio files for each scene...")
    scenes_script = [
        (
            "vo_01.wav",
            "In 1896, the shortest war in human history started and ended in just thirty-eight minutes.",
        ),
        (
            "vo_02.wav",
            "When the Sultan of Zanzibar died suddenly, his nephew seized the palace without British approval and barricaded himself inside.",
        ),
        (
            "vo_03.wav",
            "At exactly nine A.M., five Royal Navy warships in the harbor opened fire, shattering the palace artillery in minutes.",
        ),
        (
            "vo_04.wav",
            "By nine-forty A.M., the Sultan's flag was shot down, making it the fastest military conflict ever recorded.",
        ),
    ]
    for filename, text in scenes_script:
        synthesize_tts_fallback(text, vo_dir / filename, voice_rate=1)

    print("4. Generating ambient background music and transition whoosh SFX...")
    bgm_path = aud_dir / "bgm_ambient_drone.wav"
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.18*sin(2*PI*110*t)+0.12*sin(2*PI*164.81*t)+0.08*sin(2*PI*220*t)':s=48000:d=30",
            "-af", "lowpass=f=400,afade=t=in:st=0:d=1.5",
            str(bgm_path),
        ],
        desc="Generate ambient background drone BGM",
    )

    sfx_path = aud_dir / "whoosh.wav"
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "anoisesrc=d=0.35:c=pink:r=48000:a=0.35",
            "-af", "bandpass=f=500:width_type=h:w=400,afade=t=in:st=0:d=0.12,afade=t=out:st=0.15:d=0.20",
            str(sfx_path),
        ],
        desc="Generate transition whoosh SFX",
    )

    print("5. Writing `projects/history_demo/project.json`...")
    manifest = {
        "title": "The 38-Minute War (Zanzibar, 1896)",
        "theme": "history",
        "resolution": [1080, 1920],
        "fps": 30,
        "output": "output/history_short_1080p.mp4",
        "background_music": {
            "path": "assets/audio/bgm_ambient_drone.wav",
            "volume": 0.16,
            "ducking": True
        },
        "caption_style": {
            "font_name": "Impact",
            "font_size": 76,
            "primary_color": "#FFFFFF",
            "highlight_color": "#FFD700",
            "outline_color": "#000000",
            "outline": 5,
            "shadow": 3,
            "margin_v": 340,
            "uppercase": True,
            "mode": "word_highlight",
            "max_words_per_chunk": 5
        },
        "scenes": [
            {
                "id": "hook_1896",
                "badge": "AUGUST 27, 1896 • ZANZIBAR",
                "media": "assets/images/01_zanzibar_palace_16x9.jpg",
                "voiceover": "assets/voiceovers/vo_01.wav",
                "caption": "In 1896, the shortest war in human history started and ended in just 38 minutes.",
                "fit": "blur_pad",
                "effect": "zoom_in",
                "grade": "vintage",
                "transition": "cut"
            },
            {
                "id": "palace_coup",
                "badge": "08:00 AM • THE STANDOFF",
                "media": "assets/images/02_ultimatum_9x16.jpg",
                "voiceover": "assets/voiceovers/vo_02.wav",
                "caption": "When the Sultan of Zanzibar died suddenly, his nephew seized the palace without British approval and barricaded himself inside.",
                "fit": "cover",
                "effect": "pan_down",
                "grade": "vintage",
                "transition": "fadeblack",
                "transition_duration": 0.35,
                "sfx": "assets/audio/whoosh.wav",
                "sfx_volume": 0.30
            },
            {
                "id": "bombardment",
                "badge": "09:02 AM • HARBOR BOMBARDMENT",
                "media": "assets/videos/03_naval_bombardment.mp4",
                "voiceover": "assets/voiceovers/vo_03.wav",
                "caption": "At exactly 9:00 AM, five Royal Navy warships in the harbor opened fire, shattering the palace artillery in minutes.",
                "fit": "blur_pad",
                "grade": "cinematic",
                "transition": "dissolve",
                "transition_duration": 0.35,
                "sfx": "assets/audio/whoosh.wav",
                "sfx_volume": 0.30
            },
            {
                "id": "aftermath",
                "badge": "09:40 AM • RECORD SET",
                "media": "assets/images/04_aftermath_16x9.jpg",
                "voiceover": "assets/voiceovers/vo_04.wav",
                "caption": "By 9:40 AM, the Sultan's flag was shot down, making it the fastest military conflict ever recorded.",
                "fit": "blur_pad",
                "effect": "zoom_out",
                "grade": "vintage",
                "transition": "fadeblack",
                "transition_duration": 0.35
            }
        ]
    }

    manifest_path = proj_dir / "project.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Sample project ready at: {manifest_path}")


if __name__ == "__main__":
    main()
