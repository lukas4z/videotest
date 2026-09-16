from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1080, 1920
FONT_BLACK = "/home/user/videotest/assets/fonts/PlayfairDisplay-Black.ttf"
BG_SOURCE = "/home/user/videotest/assets/images/bg_source.jpg"
EMBLEM = "/home/user/videotest/assets/images/master_emblem.png"
OUT_DIR = "/home/user/videotest/assets/images"

WHITE = (255, 255, 255, 255)
PURPLE = (196, 140, 255, 255)


def make_background():
    bg = Image.open(BG_SOURCE).convert("RGB")
    bg = bg.filter(ImageFilter.GaussianBlur(18))
    bg = ImageEnhance.Brightness(bg).enhance(0.38)
    bg = ImageEnhance.Color(bg).enhance(1.15)
    overlay = Image.new("RGB", (W, H), (10, 8, 20))
    bg = Image.blend(bg, overlay, 0.35)
    return bg.convert("RGBA")


def draw_glow_text(base, lines_colors, start_y, line_gap=40, blur=16, align_center=True):
    draw = ImageDraw.Draw(base)
    glow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    y = start_y
    positions = []
    for text, size, color in lines_colors:
        font = ImageFont.truetype(FONT_BLACK, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) / 2 - bbox[0] if align_center else 60
        positions.append((text, font, x, y, color))
        glow_draw.text((x, y), text, font=font, fill=color)
        y += (bbox[3] - bbox[1]) + line_gap
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(glow_layer)
    draw = ImageDraw.Draw(base)
    for text, font, x, y, color in positions:
        draw.text((x, y), text, font=font, fill=color)
    return y


def card_intro_title():
    bg = make_background()
    draw_glow_text(bg, [
        ("SoloQ", 150, WHITE),
        ("Tagebuch", 150, PURPLE),
        ("Tag 1", 120, WHITE),
    ], start_y=520, line_gap=50)
    bg.convert("RGB").save(f"{OUT_DIR}/card_intro_title.jpg", quality=95)


def card_intro_rank():
    bg = make_background()
    draw = ImageDraw.Draw(bg)

    label_font = ImageFont.truetype(FONT_BLACK, 70)
    bbox = draw.textbbox((0, 0), "WIR STARTEN BEI", font=label_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2 - bbox[0], 300), "WIR STARTEN BEI", font=label_font, fill=WHITE)

    emblem = Image.open(EMBLEM).convert("RGBA")
    emblem = emblem.resize((620, 620))
    bg.alpha_composite(emblem, ((W - 620) // 2, 460))

    draw_glow_text(bg, [
        ("Master", 130, WHITE),
        ("1026 LP", 150, PURPLE),
    ], start_y=1130, line_gap=30)

    sub_font = ImageFont.truetype(FONT_BLACK, 56)
    sub = "Heute: 5 Games · 3 verloren"
    bbox = draw.textbbox((0, 0), sub, font=sub_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2 - bbox[0], 1520), sub, font=sub_font, fill=(230, 230, 230, 255))

    bg.convert("RGB").save(f"{OUT_DIR}/card_intro_rank.jpg", quality=95)


def card_outro_rank():
    bg = make_background()
    draw = ImageDraw.Draw(bg)

    label_font = ImageFont.truetype(FONT_BLACK, 70)
    text = "WIR ENDEN HEUTE BEI"
    bbox = draw.textbbox((0, 0), text, font=label_font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2 - bbox[0], 260), text, font=label_font, fill=WHITE)

    emblem = Image.open(EMBLEM).convert("RGBA")
    emblem = emblem.resize((620, 620))
    bg.alpha_composite(emblem, ((W - 620) // 2, 420))

    draw_glow_text(bg, [
        ("Master", 130, WHITE),
        ("989 LP", 150, PURPLE),
    ], start_y=1090, line_gap=30)

    sub_font = ImageFont.truetype(FONT_BLACK, 58)
    sub_lines = ["Hoffentlich läuft's", "morgen besser."]
    y = 1500
    for sub in sub_lines:
        bbox = draw.textbbox((0, 0), sub, font=sub_font)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) / 2 - bbox[0], y), sub, font=sub_font, fill=(230, 230, 230, 255))
        y += 80

    bg.convert("RGB").save(f"{OUT_DIR}/card_outro_rank.jpg", quality=95)


def card_twitch():
    bg = make_background()
    draw_glow_text(bg, [
        ("Schaut doch gerne", 80, WHITE),
        ("auf Twitch vorbei", 80, WHITE),
    ], start_y=760, line_gap=30)

    draw = ImageDraw.Draw(bg)
    url_font = ImageFont.truetype(FONT_BLACK, 100)
    text = "twitch.tv/zelaan"
    bbox = draw.textbbox((0, 0), text, font=url_font)
    tw = bbox[2] - bbox[0]
    glow_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.text(((W - tw) / 2 - bbox[0], 1000), text, font=url_font, fill=PURPLE)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(18))
    bg.alpha_composite(glow_layer)
    draw = ImageDraw.Draw(bg)
    draw.text(((W - tw) / 2 - bbox[0], 1000), text, font=url_font, fill=PURPLE)

    bg.convert("RGB").save(f"{OUT_DIR}/card_twitch.jpg", quality=95)


card_intro_title()
card_intro_rank()
card_outro_rank()
card_twitch()
print("done")
