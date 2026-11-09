#!/usr/bin/env python3
"""
Builds "The Doomed 18,000-Mile Voyage of the Russian Baltic Fleet (1904–1905)"
(`projects/baltic_fleet_1905/`) featuring:
- Human Neural Voiceover (`en-US-ChristopherNeural` via `edge-tts`) with studio condenser-mic EQ
- 3 AI-generated 9:16 naval historical oil paintings (Scenes 1, 3, 5)
- 2 full 1080x1920 30fps procedural Motion-Graphics Videos:
    * Scene 2 (`02_voyage_map_18000mi.mp4`): Animated 18,000-Mile Naval Expedition Map
      tracing the route from the Baltic Sea -> Dogger Bank -> around Africa -> Madagascar -> Tsushima,
      with a rolling mileage counter (0 -> 18,000 NM), moving fleet marker, and incident popups.
    * Scene 4 (`04_tsushima_crossing_t.mp4`): Animated Tactical Naval Battle Map of Tsushima Strait
      showing Admiral Togo's fleet executing "Crossing the T", animated artillery salvos,
      explosion shockwaves, and a live fleet loss counter.
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
            "impact_xl": ImageFont.truetype("impact.ttf", 82),
            "impact_lg": ImageFont.truetype("impact.ttf", 54),
            "mono_lg": ImageFont.truetype("consolab.ttf", 38),
            "mono_md": ImageFont.truetype("consolab.ttf", 28),
            "mono_sm": ImageFont.truetype("consola.ttf", 23),
        }
    except Exception:
        d = ImageFont.load_default()
        return {"impact_xl": d, "impact_lg": d, "mono_lg": d, "mono_md": d, "mono_sm": d}


def render_voyage_map_video(out_mp4: Path, duration: float = 8.5, fps: int = 30) -> None:
    """
    Render a 1080x1920 30fps animated map infographic tracing the 18,000-mile voyage
    of the Russian 2nd Pacific Squadron with rolling mileage counter and incident popups.
    """
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1080, 1920
    frames_dir = out_mp4.parent / "_tmp_map_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    fonts = load_fonts()

    # Build stylized dark vintage naval chart canvas
    bg_base = Image.new("RGB", (w, h), (10, 20, 32))
    bg_draw = ImageDraw.Draw(bg_base)

    # Latitude / Longitude grid lines
    for x in range(0, w, 90):
        bg_draw.line([(x, 0), (x, h)], fill=(18, 38, 56), width=1)
    for y in range(0, h, 90):
        bg_draw.line([(0, y), (w, y)], fill=(18, 38, 56), width=1)

    # Stylized continental landmasses (Europe, Africa, Asia, Japan) on 1080x1920 chart
    land_col = (26, 46, 58)
    land_border = (65, 115, 145)
    # Europe
    bg_draw.polygon(
        [(230, 520), (420, 470), (540, 520), (490, 650), (310, 680), (210, 630)],
        fill=land_col, outline=land_border, width=2,
    )
    # Africa
    bg_draw.polygon(
        [(250, 710), (470, 710), (560, 880), (510, 1180), (410, 1340), (330, 1280), (290, 1020), (190, 880)],
        fill=land_col, outline=land_border, width=2,
    )
    # Madagascar
    bg_draw.polygon(
        [(545, 1140), (585, 1130), (575, 1255), (535, 1245)],
        fill=land_col, outline=land_border, width=2,
    )
    # Eurasia / India / Southeast Asia / China
    bg_draw.polygon(
        [(500, 530), (960, 510), (980, 820), (860, 960), (790, 1060), (740, 960), (650, 980), (580, 840)],
        fill=land_col, outline=land_border, width=2,
    )
    # Japan archipelago
    bg_draw.polygon(
        [(925, 690), (975, 665), (985, 765), (930, 790)],
        fill=land_col, outline=land_border, width=2,
    )

    # Route waypoints: (x, y, cumulative_miles, label, alert_text)
    waypoints = [
        (360, 515, 0, "OCT 1904 • KRONSTADT (BALTIC SEA)", "45 WARSHIPS DEPART RUSSIA"),
        (235, 565, 1200, "DOGGER BANK (NORTH SEA)", "MISTOOK BRITISH TRAWLERS FOR JAPANESE TORPEDO BOATS"),
        (195, 685, 2900, "TANGIER, MOROCCO", "ANCHOR ACCIDENTALLY CUT INTERNATIONAL TELEGRAPH CABLE"),
        (145, 920, 6400, "DAKAR, WEST AFRICA", "OVERLOADED BATTLESHIPS PACKED COAL IN OFFICERS' CABINS"),
        (385, 1375, 10200, "CAPE OF GOOD HOPE", "ROUNDED SOUTHERN TIP OF AFRICA IN GALE-FORCE STORMS"),
        (565, 1200, 12400, "NOSY BE, MADAGASCAR", "CREWS ADOPTED CROCODILES & VENOMOUS SNAKES ON DECK"),
        (815, 995, 15800, "CAM RANH BAY, INDOCHINA", "7 MONTHS AT SEA • HULLS FOULED WITH SEAWEED"),
        (910, 755, 18000, "MAY 1905 • TSUSHIMA STRAIT", "INTERCEPTED BY ADMIRAL TOGO'S JAPANESE FLEET"),
    ]

    # Interpolate dense path points for smooth drawing
    dense_pts: list[tuple[float, float, float, int]] = []
    for i in range(len(waypoints) - 1):
        x0, y0, m0, _, _ = waypoints[i]
        x1, y1, m1, _, _ = waypoints[i + 1]
        steps = 35
        for s in range(steps):
            u = s / steps
            px = x0 + (x1 - x0) * u
            py = y0 + (y1 - y0) * u
            pm = m0 + (m1 - m0) * u
            dense_pts.append((px, py, pm, i))
    dense_pts.append((waypoints[-1][0], waypoints[-1][1], waypoints[-1][2], len(waypoints) - 1))

    total_frames = int(duration * fps)
    for f_idx in range(total_frames):
        t = f_idx / fps
        prog = min(1.0, t / (duration * 0.85))
        ease_p = prog * prog * (3.0 - 2.0 * prog)
        pt_idx = min(len(dense_pts) - 1, max(0, int(round(ease_p * (len(dense_pts) - 1)))))
        curr_x, curr_y, curr_miles, wp_stage = dense_pts[pt_idx]

        frame = bg_base.copy()
        draw = ImageDraw.Draw(frame)

        # 1. Draw full faint dotted planned route
        for k in range(0, len(dense_pts) - 1, 3):
            draw.line(
                [(dense_pts[k][0], dense_pts[k][1]), (dense_pts[k + 1][0], dense_pts[k + 1][1])],
                fill=(45, 85, 110),
                width=3,
            )

        # 2. Draw active glowing crimson/gold traveled route up to pt_idx
        if pt_idx >= 1:
            traveled_xy = [(dense_pts[k][0], dense_pts[k][1]) for k in range(pt_idx + 1)]
            draw.line(traveled_xy, fill=(255, 70, 55), width=8)
            draw.line(traveled_xy, fill=(255, 215, 80), width=3)

        # 3. Draw reached waypoint nodes & labels
        for w_i, (wx, wy, wm, w_title, _) in enumerate(waypoints):
            if curr_miles >= wm - 100:
                draw.ellipse([wx - 10, wy - 10, wx + 10, wy + 10], fill=(255, 215, 0), outline=(255, 60, 60), width=3)
                lbl_x = wx + 18 if wx < w * 0.62 else wx - 18
                lbl_anchor = "lm" if wx < w * 0.62 else "rm"
                draw.text((lbl_x, wy), w_title, fill=(235, 245, 255), font=fonts["mono_sm"], anchor=lbl_anchor)

        # 4. Pulsing Fleet Head Marker
        pulse_r = int(16 + 18 * ((t * 2.2) % 1.0))
        draw.ellipse([curr_x - pulse_r, curr_y - pulse_r, curr_x + pulse_r, curr_y + pulse_r], outline=(255, 90, 70), width=3)
        draw.ellipse([curr_x - 11, curr_y - 11, curr_x + 11, curr_y + 11], fill=(255, 60, 60), outline=(255, 255, 255), width=3)

        # 5. Top Telemetry Header Box
        draw.rectangle([60, 235, w - 60, 435], fill=(8, 18, 28), outline=(255, 195, 70), width=3)
        days_at_sea = int(round((curr_miles / 18000.0) * 225))
        draw.text(
            (w // 2, 278),
            f"2ND PACIFIC SQUADRON • DAY {days_at_sea} AT SEA",
            fill=(255, 215, 90),
            font=fonts["mono_md"],
            anchor="mm",
        )
        draw.text(
            (w // 2, 365),
            f"DISTANCE: {int(round(curr_miles)):,} MILES",
            fill=(255, 255, 255),
            font=fonts["impact_xl"],
            anchor="mm",
        )

        # 6. Active Incident Alert Card above captions
        active_wp = waypoints[min(len(waypoints) - 1, wp_stage + (1 if prog > 0.08 else 0))]
        draw.rectangle([60, 1380, w - 60, 1485], fill=(28, 12, 14), outline=(255, 75, 65), width=3)
        draw.text((w // 2, 1412), f"LOGBOOK INCIDENT // {active_wp[3]}", fill=(255, 185, 80), font=fonts["mono_sm"], anchor="mm")
        draw.text((w // 2, 1452), active_wp[4], fill=(255, 240, 240), font=fonts["mono_sm"], anchor="mm")

        frame.save(frames_dir / f"frame_{f_idx:04d}.jpg", quality=92)

    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%04d.jpg"),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            str(out_mp4),
        ],
        desc="Encode Scene 2 18,000-Mile Voyage Map video",
    )

    for f in frames_dir.glob("*.jpg"):
        f.unlink(missing_ok=True)
    frames_dir.rmdir()


def render_tsushima_battle_video(out_mp4: Path, duration: float = 8.0, fps: int = 30) -> None:
    """
    Render a 1080x1920 30fps animated naval tactical map of the Battle of Tsushima (May 27, 1905)
    showing Admiral Togo's fleet executing "Crossing the T" and concentrating fire on the Russian column.
    """
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1080, 1920
    frames_dir = out_mp4.parent / "_tmp_tsushima_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    fonts = load_fonts()

    bg_base = Image.new("RGB", (w, h), (8, 18, 28))
    bg_draw = ImageDraw.Draw(bg_base)
    for x in range(0, w, 75):
        bg_draw.line([(x, 0), (x, h)], fill=(14, 34, 52), width=1)
    for y in range(0, h, 75):
        bg_draw.line([(0, y), (w, y)], fill=(14, 34, 52), width=1)

    total_frames = int(duration * fps)
    num_russian = 8
    num_japanese = 8

    for f_idx in range(total_frames):
        t = f_idx / fps
        p = min(1.0, t / duration)
        frame = bg_base.copy()
        draw = ImageDraw.Draw(frame)

        # 1. Russian Column (8 battleships steaming slowly northward along x = 540)
        rus_positions: list[tuple[int, int]] = []
        sunk_count = min(8, int(max(0.0, (t - 1.4) / (duration - 2.0)) * 8.5))
        for r_i in range(num_russian):
            rx = int(540 + 18 * math.sin(r_i * 0.7 + t * 0.5))
            ry = int(820 + r_i * 72 - t * 26)
            rus_positions.append((rx, ry))
            is_sunk = r_i < sunk_count
            hull_col = (60, 20, 20) if is_sunk else (220, 65, 55)
            out_col = (255, 80, 80) if not is_sunk else (120, 50, 50)
            draw.rounded_rectangle([rx - 14, ry - 26, rx + 14, ry + 26], radius=8, fill=hull_col, outline=out_col, width=3)
            if is_sunk:
                # Expanding fire/hit ring on stricken lead battleships
                ring_r = int(22 + 24 * ((t * 1.8 + r_i * 0.3) % 1.0))
                draw.ellipse([rx - ring_r, ry - ring_r, rx + ring_r, ry + ring_r], outline=(255, 140, 40), width=3)
                draw.line([(rx - 16, ry - 16), (rx + 16, ry + 16)], fill=(255, 60, 60), width=4)
                draw.line([(rx + 16, ry - 16), (rx - 16, ry + 16)], fill=(255, 60, 60), width=4)

        # 2. Japanese Combined Fleet (Admiral Togo executing the U-turn & "Crossing the T" arc across y = 610)
        jpn_positions: list[tuple[int, int]] = []
        for j_i in range(num_japanese):
            u = p * 1.15 - j_i * 0.08
            jx = int(260 + max(0.0, min(1.0, u)) * 560)
            jy = int(620 - 55 * math.sin(max(0.0, min(1.0, u)) * math.pi))
            jpn_positions.append((jx, jy))
            draw.rounded_rectangle([jx - 26, jy - 13, jx + 26, jy + 13], radius=8, fill=(16, 85, 110), outline=(0, 240, 255), width=3)

        # 3. Animated Broadside Firing Arcs from Japanese line onto the lead Russian battleships
        if t > 0.8 and rus_positions:
            for j_i, (jx, jy) in enumerate(jpn_positions):
                target_rx, target_ry = rus_positions[min(len(rus_positions) - 1, j_i // 2)]
                salvo_phase = (t * 2.4 + j_i * 0.27) % 1.0
                sx = int(jx + (target_rx - jx) * salvo_phase)
                sy = int(jy + (target_ry - jy) * salvo_phase)
                draw.line([(jx, jy), (target_rx, target_ry)], fill=(60, 110, 130), width=1)
                draw.ellipse([sx - 6, sy - 6, sx + 6, sy + 6], fill=(255, 230, 90), outline=(255, 90, 40), width=2)

        # 4. Tactical Labels
        draw.text((540, 515), "ADMIRAL TOGO • 'CROSSING THE T'", fill=(0, 240, 255), font=fonts["mono_md"], anchor="mm")
        draw.text((755, 980), "RUSSIAN COLUMN\n(TRAPPED IN SINGLE LINE)", fill=(255, 110, 100), font=fonts["mono_sm"], anchor="lm")

        # 5. Top Scoreboard HUD
        draw.rectangle([60, 235, w - 60, 435], fill=(8, 18, 28), outline=(0, 240, 255), width=3)
        draw.text((w // 2, 278), "TSUSHIMA STRAIT • MAY 27, 1905", fill=(0, 240, 255), font=fonts["mono_md"], anchor="mm")
        draw.text(
            (w // 2, 365),
            f"BATTLESHIPS SUNK: {sunk_count} / 8",
            fill=(255, 75, 75) if sunk_count >= 4 else (255, 215, 80),
            font=fonts["impact_xl"],
            anchor="mm",
        )

        # 6. Bottom Tactical Telemetry Box
        tonnage_lost = int(round((sunk_count / 8.0) * 126000))
        draw.rectangle([60, 1385, w - 60, 1480], fill=(16, 20, 30), outline=(255, 195, 70), width=3)
        draw.text(
            (w // 2, 1432),
            f"RUSSIAN LOSSES: {tonnage_lost:,} TONS // JAPANESE BATTLESHIPS LOST: 0",
            fill=(255, 225, 130),
            font=fonts["mono_sm"],
            anchor="mm",
        )

        frame.save(frames_dir / f"frame_{f_idx:04d}.jpg", quality=92)

    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%04d.jpg"),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            str(out_mp4),
        ],
        desc="Encode Scene 4 Battle of Tsushima tactical video",
    )

    for f in frames_dir.glob("*.jpg"):
        f.unlink(missing_ok=True)
    frames_dir.rmdir()


def main() -> None:
    proj_dir = Path("projects/baltic_fleet_1905").resolve()
    img_dir = proj_dir / "assets" / "images"
    vid_dir = proj_dir / "assets" / "videos"
    vo_dir = proj_dir / "assets" / "voiceovers"
    aud_dir = proj_dir / "assets" / "audio"

    for d in (img_dir, vid_dir, vo_dir, aud_dir, proj_dir / "output"):
        d.mkdir(parents=True, exist_ok=True)

    print("1. Rendering Scene 2 1080x1920 Motion-Graphics Video (`02_voyage_map_18000mi.mp4`)...")
    if not (vid_dir / "02_voyage_map_18000mi.mp4").exists():
        render_voyage_map_video(vid_dir / "02_voyage_map_18000mi.mp4", duration=8.5, fps=30)

    print("2. Rendering Scene 4 1080x1920 Motion-Graphics Video (`04_tsushima_crossing_t.mp4`)...")
    if not (vid_dir / "04_tsushima_crossing_t.mp4").exists():
        render_tsushima_battle_video(vid_dir / "04_tsushima_crossing_t.mp4", duration=8.0, fps=30)

    print("3. Synthesizing 5 human neural voiceover tracks (en-US-ChristopherNeural)...")
    script_lines = [
        (
            "vo_01.wav",
            "In 1904, Russia sent forty-five warships on an eighteen-thousand-mile voyage around the world to fight Japan — and it turned into the greatest disaster in naval history.",
        ),
        (
            "vo_02.wav",
            "Barely out of port in the North Sea, panicked lookouts mistook British fishing trawlers for Japanese torpedo boats, and opened fire for twenty minutes.",
        ),
        (
            "vo_03.wav",
            "Stopping in Madagascar, sailors adopted crocodiles and venomous snakes that escaped inside the warships, turning the fleet into a floating zoo.",
        ),
        (
            "vo_04.wav",
            "After seven exhausting months at sea, the fleet finally reached Tsushima Strait — where Admiral Togo crossed their T and wiped them out in a single afternoon.",
        ),
        (
            "vo_05.wav",
            "Out of eight Russian battleships, every single one was sunk or captured, while Japan didn't lose a single capital ship.",
        ),
    ]
    for fname, text in script_lines:
        synthesize_tts_fallback(text, vo_dir / fname, voice_rate=1, voice_name="christopher", pitch="-2Hz")

    print("4. Generating dramatic maritime BGM and naval cannon salvo SFX...")
    bgm_path = aud_dir / "bgm_naval_tension.wav"
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.20*sin(2*PI*55.0*t)+0.14*sin(2*PI*82.41*t)+0.10*sin(2*PI*110.0*t)+0.06*sin(2*PI*130.81*t)':s=48000:d=50",
            "-af", "lowpass=f=360,afade=t=in:st=0:d=0.6",
            str(bgm_path),
        ],
        desc="Generate dramatic A-minor naval BGM",
    )

    cannon_sfx = aud_dir / "cannon_salvo.wav"
    run_cmd(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", "aevalsrc='0.80*sin(2*PI*(95*exp(-3*t)+30)*t)*exp(-2.8*t)+0.45*random(0)*exp(-8*t)':s=48000:d=1.0",
            "-af", "lowpass=f=320,afade=t=in:st=0:d=0.005,afade=t=out:st=0.45:d=0.55",
            str(cannon_sfx),
        ],
        desc="Generate naval cannon salvo SFX",
    )

    print("5. Writing `projects/baltic_fleet_1905/project.json`...")
    manifest = {
        "title": "The 18,000-Mile Voyage of Doom (1904-1905)",
        "hook_headline": "THE 18,000-MILE VOYAGE OF DOOM",
        "theme": "history",
        "resolution": [1080, 1920],
        "fps": 30,
        "output": "output/baltic_fleet_1905_1080p.mp4",
        "default_overlay_fx": "embers",
        "retention": {
            "enabled": True,
            "trim_vo_silence": True,
            "vo_speed": 1.0,
            "vo_eq_boost": True,
            "hook_flash": True,
            "hook_banner_duration": 3.0,
            "auto_pattern_interrupt": True,
            "pattern_interrupt_threshold": 4.0,
            "progress_bar": True,
            "progress_bar_color": "#FFD700",
            "loop_ending": True
        },
        "background_music": {
            "path": "assets/audio/bgm_naval_tension.wav",
            "volume": 0.16,
            "ducking": True
        },
        "caption_style": {
            "font_name": "Impact",
            "font_size": 82,
            "primary_color": "#EAEAEA",
            "highlight_color": "#FFD700",
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
                "id": "fleet_departure",
                "badge": "OCTOBER 1904 • RUSSIAN BALTIC FLEET",
                "callout": "EXPEDITION: 45 WARSHIPS // TARGET: JAPAN (18,000 MILES)",
                "media": "assets/images/01_baltic_fleet_departure.png",
                "voiceover": "assets/voiceovers/vo_01.wav",
                "caption": "In 1904, Russia sent 45 warships on an 18,000-mile voyage around the world to fight Japan — and it turned into the greatest disaster in naval history.",
                "fit": "cover",
                "effect": "zoom_in",
                "grade": "vintage",
                "overlay_fx": "embers",
                "transition": "cut",
                "sfx": "assets/audio/cannon_salvo.wav",
                "sfx_volume": 0.42
            },
            {
                "id": "voyage_map",
                "badge": "DOGGER BANK INCIDENT • NORTH SEA",
                "callout": "FRIENDLY FIRE & PHANTOM TORPEDO BOATS across 3 OCEANS",
                "media": "assets/videos/02_voyage_map_18000mi.mp4",
                "voiceover": "assets/voiceovers/vo_02.wav",
                "caption": "Barely out of port in the North Sea, panicked lookouts mistook British fishing trawlers for Japanese torpedo boats, and opened fire for 20 minutes.",
                "fit": "cover",
                "grade": "none",
                "overlay_fx": "none",
                "transition": "fadeblack",
                "transition_duration": 0.25,
                "sfx": "builtin:whoosh",
                "sfx_volume": 0.35
            },
            {
                "id": "madagascar_zoo",
                "badge": "JANUARY 1905 • MADAGASCAR ANCHORAGE",
                "callout": "ONBOARD CHAOS: ESCAPED CROCODILES, SNAKES & TROPICAL HEAT",
                "media": "assets/images/03_madagascar_chaos.png",
                "voiceover": "assets/voiceovers/vo_03.wav",
                "caption": "Stopping in Madagascar, sailors adopted crocodiles and venomous snakes that escaped inside the warships, turning the fleet into a floating zoo.",
                "fit": "cover",
                "effect": "pan_right",
                "grade": "vintage",
                "overlay_fx": "embers",
                "transition": "dissolve",
                "transition_duration": 0.25,
                "sfx": "builtin:whoosh",
                "sfx_volume": 0.32
            },
            {
                "id": "tsushima_tactical",
                "badge": "MAY 27, 1905 • BATTLE OF TSUSHIMA",
                "callout": "TACTICAL MANEUVER: ADMIRAL TOGO CROSSES THE RUSSIAN 'T'",
                "media": "assets/videos/04_tsushima_crossing_t.mp4",
                "voiceover": "assets/voiceovers/vo_04.wav",
                "caption": "After 7 exhausting months at sea, the fleet finally reached Tsushima Strait — where Admiral Togo crossed their T and wiped them out in a single afternoon.",
                "fit": "cover",
                "grade": "none",
                "overlay_fx": "none",
                "transition": "fadeblack",
                "transition_duration": 0.25,
                "sfx": "assets/audio/cannon_salvo.wav",
                "sfx_volume": 0.45
            },
            {
                "id": "tsushima_aftermath",
                "badge": "THE AFTERMATH • END OF AN EMPIRE",
                "callout": "FINAL SCORE: 8 OF 8 RUSSIAN BATTLESHIPS LOST // 0 JAPANESE LOST",
                "media": "assets/images/05_tsushima_aftermath.png",
                "voiceover": "assets/voiceovers/vo_05.wav",
                "caption": "Out of 8 Russian battleships, every single one was sunk or captured, while Japan didn't lose a single capital ship.",
                "fit": "cover",
                "effect": "zoom_out",
                "grade": "vintage",
                "overlay_fx": "embers",
                "transition": "dissolve",
                "transition_duration": 0.25,
                "sfx": "assets/audio/cannon_salvo.wav",
                "sfx_volume": 0.38
            }
        ]
    }

    manifest_path = proj_dir / "project.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Baltic Fleet 1905 assets & manifest ready at: {manifest_path}")


if __name__ == "__main__":
    main()
