import math, os, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1080, 1920
FPS = 30
FONT_BLACK = "/home/user/videotest/assets/fonts/PlayfairDisplay-Black.ttf"
FONT_CAPTION = "/home/user/videotest/assets/fonts/Anton-Regular.ttf"
BG_SOURCE = "/home/user/videotest/assets/images/bg_source.jpg"
EMBLEM = "/home/user/videotest/assets/images/master_emblem.png"
TMP = "/home/user/videotest/segments/_frames"
SEG_DIR = "/home/user/videotest/segments"

WHITE = (255, 255, 255, 255)
PURPLE = (196, 140, 255, 255)


def ease_out_elastic(p):
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    c4 = (2 * math.pi) / 3
    return 2 ** (-10 * p) * math.sin((p * 10 - 0.75) * c4) + 1


def wobble_transform(t, start, dur=0.5):
    """Returns (scale, rotation_deg, alpha) for an element entering at `start`."""
    if t < start:
        return 0.0, 0.0, 0.0
    p = min((t - start) / dur, 1.0)
    scale = ease_out_elastic(p)
    rot = 6.0 * math.exp(-6 * p) * math.sin(p * 14)
    alpha = min(p / 0.25, 1.0)
    return scale, rot, alpha


def make_bg_frame(t, total_dur, zoom_to=1.10):
    bg = Image.open(BG_SOURCE).convert("RGB")
    bg = bg.filter(ImageFilter.GaussianBlur(18))
    bg = ImageEnhance.Brightness(bg).enhance(0.38)
    bg = ImageEnhance.Color(bg).enhance(1.15)
    overlay = Image.new("RGB", (W, H), (10, 8, 20))
    bg = Image.blend(bg, overlay, 0.35)
    z = 1.0 + (zoom_to - 1.0) * (t / total_dur)
    nw, nh = int(W * z), int(H * z)
    bg = bg.resize((nw, nh))
    x0 = (nw - W) // 2
    y0 = (nh - H) // 2
    bg = bg.crop((x0, y0, x0 + W, y0 + H))
    return bg.convert("RGBA")


def render_text_sprite(text, size, color, font_path=FONT_BLACK, glow=16):
    font = ImageFont.truetype(font_path, size)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=font)
    pad = glow * 3 + 20
    w = bbox[2] - bbox[0] + pad * 2
    h = bbox[3] - bbox[1] + pad * 2
    sprite = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=color)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(glow))
    sprite.alpha_composite(glow_layer)
    d2 = ImageDraw.Draw(sprite)
    d2.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=color)
    return sprite


def paste_sprite(base, sprite, cx, cy, scale, rot, alpha):
    if scale <= 0.001 or alpha <= 0.001:
        return
    w, h = sprite.size
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    s = sprite.resize((nw, nh), Image.LANCZOS)
    if abs(rot) > 0.05:
        s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = s.split()[3].point(lambda p: int(p * alpha))
        s.putalpha(a)
    x = int(cx - s.width / 2)
    y = int(cy - s.height / 2)
    base.alpha_composite(s, (x, y))


def render_caption_bar(base, text, cy, t, start, dur=0.4):
    if t < start:
        return
    scale, rot, alpha = wobble_transform(t, start, dur)
    sprite = render_text_sprite(text.upper(), 62, WHITE, font_path=FONT_CAPTION, glow=10)
    max_w = W - 100
    if sprite.width > max_w:
        ratio = max_w / sprite.width
        sprite = sprite.resize((int(sprite.width * ratio), int(sprite.height * ratio)))
    # dark pill behind caption for readability
    pill_w, pill_h = sprite.width + 50, sprite.height + 20
    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], radius=pill_h // 2, fill=(10, 8, 16, 160))
    paste_sprite(base, pill, W // 2, cy, min(scale, 1.0), 0, alpha * 0.9)
    paste_sprite(base, sprite, W // 2, cy, scale, rot, alpha)


def render_card(name, duration, headline_lines, sub_captions, emblem=False,
                 emblem_y=740, headline_y=560, sub_y=1520, caption_y=1720):
    frame_dir = f"{TMP}/{name}"
    if os.path.exists(frame_dir):
        shutil.rmtree(frame_dir)
    os.makedirs(frame_dir)

    headline_sprites = []
    y = headline_y
    for text, size, color, delay in headline_lines:
        sprite = render_text_sprite(text, size, color)
        headline_sprites.append((sprite, y + sprite.height // 2 - 40, delay))
        y += sprite.height - 40

    emblem_sprite = None
    if emblem:
        em = Image.open(EMBLEM).convert("RGBA").resize((620, 620))
        emblem_sprite = em

    n_frames = int(duration * FPS)
    for i in range(n_frames):
        t = i / FPS
        base = make_bg_frame(t, duration)

        if emblem_sprite is not None:
            scale, rot, alpha = wobble_transform(t, 0.15, 0.55)
            paste_sprite(base, emblem_sprite, W // 2, emblem_y, scale, rot, alpha)

        for sprite, cy, delay in headline_sprites:
            scale, rot, alpha = wobble_transform(t, delay, 0.5)
            paste_sprite(base, sprite, W // 2, cy, scale, rot, alpha)

        for text, size, color, cy, delay in sub_captions:
            scale, rot, alpha = wobble_transform(t, delay, 0.4)
            sprite = render_text_sprite(text, size, color)
            paste_sprite(base, sprite, W // 2, cy, scale, rot, alpha)

        cues = CAPTION_TRACKS.get(name, [])
        active = None
        for idx, (text, start, end) in enumerate(cues):
            next_start = cues[idx + 1][1] if idx + 1 < len(cues) else None
            linger = 0.25
            if next_start is not None:
                linger = max(0.0, min(linger, next_start - end))
            draw_end = end + linger
            if start <= t <= draw_end:
                active = (text, start, end, draw_end)
                break
        if active:
            text, start, end, draw_end = active
            a = 1.0
            if t > end and draw_end > end:
                a = max(0.0, 1.0 - (t - end) / (draw_end - end))
            scale, rot, alpha = wobble_transform(t, start, 0.3)
            alpha *= a
            sprite = render_text_sprite(text.upper(), 56, WHITE, font_path=FONT_CAPTION, glow=8)
            max_w = W - 120
            if sprite.width > max_w:
                ratio = max_w / sprite.width
                sprite = sprite.resize((int(sprite.width * ratio), int(sprite.height * ratio)))
            pill_w, pill_h = sprite.width + 60, sprite.height + 24
            pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
            pd = ImageDraw.Draw(pill)
            pd.rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], radius=pill_h // 2, fill=(10, 8, 16, 165))
            paste_sprite(base, pill, W // 2, caption_y, min(scale, 1.0), 0, alpha * 0.9)
            paste_sprite(base, sprite, W // 2, caption_y, scale, rot, alpha)

        base.convert("RGB").save(f"{frame_dir}/f_{i:05d}.jpg", quality=93)

    out = f"{SEG_DIR}/{name}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{frame_dir}/f_%05d.jpg",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p", out
    ], check=True, capture_output=True)
    shutil.rmtree(frame_dir)
    print("rendered", out)


CAPTION_TRACKS = {
    "seg1_intro_title": [
        ("SoloQ Tagebuch.", 0.05, 1.67),
        ("Tag eins.", 1.67, 2.79),
    ],
    "seg2_intro_rank": [
        ("Wir haben bei Master, 1026 LP, angefangen.", 0.0, 2.5),
        ("Heute haben wir 5 Games gespielt, davon 3 verloren.", 2.5, 5.85),
        ("Und das sind die Highlights.", 5.85, 7.55),
    ],
    "seg5_outro_rank": [
        ("Somit enden wir heute bei Master...", 0.05, 2.20),
        ("989 LP.", 2.20, 4.33),
        ("Hoffentlich läuft's morgen besser.", 4.33, 6.34),
    ],
    "seg7_twitch": [
        ("Schaut doch gerne auf Twitch vorbei:", 0.05, 2.2),
        ("twitch.tv/zelaan", 2.2, 4.06),
    ],
}


def main():
    render_card(
        "seg1_intro_title", 4.5,
        headline_lines=[
            ("SoloQ", 150, WHITE, 0.05),
            ("Tagebuch", 150, PURPLE, 0.20),
            ("Tag 1", 120, WHITE, 0.35),
        ],
        sub_captions=[],
        headline_y=520,
        caption_y=1740,
    )
    render_card(
        "seg2_intro_rank", 8.0,
        headline_lines=[
            ("Master", 130, WHITE, 0.65),
            ("1026 LP", 150, PURPLE, 0.80),
        ],
        sub_captions=[
            ("WIR STARTEN BEI", 62, WHITE, 350, 0.15),
            ("Heute: 5 Games · 3 verloren", 52, (230, 230, 230, 255), 1560, 2.55),
        ],
        emblem=True, emblem_y=780, headline_y=1150,
        caption_y=1780,
    )
    render_card(
        "seg5_outro_rank", 7.0,
        headline_lines=[
            ("Master", 130, WHITE, 0.55),
            ("989 LP", 150, PURPLE, 0.70),
        ],
        sub_captions=[
            ("WIR ENDEN HEUTE BEI", 62, WHITE, 300, 0.15),
        ],
        emblem=True, emblem_y=720, headline_y=1090,
        caption_y=1740,
    )
    render_card(
        "seg7_twitch", 4.5,
        headline_lines=[
            ("Schaut doch gerne", 76, WHITE, 0.10),
            ("auf Twitch vorbei", 76, WHITE, 0.25),
            ("twitch.tv/zelaan", 100, PURPLE, 0.55),
        ],
        sub_captions=[],
        headline_y=780,
        caption_y=1740,
    )


if __name__ == "__main__":
    main()
