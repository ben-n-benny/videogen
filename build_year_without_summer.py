#!/usr/bin/env python3
"""
Prepares all voiceovers, SFX, BGM, animated B-roll video clip, and `project.json`
for the new video project: "1816: The Year Without a Summer" (`projects/year_without_summer/`).
"""

import json
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from videogen import run_cmd, synthesize_tts_fallback


def generate_blizzard_video(out_mp4: Path, duration: float = 8.5, fps: int = 30) -> None:
    """
    Generate an atmospheric 16:9 archival-style video clip for Scene 3
    ("JUNE 1816 • SNOW IN NEW ENGLAND") with animated falling snow particles
    and frost vignette over an 1816 New England engraving plate.
    """
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1280, 720
    frames_dir = out_mp4.parent / "_tmp_blizzard_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Create base background image once
    base = Image.new("RGB", (w, h))
    bdraw = ImageDraw.Draw(base)
    for y in range(h):
        t = y / (h - 1)
        r = int(18 * (1 - t) + 38 * t)
        g = int(28 * (1 - t) + 52 * t)
        b = int(42 * (1 - t) + 68 * t)
        bdraw.line([(0, y), (w, y)], fill=(r, g, b))

    # Draw silhouetted 19th-century New England hills, church spire, and bare trees
    horizon_y = int(h * 0.72)
    bdraw.polygon(
        [(0, h), (0, horizon_y), (320, horizon_y - 35), (720, horizon_y + 10), (1050, horizon_y - 25), (w, horizon_y), (w, h)],
        fill=(210, 222, 232),
    )
    # Church & farmhouse silhouettes
    bdraw.rectangle([560, horizon_y - 70, 650, horizon_y], fill=(16, 22, 30))
    bdraw.polygon([(550, horizon_y - 70), (605, horizon_y - 115), (660, horizon_y - 70)], fill=(16, 22, 30))
    bdraw.polygon([(592, horizon_y - 110), (605, horizon_y - 210), (618, horizon_y - 110)], fill=(16, 22, 30))
    # Warm window glow
    bdraw.rectangle([585, horizon_y - 45, 600, horizon_y - 25], fill=(235, 180, 85))
    bdraw.rectangle([612, horizon_y - 45, 627, horizon_y - 25], fill=(235, 180, 85))

    # Ornate archival border
    bdraw.rectangle([20, 20, w - 20, h - 20], outline=(180, 205, 225), width=3)
    bdraw.rectangle([28, 28, w - 28, h - 28], outline=(120, 150, 175), width=1)

    try:
        font_hdr = ImageFont.truetype("georgia.ttf", 28)
        font_big = ImageFont.truetype("impact.ttf", 64)
        font_sub = ImageFont.truetype("georgia.ttf", 26)
    except Exception:
        font_hdr = ImageFont.load_default()
        font_big = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    bdraw.text((w // 2, 78), "NEW ENGLAND CHRONICLE • JUNE 1816", fill=(195, 220, 240), font=font_hdr, anchor="mm")
    bdraw.text((w // 2, 160), "FROZEN IN MID-SUMMER", fill=(245, 250, 255), font=font_big, anchor="mm")
    bdraw.text((w // 2, h - 55), "18 Inches of June Snow • Lakes Frozen Solid • Crop Failure", fill=(30, 45, 62), font=font_sub, anchor="mm")

    # Generate snow particles
    rng = random.Random(1816)
    num_flakes = 180
    flakes = [
        {
            "x": rng.uniform(0, w),
            "y": rng.uniform(0, h),
            "r": rng.uniform(1.5, 4.2),
            "vy": rng.uniform(90.0, 210.0),
            "vx": rng.uniform(-75.0, -25.0),
            "phase": rng.uniform(0, math.tau),
        }
        for _ in range(num_flakes)
    ]

    total_frames = int(duration * fps)
    for f_idx in range(total_frames):
        t = f_idx / fps
        frame = base.copy()
        fdraw = ImageDraw.Draw(frame)
        for fl in flakes:
            px = (fl["x"] + fl["vx"] * t + 12.0 * math.sin(t * 2.5 + fl["phase"])) % w
            py = (fl["y"] + fl["vy"] * t) % h
            rad = fl["r"]
            fdraw.ellipse([px - rad, py - rad, px + rad, py + rad], fill=(240, 248, 255))
        frame.save(frames_dir / f"frame_{f_idx:04d}.jpg", quality=90)

    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%04d.jpg"),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
            str(out_mp4),
        ],
        desc="Encode Scene 3 June 1816 blizzard video clip",
    )

    # Clean up temporary frames
    for f in frames_dir.glob("*.jpg"):
        f.unlink(missing_ok=True)
    frames_dir.rmdir()


def main() -> None:
    proj_dir = Path("projects/year_without_summer").resolve()
    img_dir = proj_dir / "assets" / "images"
    vid_dir = proj_dir / "assets" / "videos"
    vo_dir = proj_dir / "assets" / "voiceovers"
    aud_dir = proj_dir / "assets" / "audio"

    for d in (img_dir, vid_dir, vo_dir, aud_dir, proj_dir / "output"):
        d.mkdir(parents=True, exist_ok=True)

    print("1. Generating Scene 3 animated blizzard video clip (`03_june_blizzard.mp4`)...")
    generate_blizzard_video(vid_dir / "03_june_blizzard.mp4", duration=8.5, fps=30)

    print("2. Synthesizing 5 scene voiceover audio tracks...")
    script_lines = [
        (
            "vo_01.wav",
            "In 1816, summer simply never arrived. Looking back, historians call it the Year Without a Summer.",
        ),
        (
            "vo_02.wav",
            "Months earlier, Indonesia's Mount Tambora exploded in the largest volcanic eruption in recorded history, blasting a veil of ash across the planet.",
        ),
        (
            "vo_03.wav",
            "By June, relentless blizzards buried New England in snow, lakes froze solid in July, and crops across the Northern Hemisphere died overnight.",
        ),
        (
            "vo_04.wav",
            "Trapped indoors by the endless dark storms in Switzerland, an eighteen-year-old Mary Shelley passed the time by writing Frankenstein.",
        ),
        (
            "vo_05.wav",
            "One volcano on the other side of the Earth froze the world in July and changed human history forever.",
        ),
    ]
    for fname, text in script_lines:
        synthesize_tts_fallback(text, vo_dir / fname, voice_rate=1)

    print("3. Generating cinematic minor-chord BGM and volcanic rumble/wind SFX...")
    bgm_path = aud_dir / "bgm_dark_history.wav"
    # D-minor atmospheric drone (D2=73.42Hz, A2=110Hz, D3=146.83Hz, F3=174.61Hz)
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.20*sin(2*PI*73.42*t)+0.14*sin(2*PI*110*t)+0.10*sin(2*PI*146.83*t)+0.07*sin(2*PI*174.61*t)':s=48000:d=45",
            "-af", "lowpass=f=360,afade=t=in:st=0:d=1.2",
            str(bgm_path),
        ],
        desc="Generate D-minor dark history BGM",
    )

    rumble_sfx = aud_dir / "volcano_rumble.wav"
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "anoisesrc=d=0.9:c=brown:r=48000:a=0.55",
            "-af", "lowpass=f=180,afade=t=in:st=0:d=0.08,afade=t=out:st=0.35:d=0.55",
            str(rumble_sfx),
        ],
        desc="Generate deep volcanic rumble SFX",
    )

    wind_sfx = aud_dir / "cold_whoosh.wav"
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "anoisesrc=d=0.45:c=pink:r=48000:a=0.40",
            "-af", "bandpass=f=650:width_type=h:w=450,afade=t=in:st=0:d=0.12,afade=t=out:st=0.18:d=0.27",
            str(wind_sfx),
        ],
        desc="Generate cold wind whoosh SFX",
    )

    print("4. Writing `projects/year_without_summer/project.json`...")
    manifest = {
        "title": "1816: The Year Without a Summer",
        "theme": "history",
        "resolution": [1080, 1920],
        "fps": 30,
        "output": "output/year_without_a_summer_1080p.mp4",
        "background_music": {
            "path": "assets/audio/bgm_dark_history.wav",
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
                "id": "hook_1816",
                "badge": "1816 • GLOBAL CLIMATE ANOMALY",
                "media": "assets/images/02_blood_red_sky.png",
                "voiceover": "assets/voiceovers/vo_01.wav",
                "caption": "In 1816, summer simply never arrived. Historians call it the Year Without a Summer.",
                "fit": "blur_pad",
                "effect": "zoom_in",
                "grade": "vintage",
                "transition": "cut"
            },
            {
                "id": "tambora_1815",
                "badge": "APRIL 1815 • MOUNT TAMBORA",
                "media": "assets/images/01_tambora_eruption.png",
                "voiceover": "assets/voiceovers/vo_02.wav",
                "caption": "Months earlier, Indonesia's Mount Tambora exploded in the largest volcanic eruption in recorded history, blasting a veil of ash across the planet.",
                "fit": "blur_pad",
                "effect": "pan_up",
                "grade": "cinematic",
                "transition": "fadeblack",
                "transition_duration": 0.35,
                "sfx": "assets/audio/volcano_rumble.wav",
                "sfx_volume": 0.45
            },
            {
                "id": "june_blizzard",
                "badge": "JUNE 1816 • NEW ENGLAND BLIZZARD",
                "media": "assets/videos/03_june_blizzard.mp4",
                "voiceover": "assets/voiceovers/vo_03.wav",
                "caption": "By June, relentless blizzards buried New England in snow, lakes froze solid in July, and crops across the Northern Hemisphere died overnight.",
                "fit": "blur_pad",
                "grade": "cinematic",
                "transition": "dissolve",
                "transition_duration": 0.35,
                "sfx": "assets/audio/cold_whoosh.wav",
                "sfx_volume": 0.35
            },
            {
                "id": "mary_shelley",
                "badge": "GENEVA, SWITZERLAND • VILLA DIODATI",
                "media": "assets/images/04_mary_shelley_geneva.png",
                "voiceover": "assets/voiceovers/vo_04.wav",
                "caption": "Trapped indoors by the endless dark storms in Switzerland, an 18-year-old Mary Shelley passed the time by writing Frankenstein.",
                "fit": "blur_pad",
                "effect": "zoom_in_top",
                "grade": "vintage",
                "transition": "fadeblack",
                "transition_duration": 0.35,
                "sfx": "assets/audio/cold_whoosh.wav",
                "sfx_volume": 0.30
            },
            {
                "id": "outro_legacy",
                "badge": "THE BUTTERFLY EFFECT OF HISTORY",
                "media": "assets/images/05_global_aftermath.png",
                "voiceover": "assets/voiceovers/vo_05.wav",
                "caption": "One volcano on the other side of the Earth froze the world in July and changed human history forever.",
                "fit": "blur_pad",
                "effect": "zoom_out",
                "grade": "vintage",
                "transition": "dissolve",
                "transition_duration": 0.35,
                "sfx": "assets/audio/volcano_rumble.wav",
                "sfx_volume": 0.35
            }
        ]
    }

    manifest_path = proj_dir / "project.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Project assets & manifest prepared at: {manifest_path}")


if __name__ == "__main__":
    main()
