#!/usr/bin/env python3
"""
Builds the "Project Azorian (1974): The CIA's Giant Ocean Claw" short video project
(`projects/project_azorian/`) featuring:
- 3 AI-generated 9:16 Cold War illustrations (Scenes 1, 3, 5) with real-time vector HUDs & embers
- 2 full 1080x1920 30fps procedural Motion-Graphics Videos:
    * Scene 2 (`02_ocean_depth_dive.mp4`): Animated 0 -> 16,500 ft Ocean Depth Dive Infographic
      with rolling depth counter, scrolling depth ruler, Titanic/Empire State comparisons,
      rising bubbles, and pulsing sonar rings.
    * Scene 4 (`04_claw_extraction.mp4`): Animated mechanical schematic of the giant CIA claw
      ("Clementine") descending on a 3-mile steel pipe, clamping onto the Soviet K-129 submarine,
      lifting it, and flashing a structural fracture alert.
"""

import json
import math
import random
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from videogen import run_cmd, synthesize_tts_fallback


def load_fonts() -> dict:
    try:
        return {
            "impact_xl": ImageFont.truetype("impact.ttf", 84),
            "impact_lg": ImageFont.truetype("impact.ttf", 56),
            "mono_lg": ImageFont.truetype("consolab.ttf", 40),
            "mono_md": ImageFont.truetype("consolab.ttf", 30),
            "mono_sm": ImageFont.truetype("consola.ttf", 24),
        }
    except Exception:
        d = ImageFont.load_default()
        return {"impact_xl": d, "impact_lg": d, "mono_lg": d, "mono_md": d, "mono_sm": d}


def render_ocean_depth_dive_video(out_mp4: Path, duration: float = 8.0, fps: int = 30) -> None:
    """
    Render a 1080x1920 30fps animated motion-graphics infographic diving from 0 ft to 16,500 ft.
    """
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1080, 1920
    frames_dir = out_mp4.parent / "_tmp_depth_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    fonts = load_fonts()

    rng = random.Random(1968)
    bubbles = [
        {
            "x": rng.uniform(80, w - 160),
            "y": rng.uniform(0, h),
            "r": rng.uniform(3, 9),
            "vy": rng.uniform(140, 320),
            "wobble": rng.uniform(0, math.tau),
        }
        for _ in range(55)
    ]

    # Pre-build background ocean depth gradient (surface cyan-blue -> abyssal black-blue)
    bg_base = Image.new("RGB", (w, h))
    bg_draw = ImageDraw.Draw(bg_base)
    for y in range(h):
        t = y / (h - 1)
        r = int(8 * (1 - t) + 2 * t)
        g = int(48 * (1 - t) + 12 * t)
        b = int(78 * (1 - t) + 22 * t)
        bg_draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Subtle sonar grid lines
    for x in range(0, w, 90):
        bg_draw.line([(x, 0), (x, h)], fill=(12, 42, 62), width=1)
    for y in range(0, h, 90):
        bg_draw.line([(0, y), (w, y)], fill=(12, 42, 62), width=1)

    total_frames = int(duration * fps)
    max_depth = 16500

    # Depth milestones (depth_ft, label, color)
    milestones = [
        (800, "800 FT • US NAVY SUB CRUSH DEPTH", (120, 220, 255)),
        (1454, "1,454 FT • EMPIRE STATE BUILDING", (255, 215, 90)),
        (3300, "3,300 FT • MIDNIGHT ZONE (ZERO SUNLIGHT)", (110, 190, 255)),
        (12500, "12,500 FT • RMS TITANIC WRECK", (255, 165, 70)),
        (16500, "16,500 FT • SOVIET SUB K-129 (3.1 MILES)", (255, 75, 75)),
    ]

    for f_idx in range(total_frames):
        t = f_idx / fps
        # Smooth ease-in-out progress reaching 16,500 ft at 75% of clip duration, then holding on target
        raw_p = min(1.0, t / (duration * 0.76))
        ease_p = raw_p * raw_p * (3.0 - 2.0 * raw_p)
        curr_depth = int(round(ease_p * max_depth))

        frame = bg_base.copy()
        draw = ImageDraw.Draw(frame)

        # 1. Rising deep-sea bubbles
        for b in bubbles:
            bx = b["x"] + 14.0 * math.sin(t * 3.0 + b["wobble"])
            by = (b["y"] - (b["vy"] + ease_p * 260.0) * t) % h
            rad = b["r"]
            draw.ellipse([bx - rad, by - rad, bx + rad, by + rad], outline=(70, 175, 220), width=2)

        # 2. Scrolling right-side depth ruler
        ruler_x = w - 125
        draw.line([(ruler_x, 220), (ruler_x, h - 280)], fill=(0, 240, 255), width=3)
        for tick_d in range(0, 18000, 500):
            # Map tick_d relative to curr_depth where curr_depth is at y = h * 0.50
            rel_ft = tick_d - curr_depth
            ty = int(h * 0.50 + (rel_ft / 5000.0) * 750)
            if 230 <= ty <= h - 290:
                is_major = (tick_d % 2000 == 0)
                t_len = 32 if is_major else 16
                draw.line([(ruler_x, ty), (ruler_x + t_len, ty)], fill=(0, 240, 255), width=3 if is_major else 1)
                if is_major:
                    draw.text((ruler_x - 12, ty), f"{tick_d:,}'", fill=(160, 230, 255), font=fonts["mono_sm"], anchor="rm")

        # 3. Depth milestone comparison markers scrolling past
        for m_depth, m_label, m_col in milestones:
            rel_ft = m_depth - curr_depth
            my = int(h * 0.50 + (rel_ft / 5000.0) * 750)
            if 250 <= my <= h - 320:
                draw.line([(90, my), (ruler_x - 20, my)], fill=m_col, width=3)
                draw.rectangle([90, my - 46, 820, my - 6], fill=(8, 22, 34), outline=m_col, width=2)
                draw.text((108, my - 26), m_label, fill=m_col, font=fonts["mono_sm"], anchor="lm")

        # 4. Sunken Soviet K-129 Submarine Silhouette & Pulsing Sonar Target Rings at 16,500 ft
        sub_rel_ft = 16500 - curr_depth
        sub_y = int(h * 0.50 + (sub_rel_ft / 5000.0) * 750)
        if 260 <= sub_y <= h - 240:
            sub_cx = w // 2 - 30
            # Expanding sonar pulse rings
            for ring_i in range(3):
                ring_phase = ((t * 1.4 + ring_i * 0.33) % 1.0)
                ring_r = int(40 + ring_phase * 220)
                ring_col = (
                    int(255 * (1 - ring_phase)),
                    int(80 * (1 - ring_phase)),
                    int(80 * (1 - ring_phase)),
                )
                draw.ellipse(
                    [sub_cx - ring_r, sub_y - int(ring_r * 0.55), sub_cx + ring_r, sub_y + int(ring_r * 0.55)],
                    outline=ring_col,
                    width=3,
                )

            # Submarine hull + conning tower silhouette
            draw.rounded_rectangle(
                [sub_cx - 210, sub_y - 26, sub_cx + 210, sub_y + 26],
                radius=24,
                fill=(24, 34, 44),
                outline=(255, 85, 85),
                width=3,
            )
            draw.polygon(
                [(sub_cx - 35, sub_y - 26), (sub_cx - 20, sub_y - 68), (sub_cx + 35, sub_y - 68), (sub_cx + 50, sub_y - 26)],
                fill=(24, 34, 44),
                outline=(255, 85, 85),
                width=3,
            )
            draw.text((sub_cx, sub_y), "K-129 WRECK SITE", fill=(255, 220, 220), font=fonts["mono_sm"], anchor="mm")

        # 5. Top Digital Depth Counter HUD Box
        draw.rectangle([70, 240, w - 70, 440], fill=(6, 18, 28), outline=(0, 240, 255), width=3)
        draw.text((w // 2, 282), "PACIFIC OCEAN • TELEMETRY DIVE", fill=(0, 240, 255), font=fonts["mono_md"], anchor="mm")
        depth_color = (255, 75, 75) if curr_depth >= 15000 else (255, 220, 80)
        draw.text((w // 2, 368), f"DEPTH: {curr_depth:,} FT", fill=depth_color, font=fonts["impact_xl"], anchor="mm")

        frame.save(frames_dir / f"frame_{f_idx:04d}.jpg", quality=92)

    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%04d.jpg"),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            str(out_mp4),
        ],
        desc="Encode Scene 2 Ocean Depth Dive motion graphics video",
    )

    for f in frames_dir.glob("*.jpg"):
        f.unlink(missing_ok=True)
    frames_dir.rmdir()


def render_claw_extraction_video(out_mp4: Path, duration: float = 8.5, fps: int = 30) -> None:
    """
    Render a 1080x1920 30fps animated engineering schematic of the CIA's giant mechanical
    claw ("Clementine") descending, clamping onto K-129, lifting it, and fracturing a claw tine.
    """
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1080, 1920
    frames_dir = out_mp4.parent / "_tmp_claw_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    fonts = load_fonts()

    # Blueprint schematic background
    bg_base = Image.new("RGB", (w, h), (6, 16, 28))
    bg_draw = ImageDraw.Draw(bg_base)
    for x in range(0, w, 60):
        bg_draw.line([(x, 0), (x, h)], fill=(12, 36, 58), width=1)
    for y in range(0, h, 60):
        bg_draw.line([(0, y), (w, y)], fill=(12, 36, 58), width=1)
    for x in range(0, w, 300):
        bg_draw.line([(x, 0), (x, h)], fill=(18, 55, 88), width=2)
    for y in range(0, h, 300):
        bg_draw.line([(0, y), (w, y)], fill=(18, 55, 88), width=2)

    # Seafloor sediment bed at y = 1320
    floor_y = 1320
    bg_draw.rectangle([0, floor_y, w, h], fill=(10, 22, 32))
    bg_draw.line([(0, floor_y), (w, floor_y)], fill=(0, 210, 255), width=3)

    total_frames = int(duration * fps)
    cx = w // 2

    for f_idx in range(total_frames):
        t = f_idx / fps
        frame = bg_base.copy()
        draw = ImageDraw.Draw(frame)

        # Phases of animation:
        # Phase 1 (0.0 -> 2.6s): Claw descends from y=520 to y=1180 with open jaws
        # Phase 2 (2.6 -> 3.8s): Claw jaws clamp shut around K-129 hull
        # Phase 3 (3.8 -> 5.8s): Claw lifts submarine upward from y=1260 to y=880
        # Phase 4 (5.8 -> end): Claw tine fractures (red alert flash), aft section drops while forward section stays held!
        if t < 2.6:
            p = t / 2.6
            claw_y = int(520 + (1190 - 520) * (p * p * (3 - 2 * p)))
            jaw_angle = 42.0  # Open degrees
            sub_y = 1265
            fractured = False
            status_txt = "PHASE 1: LOWERING CAPTURE VEHICLE (16,500 FT)"
            status_col = (0, 240, 255)
        elif t < 3.8:
            p = (t - 2.6) / 1.2
            claw_y = 1190
            jaw_angle = 42.0 * (1.0 - p) + 8.0 * p  # Clamping shut
            sub_y = 1265
            fractured = False
            status_txt = "PHASE 2: GRAPPLING CLAW LOCKED ON HULL"
            status_col = (255, 215, 0)
        elif t < 5.6:
            p = (t - 3.8) / 1.8
            claw_y = int(1190 - 310 * p)
            jaw_angle = 8.0
            sub_y = claw_y + 75
            fractured = False
            status_txt = "PHASE 3: HEAVY LIFT EXTRACTION IN PROGRESS"
            status_col = (0, 255, 140)
        else:
            p = min(1.0, (t - 5.6) / 1.8)
            claw_y = int(880 - 90 * p)
            jaw_angle = 12.0
            sub_y = claw_y + 75
            fractured = True
            status_txt = "ALERT: CLAW TINE FRACTURE • PARTIAL RECOVERY"
            status_col = (255, 65, 65)

        # 1. Draw Hughes Glomar Explorer ship silhouette at top (y=260)
        ship_y = 265
        draw.polygon(
            [(cx - 240, ship_y), (cx + 240, ship_y), (cx + 195, ship_y + 42), (cx - 195, ship_y + 42)],
            fill=(20, 48, 72),
            outline=(0, 240, 255),
            width=3,
        )
        # Derrick tower on ship
        draw.polygon(
            [(cx - 45, ship_y), (cx - 14, ship_y - 70), (cx + 14, ship_y - 70), (cx + 45, ship_y)],
            outline=(0, 240, 255),
            width=3,
        )
        draw.text((cx, ship_y + 21), "HUGHES GLOMAR EXPLORER", fill=(200, 245, 255), font=fonts["mono_sm"], anchor="mm")

        # 2. Draw 3-mile steel drill pipe string from ship down to claw
        draw.line([(cx - 8, ship_y + 42), (cx - 8, claw_y - 50)], fill=(160, 215, 240), width=4)
        draw.line([(cx + 8, ship_y + 42), (cx + 8, claw_y - 50)], fill=(160, 215, 240), width=4)
        for collar_y in range(ship_y + 90, claw_y - 50, 75):
            draw.rectangle([cx - 16, collar_y - 5, cx + 16, collar_y + 5], fill=(0, 240, 255))

        # 3. Draw K-129 Submarine (whole before fracture, split into held forward section + falling aft section after fracture)
        if not fractured:
            draw.rounded_rectangle(
                [cx - 250, sub_y - 32, cx + 250, sub_y + 32],
                radius=28,
                fill=(28, 42, 56),
                outline=(255, 195, 70),
                width=4,
            )
            draw.polygon(
                [(cx - 40, sub_y - 32), (cx - 22, sub_y - 82), (cx + 35, sub_y - 82), (cx + 52, sub_y - 32)],
                fill=(28, 42, 56),
                outline=(255, 195, 70),
                width=3,
            )
            draw.text((cx, sub_y), "SOVIET SUBMARINE K-129", fill=(255, 235, 180), font=fonts["mono_sm"], anchor="mm")
        else:
            # Forward section (38 ft) stays clamped in the claw!
            draw.rounded_rectangle(
                [cx - 220, sub_y - 32, cx + 15, sub_y + 32],
                radius=20,
                fill=(28, 42, 56),
                outline=(0, 255, 140),
                width=4,
            )
            draw.text((cx - 102, sub_y), "FWD BOW (CAPTURED)", fill=(0, 255, 140), font=fonts["mono_sm"], anchor="mm")

            # Aft section falls back toward the seafloor with rotation/sparks
            drop_p = min(1.0, (t - 5.6) / 1.4)
            aft_y = int(sub_y + drop_p * drop_p * (1265 - sub_y))
            draw.rounded_rectangle(
                [cx + 35, aft_y - 30, cx + 265, aft_y + 30],
                radius=20,
                fill=(38, 22, 26),
                outline=(255, 70, 70),
                width=4,
            )
            draw.text((cx + 150, aft_y), "AFT SECTION BREAK", fill=(255, 110, 110), font=fonts["mono_sm"], anchor="mm")

        # 4. Draw Giant Mechanical Claw ("Clementine")
        # Upper stabilizer beam
        draw.rectangle(
            [cx - 190, claw_y - 50, cx + 190, claw_y - 12],
            fill=(35, 65, 90),
            outline=(0, 240, 255),
            width=4,
        )
        draw.text((cx, claw_y - 31), "CAPTURE VEHICLE 'CLEMENTINE'", fill=(220, 250, 255), font=fonts["mono_sm"], anchor="mm")

        # 4 pairs of mechanical grappling tines
        rad = math.radians(jaw_angle)
        for offset_x in (-150, -55, 55, 150):
            pivot_x = cx + offset_x
            pivot_y = claw_y - 12
            # Left & right curved tines at each station
            tine_len = 115
            lx = int(pivot_x - math.sin(rad) * tine_len)
            ly = int(pivot_y + math.cos(rad) * tine_len)
            rx = int(pivot_x + math.sin(rad) * tine_len)
            ry = int(pivot_y + math.cos(rad) * tine_len)

            tine_col = (255, 75, 75) if (fractured and offset_x > 0) else (0, 240, 255)
            draw.line([(pivot_x, pivot_y), (lx, ly)], fill=tine_col, width=7)
            draw.line([(lx, ly), (lx + 24, ly + 22)], fill=tine_col, width=7)
            if not (fractured and offset_x == 150):
                draw.line([(pivot_x, pivot_y), (rx, ry)], fill=tine_col, width=7)
                draw.line([(rx, ry), (rx - 24, ry + 22)], fill=tine_col, width=7)

        # 5. Status Banner & Telemetry Header
        draw.rectangle([60, 1365, w - 60, 1465], fill=(8, 20, 32), outline=status_col, width=3)
        draw.text((cx, 1415), status_txt, fill=status_col, font=fonts["mono_md"], anchor="mm")

        frame.save(frames_dir / f"frame_{f_idx:04d}.jpg", quality=92)

    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%04d.jpg"),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            str(out_mp4),
        ],
        desc="Encode Scene 4 Claw Extraction motion graphics video",
    )

    for f in frames_dir.glob("*.jpg"):
        f.unlink(missing_ok=True)
    frames_dir.rmdir()


def main() -> None:
    proj_dir = Path("projects/project_azorian").resolve()
    img_dir = proj_dir / "assets" / "images"
    vid_dir = proj_dir / "assets" / "videos"
    vo_dir = proj_dir / "assets" / "voiceovers"
    aud_dir = proj_dir / "assets" / "audio"

    for d in (img_dir, vid_dir, vo_dir, aud_dir, proj_dir / "output"):
        d.mkdir(parents=True, exist_ok=True)

    # Copy AI illustrations from artifact directory
    artifact_dir = Path(r"C:\Users\benedick\.gemini\antigravity\brain\e218483e-5255-4893-bcca-4fc2b15d479e")
    mapping = [
        ("01_soviet_k129_sub_1794238414453.jpg", "01_soviet_k129_sub.png"),
        ("03_glomar_explorer_ship_1794238432383.jpg", "03_glomar_explorer_ship.png"),
        ("05_cold_war_heist_1794238452418.jpg", "05_cold_war_heist.png"),
    ]
    print("1. Copying Cold War 9:16 illustrations into `projects/project_azorian/assets/images/`...")
    for src_name, dst_name in mapping:
        shutil.copyfile(artifact_dir / src_name, img_dir / dst_name)

    print("2. Checking Scene 2 1080x1920 Motion-Graphics Video (`02_ocean_depth_dive.mp4`)...")
    if not (vid_dir / "02_ocean_depth_dive.mp4").exists():
        render_ocean_depth_dive_video(vid_dir / "02_ocean_depth_dive.mp4", duration=8.0, fps=30)

    print("3. Checking Scene 4 1080x1920 Motion-Graphics Video (`04_claw_extraction.mp4`)...")
    if not (vid_dir / "04_claw_extraction.mp4").exists():
        render_claw_extraction_video(vid_dir / "04_claw_extraction.mp4", duration=8.5, fps=30)

    print("4. Synthesizing 5 scene human neural voiceover tracks (en-US-ChristopherNeural)...")
    script_lines = [
        (
            "vo_01.wav",
            "In 1968, a Soviet nuclear missile submarine sank in the Pacific Ocean... and Moscow couldn't find the wreck.",
        ),
        (
            "vo_02.wav",
            "But the U.S. Navy secretly pinpointed it three miles deep — resting at sixteen thousand, five hundred feet below the surface.",
        ),
        (
            "vo_03.wav",
            "To steal it without starting World War Three, the CIA partnered with billionaire Howard Hughes to build a fake deep-sea mining ship.",
        ),
        (
            "vo_04.wav",
            "Hidden inside was a giant mechanical claw, that lowered on three miles of steel pipe and grabbed the Soviet submarine off the ocean floor.",
        ),
        (
            "vo_05.wav",
            "Even though part of the hull broke away during the lift, Project Azorian remains the most audacious ocean heist in Cold War history.",
        ),
    ]
    for fname, text in script_lines:
        synthesize_tts_fallback(text, vo_dir / fname, voice_rate=1, voice_name="christopher", pitch="-2Hz")

    print("5. Generating Cold War sonar ping SFX and dark synth pulse BGM...")
    bgm_path = aud_dir / "bgm_cold_war_pulse.wav"
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.22*sin(2*PI*65.41*t)+0.14*sin(2*PI*98.0*t)+0.09*sin(2*PI*130.81*t)*(0.6+0.4*sin(2*PI*2.0*t))':s=48000:d=45",
            "-af", "lowpass=f=380,afade=t=in:st=0:d=0.6",
            str(bgm_path),
        ],
        desc="Generate Cold War pulsing synth BGM",
    )

    sonar_sfx = aud_dir / "sonar_ping.wav"
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.55*sin(2*PI*1320*t)*exp(-4.5*t)':s=48000:d=1.0",
            "-af", "afade=t=in:st=0:d=0.01,afade=t=out:st=0.5:d=0.5",
            str(sonar_sfx),
        ],
        desc="Generate submarine sonar ping SFX",
    )

    print("6. Writing `projects/project_azorian/project.json`...")
    manifest = {
        "title": "Project Azorian: The CIA's Giant Ocean Claw",
        "hook_headline": "THE CIA'S GIANT OCEAN CLAW",
        "theme": "commentary",
        "resolution": [1080, 1920],
        "fps": 30,
        "output": "output/project_azorian_1080p.mp4",
        "default_overlay_fx": "radar_hud",
        "retention": {
            "enabled": True,
            "trim_vo_silence": True,
            "vo_speed": 1.0,
            "vo_eq_boost": True,
            "hook_flash": True,
            "hook_banner_duration": 2.9,
            "auto_pattern_interrupt": True,
            "pattern_interrupt_threshold": 4.0,
            "progress_bar": True,
            "progress_bar_color": "#00FF88",
            "loop_ending": True
        },
        "background_music": {
            "path": "assets/audio/bgm_cold_war_pulse.wav",
            "volume": 0.16,
            "ducking": True
        },
        "caption_style": {
            "font_name": "Impact",
            "font_size": 82,
            "primary_color": "#EAEAEA",
            "highlight_color": "#00FF88",
            "power_color": "#FF3B30",
            "number_color": "#00F0FF",
            "outline_color": "#000000",
            "outline": 6,
            "shadow": 4,
            "margin_v": 340,
            "uppercase": True,
            "mode": "word_highlight",
            "semantic_colors": True,
            "max_words_per_chunk": 3
        },
        "scenes": [
            {
                "id": "k129_sinks",
                "badge": "MARCH 1968 • PACIFIC OCEAN",
                "callout": "TARGET: SOVIET SUB K-129 // NUCLEAR BALLISTIC MISSILES",
                "media": "assets/images/01_soviet_k129_sub.png",
                "voiceover": "assets/voiceovers/vo_01.wav",
                "caption": "In 1968, a Soviet nuclear missile submarine sank in the Pacific Ocean, and Moscow couldn't find the wreck.",
                "fit": "cover",
                "effect": "zoom_in",
                "grade": "cinematic",
                "overlay_fx": "radar_hud",
                "transition": "cut",
                "sfx": "assets/audio/sonar_ping.wav",
                "sfx_volume": 0.45
            },
            {
                "id": "depth_dive_16500",
                "badge": "CLASSIFIED SOSUS HYDROPHONE FIX",
                "callout": "DEPTH: 16,500 FT (3.1 MILES) // CRUSH PRESSURE: 7,300 PSI",
                "media": "assets/videos/02_ocean_depth_dive.mp4",
                "voiceover": "assets/voiceovers/vo_02.wav",
                "caption": "But the U.S. Navy secretly pinpointed it 3 miles deep, resting at 16,500 feet below the surface.",
                "fit": "cover",
                "grade": "none",
                "overlay_fx": "none",
                "transition": "fadeblack",
                "transition_duration": 0.25,
                "sfx": "assets/audio/sonar_ping.wav",
                "sfx_volume": 0.40
            },
            {
                "id": "glomar_explorer",
                "badge": "1972 • THE HOWARD HUGHES COVER STORY",
                "callout": "VESSEL: HUGHES GLOMAR EXPLORER // COST: $500 MILLION",
                "media": "assets/images/03_glomar_explorer_ship.png",
                "voiceover": "assets/voiceovers/vo_03.wav",
                "caption": "To steal it without starting World War 3, the CIA partnered with billionaire Howard Hughes to build a fake deep-sea mining ship.",
                "fit": "cover",
                "effect": "pan_down",
                "grade": "cinematic",
                "overlay_fx": "blueprint_hud",
                "transition": "dissolve",
                "transition_duration": 0.25,
                "sfx": "builtin:whoosh",
                "sfx_volume": 0.35
            },
            {
                "id": "claw_extraction",
                "badge": "AUGUST 1974 • OPERATION AZORIAN",
                "callout": "CAPTURE VEHICLE: 'CLEMENTINE' // 3-MILE STEEL PIPE STRING",
                "media": "assets/videos/04_claw_extraction.mp4",
                "voiceover": "assets/voiceovers/vo_04.wav",
                "caption": "Hidden inside was a giant mechanical claw that lowered on 3 miles of steel pipe and grabbed the Soviet submarine off the ocean floor.",
                "fit": "cover",
                "grade": "none",
                "overlay_fx": "none",
                "transition": "fadeblack",
                "transition_duration": 0.25,
                "sfx": "builtin:boom",
                "sfx_volume": 0.42
            },
            {
                "id": "cold_war_legacy",
                "badge": "DECLASSIFIED • COLD WAR INTELLIGENCE",
                "callout": "RECOVERED: 2 NUCLEAR TORPEDOES & CRYPTOGRAPHIC MATERIALS",
                "media": "assets/images/05_cold_war_heist.png",
                "voiceover": "assets/voiceovers/vo_05.wav",
                "caption": "Even though part of the hull broke away during the lift, Project Azorian remains the most audacious ocean heist in Cold War history.",
                "fit": "cover",
                "effect": "zoom_out",
                "grade": "cinematic",
                "overlay_fx": "embers",
                "transition": "dissolve",
                "transition_duration": 0.25,
                "sfx": "assets/audio/sonar_ping.wav",
                "sfx_volume": 0.38
            }
        ]
    }

    manifest_path = proj_dir / "project.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Project Azorian assets & manifest ready at: {manifest_path}")


if __name__ == "__main__":
    main()
