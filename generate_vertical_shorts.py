import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

# This script reads movies from an NDJSON file (movies-data.ndjson by default),
# finds YouTube trailer URLs/IDs, downloads the full trailer, and creates a
# vertical 9:16 short by cropping 15% from the left and right (to punch-in),
# then scaling and center-cropping to 1080x1920.
#
# Requirements:
# - Python packages: yt_dlp (pip install yt-dlp)
# - ffmpeg available in PATH
#
# Example usage:
#   python generate_vertical_shorts.py \
#       --ndjson movies-data.ndjson \
#       --out-dir shorts \
#       --limit 20
#
# Notes:
# - The script keeps the full duration of the trailer (does not trim length).
# - If you want to restrict duration to <= 60s (YouTube Shorts), add --duration 60.
# - Existing outputs are skipped by default; use --overwrite to redo.

YOUTUBE_ID_RE = re.compile(r"(?:youtube\\.com/(?:watch\\?v=|embed/|shorts/)|youtu\\.be/)([A-Za-z0-9_-]{6,})")

# Global runtime-configurable options for bottom caption
BOTTOM_OUTER_MARGIN_Y = 40  # space between bottom of video and bottom band
BOTTOM_FONT_SIZE = None     # if None, reuse title font size

# Global toggles for background-only/visibility
BG_ONLY = False
NO_FOREGROUND = False
NO_TEXT = False
# Show semi-transparent bands behind texts
SHOW_BANDS = False
# Background styling defaults
BG_BRIGHTNESS = -0.12  # darker is negative (e.g., -0.25)
BG_CONTRAST = 1.0
BG_BLUR = 0.0  # gaussian blur sigma (e.g., 10-20)

def youtube_id_from_any(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    # If it's already an ID-like token (no slashes and short), accept
    if "/" not in value and len(value) >= 6 and len(value) <= 64 and re.match(r"^[A-Za-z0-9_-]+$", value):
        return value
    m = YOUTUBE_ID_RE.search(value)
    if m:
        return m.group(1)
    return None


def build_youtube_watch_url(yid: str) -> str:
    return f"https://www.youtube.com/watch?v={yid}"


def run_cmd(cmd: list[str]) -> int:
    print("$ ", " ".join(cmd))
    try:
        return subprocess.call(cmd)
    except FileNotFoundError as e:
        print(f"ERROR: Failed to execute command: {e}")
        return 127


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def download_youtube_video(yurl: str, out_dir: str, ffmpeg_path: Optional[str] = None, yt_extractor_client: Optional[str] = "default") -> Optional[str]:
    """Download video+audio into a single MP4/MKV file.
    Returns the local file path, or None on failure.
    """
    ensure_dir(out_dir)
    with tempfile.TemporaryDirectory() as tmpd:
        # Use yt-dlp to get best mp4/mkv; we'll remux to MP4 if needed.
        # Output template to temporary directory.
        out_tmpl = os.path.join(tmpd, "%(title)s-%(id)s.%(ext)s")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "-f", "bv*+ba/b",  # best video+audio
            "--merge-output-format", "mp4",
            "-o", out_tmpl,
            "--no-abort-on-unavailable-fragments",
            "--concurrent-fragments", "8",
            "--extractor-args", f"youtube:player_client={yt_extractor_client}",
        ]
        # Only pass ffmpeg-location if it actually resolves
        if ffmpeg_path:
            resolved = shutil.which(ffmpeg_path) or (ffmpeg_path if os.path.exists(ffmpeg_path) else None)
            if resolved:
                cmd.extend(["--ffmpeg-location", resolved])
        cmd.append(yurl)
        rc = run_cmd(cmd)
        if rc != 0:
            print(f"yt-dlp failed with code {rc}")
            return None
        # Find the downloaded file
        downloaded = None
        for name in os.listdir(tmpd):
            if name.lower().endswith((".mp4", ".mkv", ".webm", ".mov", ".m4v")):
                downloaded = os.path.join(tmpd, name)
                break
        if not downloaded:
            print("Downloaded file not found in temp dir")
            return None
        # Move to out_dir (originals)
        ensure_dir(out_dir)
        base = os.path.basename(downloaded)
        dest = os.path.join(out_dir, base)
        shutil.move(downloaded, dest)
        return dest


def _escape_drawtext_text(s: str) -> str:
    # Escape characters for ffmpeg drawtext text field.
    # Important: do NOT escape backslashes, so that sequences like \n are preserved for drawtext.
    return s.replace(':', '\\:').replace("'", "\\'").replace(',', '\\,')


def _escape_drawtext_path(s: str) -> str:
    # Escape characters for ffmpeg drawtext path-like fields (e.g., fontfile)
    # Backslashes and colons must be escaped. Quotes must be escaped.
    return s.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")


def make_vertical_short(src_path: str, dst_path: str, overwrite: bool = False, target_w: int = 1080, target_h: int = 1920, fps: Optional[int] = None, max_duration: Optional[int] = None, ffmpeg_bin: str = "ffmpeg", title_text: Optional[str] = None, font_file: Optional[str] = None, font_size: int = 48, font_color: str = "white", box_color: str = "black@0.5", box_borderw: int = 20, title_y: int = 40, title_band_h: int = 220, title_margin_x: int = 40, title_max_chars: Optional[int] = None, title_line_spacing: int = 0, title_align: str = "left") -> bool:
    """
    Create a 9:16 vertical video from src_path:
      1) Crop 15% from the left and 15% from the right (keep center 70%).
      2) Scale so that height <= target_h-title_band_h while preserving aspect ratio.
      3) Pad to target_w x target_h with a reserved top band (title_band_h) for text.
    Optionally set fps and trim to max_duration seconds.
    """
    if os.path.exists(dst_path) and not overwrite:
        print(f"Skip: exists {dst_path}")
        return True

    ensure_dir(os.path.dirname(dst_path) or ".")

    temp_textfile = None
    lines = None
    # If we have title text, wrap to multiple lines within the title band and margins.
    # Approximate width per char ~ 0.6*fontsize, so we can estimate how many chars fit per line.
    if title_text:
        if title_max_chars is None:
            approx_chars_fit = int(max(1, (target_w - 2 * title_margin_x) / max(1, font_size * 0.6)))
        else:
            approx_chars_fit = max(1, int(title_max_chars))
        words = str(title_text).split()
        lines = []
        cur = ""
        for w_ in words:
            if not cur:
                cur = w_
            elif len(cur) + 1 + len(w_) <= approx_chars_fit:
                cur += " " + w_
            else:
                lines.append(cur)
                cur = w_
        if cur:
            lines.append(cur)
        # We will render each line via a separate drawtext so each line can be truly centered

    # Define bottom band height and outer margin so we can reserve space during scale/pad
    bottom_band_h = 140
    bottom_outer_margin_y = BOTTOM_OUTER_MARGIN_Y

    # Build foreground (content) chain and separate text overlays
    fg_parts = [
        "crop=iw*0.7:ih:iw*0.15:0",     # remove 15% left+right
        # Scale content to fit inside target while preserving AR; no padding here (we'll overlay centered on BG)
        f"scale={target_w}:{max(1, target_h)}:force_original_aspect_ratio=decrease",
    ]
    text_parts = []

    # Draw a full-width (with side margins) semi-transparent band at the top for the title
    if title_text:
        # Optional background band (top)
        if SHOW_BANDS:
            drawbox = (
                f"drawbox=x={title_margin_x}:y=0:w={target_w - 2*title_margin_x}:h={title_band_h}:color={box_color}:t=fill"
            )
            text_parts.append(drawbox)
        font_clause = f":fontfile='{_escape_drawtext_path(font_file)}'" if font_file else ""

        # If we have multiple lines, render each as its own drawtext, so each line is horizontally centered individually
        if lines:
            # Baseline top y for the block of text to be vertically centered within the band
            # We approximate each line height as fontsize, with extra line_spacing between lines.
            # Total block height = n*fontsize + (n-1)*line_spacing
            n = len(lines)
            total_h = n * font_size + (n - 1) * title_line_spacing
            base_y = (title_band_h - total_h) / 2 + title_y
            for i, line in enumerate(lines):
                tt = _escape_drawtext_text(line)
                # Horizontal alignment per line
                if title_align == "left":
                    x_expr = f"{title_margin_x}"
                elif title_align == "right":
                    x_expr = f"w-tw-{title_margin_x}"
                else:  # center each line individually
                    x_expr = f"{title_margin_x} + (w - 2*{title_margin_x} - tw)/2"
                # y for each line: base_y + i*(fontsize + line_spacing)
                y_expr = f"{base_y} + {i}*({font_size} + {title_line_spacing})"
                drawtext = (
                    f"drawtext=text='{tt}'"
                    f"{font_clause}:x={x_expr}:y={y_expr}:fontsize={font_size}:fontcolor={font_color}:"
                    f"box=0:boxcolor={box_color}:boxborderw={box_borderw}"
                )
                text_parts.append(drawtext)
        else:
            # Single-line textfile or text
            # choose horizontal x by alignment
            if title_align == "left":
                x_expr = f"{title_margin_x}"
            elif title_align == "right":
                x_expr = f"w-tw-{title_margin_x}"
            else:  # center
                x_expr = f"{title_margin_x} + (w - 2*{title_margin_x} - tw)/2"
            if temp_textfile:
                tf_escaped = _escape_drawtext_path(temp_textfile)
                drawtext = (
                    f"drawtext=textfile='{tf_escaped}'"
                    f"{font_clause}:x={x_expr}:y=(({title_band_h})-th)/2+{title_y}:fontsize={font_size}:fontcolor={font_color}:"
                    f"box=0:boxcolor={box_color}:boxborderw={box_borderw}"
                )
            else:
                tt = _escape_drawtext_text(title_text)
                drawtext = (
                    f"drawtext=text='{tt}'"
                    f"{font_clause}:x={x_expr}:y=(({title_band_h})-th)/2+{title_y}:fontsize={font_size}:fontcolor={font_color}:"
                    f"box=0:boxcolor={box_color}:boxborderw={box_borderw}"
                )
            text_parts.append(drawtext)

    # Bottom call-to-action band and text
    bottom_text = "Смотрите полностью по ссылке в описании!!"
    bottom_band_h = 140
    bottom_margin_x = title_margin_x  # outer side margins for the band
    bottom_text_margin_x = 40         # inner text inset from the band's left/right
    bottom_text_margin_y = 12         # inner text inset from the band's top/bottom
    # Draw bottom band (full width minus side margins), anchored to bottom of the frame
    bottom_y0 = target_h - bottom_band_h - bottom_outer_margin_y
    if SHOW_BANDS:
        drawbox_bottom = (
            f"drawbox=x={bottom_margin_x}:y={bottom_y0}:w={target_w - 2*bottom_margin_x}:h={bottom_band_h}:color={box_color}:t=fill"
        )
        text_parts.append(drawbox_bottom)
    # Wrap bottom text to avoid clipping and center each line inside inner insets
    inner_w = target_w - 2 * (bottom_margin_x + bottom_text_margin_x)
    approx_chars_fit_bottom = max(1, int(inner_w / max(1, font_size * 0.6)))
    words_b = str(bottom_text).split()
    bottom_lines = []
    cur_b = ""
    for w_ in words_b:
        if not cur_b:
            cur_b = w_
        elif len(cur_b) + 1 + len(w_) <= approx_chars_fit_bottom:
            cur_b += " " + w_
        else:
            bottom_lines.append(cur_b)
            cur_b = w_
    if cur_b:
        bottom_lines.append(cur_b)

    n_b = len(bottom_lines)
    # use same spacing as title for consistency
    bfsize = (BOTTOM_FONT_SIZE or font_size)
    total_h_b = n_b * bfsize + (n_b - 1) * title_line_spacing
    base_y_b = bottom_y0 + bottom_text_margin_y + max(0, ((bottom_band_h - 2*bottom_text_margin_y) - total_h_b) / 2)

    for i, line_b in enumerate(bottom_lines):
        tt_b = _escape_drawtext_text(line_b)
        x_expr_b = f"{bottom_margin_x + bottom_text_margin_x} + (w - 2*{bottom_margin_x + bottom_text_margin_x} - tw)/2"
        y_expr_b = f"{base_y_b} + {i}*({bfsize} + {title_line_spacing})"
        drawtext_b = (
            f"drawtext=text='{tt_b}'"
            f"{font_clause if 'font_clause' in locals() else ''}:x={x_expr_b}:y={y_expr_b}:fontsize={bfsize}:fontcolor={font_color}:"
            f"box=0:boxcolor={box_color}:boxborderw=0:fix_bounds=1"
        )
        text_parts.append(drawtext_b)

    fg_chain = ",".join(fg_parts)
    texts_chain = ",".join(text_parts) if text_parts else None

    # Build background + foreground pipeline using filter_complex
    # Background: same trailer scaled to fill the 9:16 frame and slightly darkened/blurred
    bg_brightness = BG_BRIGHTNESS
    bg_contrast = BG_CONTRAST
    bg_blur_sigma = BG_BLUR  # set >0 to add subtle blur, e.g., 10-20
    bg_chain = f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},eq=brightness={bg_brightness}:contrast={bg_contrast}"
    if bg_blur_sigma and bg_blur_sigma > 0:
        bg_chain += f",gblur=sigma={bg_blur_sigma}"

    # Apply NO_TEXT/NO_FOREGROUND toggles
    final_texts_chain = texts_chain if not NO_TEXT else None
    final_fg_chain = fg_chain if not NO_FOREGROUND else None

    if BG_ONLY:
        # Background only for debugging
        filter_complex = (
            f"[0:v]{bg_chain}[outv]"
        )
    else:
        if final_fg_chain:
            if final_texts_chain:
                # Compose BG + FG first, then draw texts on the full frame to keep positions as before
                filter_complex = (
                    f"[0:v]split=2[vbg][vsrc];"
                    f"[vbg]{bg_chain}[bg];"
                    f"[vsrc]{final_fg_chain}[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
                    f"[base]{final_texts_chain}[outv]"
                )
            else:
                filter_complex = (
                    f"[0:v]split=2[vbg][vsrc];"
                    f"[vbg]{bg_chain}[bg];"
                    f"[vsrc]{final_fg_chain}[fg];"
                    f"[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
                )
        else:
            # no foreground, only background; optionally add texts over background
            if final_texts_chain:
                filter_complex = (
                    f"[0:v]{bg_chain}[base];"
                    f"[base]{final_texts_chain}[outv]"
                )
            else:
                filter_complex = (
                    f"[0:v]{bg_chain}[outv]"
                )

    cmd = [ffmpeg_bin, "-y" if overwrite else "-n", "-i", src_path,
           "-filter_complex", filter_complex,
           "-map", "[outv]", "-map", "0:a?",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "19",
           "-c:a", "aac", "-b:a", "128k"]

    # FPS control
    if fps:
        cmd.extend(["-r", str(fps)])

    # Duration trimming
    if max_duration and max_duration > 0:
        cmd.extend(["-t", str(max_duration)])

    cmd.append(dst_path)

    rc = run_cmd(cmd)

    # Cleanup
    if temp_textfile:
        try:
            os.unlink(temp_textfile)
        except OSError:
            pass

    return rc == 0


def process_ndjson(ndjson_path: str, out_dir: str, originals_dir: Optional[str] = None, overwrite: bool = False, limit: Optional[int] = None, fps: Optional[int] = None, max_duration: Optional[int] = None, ffmpeg_bin: str = "ffmpeg", yt_extractor_client: str = "default", title_template: Optional[str] = None, title_font_file: Optional[str] = None, title_font_size: int = 48, title_font_color: str = "white", title_box_color: str = "black@0.5", title_box_borderw: int = 20, title_y: int = 40, title_band_h: int = 220, title_margin_x: int = 40, title_max_chars: Optional[int] = None, title_line_spacing: int = 0, title_align: str = "left"):
    if not os.path.exists(ndjson_path):
        print(f"NDJSON not found: {ndjson_path}")
        return

    ensure_dir(out_dir)
    if originals_dir:
        ensure_dir(originals_dir)

    made = 0
    with open(ndjson_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                movie = json.loads(line)
            except json.JSONDecodeError:
                print("Skip malformed NDJSON line")
                continue

            mid = movie.get("id") or movie.get("kpId") or movie.get("slug")
            yid = movie.get("youtubeId")
            if not yid:
                yid = youtube_id_from_any(movie.get("trailer"))

            if not mid:
                print("Skip entry without 'id'")
                continue
            if not yid:
                print(f"[{mid}] No YouTube ID/URL; skip")
                continue

            yurl = build_youtube_watch_url(yid)

            # Determine output filenames
            out_name = f"{mid}.mp4"
            dst_path = os.path.join(out_dir, out_name)
            if os.path.exists(dst_path) and not overwrite:
                print(f"[{mid}] Short already exists -> {dst_path}")
                made += 1
                if limit and made >= limit:
                    break
                continue

            # Download original if needed
            local_src = None
            if originals_dir:
                # check for any existing original downloaded with same yid
                pattern_prefix = f"-{yid}."
                for name in os.listdir(originals_dir):
                    if name.endswith(f"-{yid}.mp4") or name.endswith(f"-{yid}.mkv") or name.endswith(f"-{yid}.webm") or name.endswith(f"-{yid}.mov") or name.endswith(f"-{yid}.m4v"):
                        local_src = os.path.join(originals_dir, name)
                        break
            if not local_src:
                # Pass ffmpeg path to yt-dlp so it can merge A/V
                ffmpeg_path = shutil.which(ffmpeg_bin) or ffmpeg_bin
                local_src = download_youtube_video(yurl, originals_dir or out_dir, ffmpeg_path=ffmpeg_path, yt_extractor_client=yt_extractor_client)
            if not local_src:
                print(f"[{mid}] Failed to download: {yurl}")
                continue

            # Build display title using template if provided, else fallback
            display_title = None
            title_fields = ["title", "name", "ru_title", "ruTitle", "originalTitle", "orig_title"]
            movie_title = None
            for tf in title_fields:
                if movie.get(tf):
                    movie_title = str(movie.get(tf))
                    break

            # Determine kind word from category (in Russian, genitive where natural):
            # filmy -> фильма, serialy -> сериала, multfilmy -> мультфильма, anime -> аниме (неизменяемое)
            category = (movie.get("category") or "").lower()
            kind_map = {
                "filmy": "фильма",
                "serialy": "сериала",
                "multfilmy": "мультфильма",
                "anime": "аниме",
            }
            kind_word = kind_map.get(category, "фильма")

            if movie_title:
                if title_template:
                    tpl = str(title_template)
                    # If template uses placeholders, honor them
                    if "{kind}" in tpl:
                        tpl = tpl.replace("{kind}", kind_word)
                    if "{title}" in tpl:
                        display_title = tpl.replace("{title}", movie_title)
                    else:
                        # Backward compatibility if user passes a simple word 'title'
                        display_title = tpl.replace("title", movie_title)
                    # If user hard-coded a type word, replace it with dynamic kind_word
                    # e.g., "Трейлер фильма {title}" -> "Трейлер сериала {title}" for serialy
                    display_title = re.sub(r"\b(фильма|мультфильма|аниме|сериала)\b", kind_word, display_title, count=1, flags=re.IGNORECASE)
                else:
                    display_title = f"Трейлер {kind_word} {movie_title}"

            ok = make_vertical_short(
                local_src,
                dst_path,
                overwrite=overwrite,
                fps=fps,
                max_duration=max_duration,
                ffmpeg_bin=ffmpeg_bin,
                title_text=display_title,
                font_file=title_font_file,
                font_size=title_font_size,
                font_color=title_font_color,
                box_color=title_box_color,
                box_borderw=title_box_borderw,
                title_y=title_y,
                title_band_h=title_band_h,
                title_margin_x=title_margin_x,
                title_max_chars=title_max_chars,
                title_line_spacing=title_line_spacing,
                title_align=title_align,
            )
            if ok:
                made += 1
                print(f"[{mid}] OK -> {dst_path}")
            else:
                print(f"[{mid}] Failed to render vertical short")

            if limit and made >= limit:
                break

    print(f"Done. Created/confirmed {made} shorts.")


def main():
    ap = argparse.ArgumentParser(description="Generate vertical 9:16 shorts from movies-data.ndjson trailers.")
    ap.add_argument("--ndjson", default="movies-data.ndjson", help="Path to NDJSON file with movies (default: movies-data.ndjson)")
    ap.add_argument("--out-dir", default="shorts", help="Directory to place generated shorts")
    ap.add_argument("--originals-dir", default="shorts_originals", help="Directory to store downloaded originals (for caching)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs")
    ap.add_argument("--limit", type=int, default=None, help="Process at most N entries")
    ap.add_argument("--fps", type=int, default=None, help="Force output FPS (e.g., 30)")
    ap.add_argument("--duration", type=int, default=None, help="Trim to max duration seconds (e.g., 60 for Shorts)")
    ap.add_argument("--ffmpeg", dest="ffmpeg_bin", default="ffmpeg", help="Path to ffmpeg binary or name in PATH (default: ffmpeg)")
    ap.add_argument("--yt-client", dest="yt_extractor_client", default="default", help="yt-dlp extractor client (default, android, web_safari, tv_embedded, etc.)")
    # Title overlay options
    ap.add_argument("--title-template", default=None, help="Template for title text, e.g. 'Трейлер фильма {title}'. If not set, auto builds.")
    ap.add_argument("--title-font-file", default=None, help="Path to TTF font file (required for Cyrillic on some systems). E.g., C:\\Windows\\Fonts\\arial.ttf")
    ap.add_argument("--title-font-size", type=int, default=48, help="Title font size (default: 48)")
    ap.add_argument("--title-font-color", default="white", help="Title font color (default: white)")
    ap.add_argument("--title-box-color", default="black@0.5", help="Title box color (default: black@0.5)")
    ap.add_argument("--title-box-borderw", type=int, default=20, help="Title box border width (default: 20)")
    ap.add_argument("--title-y", type=int, default=0, help="Fine Y offset inside the title band (default: 0)")
    ap.add_argument("--title-band-h", type=int, default=220, help="Reserved top band height in px for the title (default: 220)")
    ap.add_argument("--title-margin-x", type=int, default=40, help="Left/right margin for title band and text (default: 40)")
    ap.add_argument("--title-max-chars", type=int, default=None, help="Max characters per line for the title (auto by default)")
    ap.add_argument("--title-line-spacing", type=int, default=-8, help="Extra pixels between lines in multi-line title (negative to tighten, default: -8)")
    ap.add_argument("--title-align", choices=["left", "center", "right"], default="center", help="Horizontal alignment inside the band (default: center)")
    # Bottom caption options
    ap.add_argument("--bottom-outer-margin-y", type=int, default=40, help="Extra space between bottom of video and bottom band (default: 40)")
    ap.add_argument("--bottom-font-size", type=int, default=None, help="Font size for bottom caption (default: same as title-font-size)")
    # Debug/toggles
    ap.add_argument("--bg-only", action="store_true", help="Render only the background layer (for debugging)")
    ap.add_argument("--no-foreground", action="store_true", help="Hide the foreground (cropped content)")
    ap.add_argument("--no-text", action="store_true", help="Hide all text overlays")
    ap.add_argument("--show-bands", action="store_true", help="Show semi-transparent bands behind title and bottom text")
    # Background tuning
    ap.add_argument("--bg-brightness", type=float, default=None, help="Background brightness (negative to darken, e.g., -0.25)")
    ap.add_argument("--bg-contrast", type=float, default=None, help="Background contrast (e.g., 1.0)")
    ap.add_argument("--bg-blur", type=float, default=None, help="Background Gaussian blur sigma (e.g., 15)")

    args = ap.parse_args()

    # Expose bottom options via globals used in make_vertical_short
    global BOTTOM_OUTER_MARGIN_Y, BOTTOM_FONT_SIZE, BG_ONLY, NO_FOREGROUND, NO_TEXT, SHOW_BANDS, BG_BRIGHTNESS, BG_CONTRAST, BG_BLUR
    BOTTOM_OUTER_MARGIN_Y = args.bottom_outer_margin_y
    BOTTOM_FONT_SIZE = args.bottom_font_size
    BG_ONLY = args.bg_only
    NO_FOREGROUND = args.no_foreground
    NO_TEXT = args.no_text
    SHOW_BANDS = args.show_bands
    if args.bg_brightness is not None:
        BG_BRIGHTNESS = args.bg_brightness
    if args.bg_contrast is not None:
        BG_CONTRAST = args.bg_contrast
    if args.bg_blur is not None:
        BG_BLUR = args.bg_blur

    process_ndjson(
        ndjson_path=args.ndjson,
        out_dir=args.out_dir,
        originals_dir=args.originals_dir,
        overwrite=args.overwrite,
        limit=args.limit,
        fps=args.fps,
        max_duration=args.duration,
        ffmpeg_bin=args.ffmpeg_bin,
        yt_extractor_client=args.yt_extractor_client,
        title_template=args.title_template,
        title_font_file=args.title_font_file,
        title_font_size=args.title_font_size,
        title_font_color=args.title_font_color,
        title_box_color=args.title_box_color,
        title_box_borderw=args.title_box_borderw,
        title_y=args.title_y,
        title_band_h=args.title_band_h,
        title_margin_x=args.title_margin_x,
        title_max_chars=args.title_max_chars,
        title_line_spacing=args.title_line_spacing,
        title_align=args.title_align,
    )


if __name__ == "__main__":
    main()
