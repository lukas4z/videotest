from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920

def make_card(font_path, lines_colors, out_path, glow_color=(190, 100, 255)):
    img = Image.new("RGBA", (W, H), (20, 25, 20, 255))
    draw = ImageDraw.Draw(img)

    y = 200
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    for text, size, color in lines_colors:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) / 2 - bbox[0]
        # glow pass
        glow_draw.text((x, y), text, font=font, fill=color)
        y += (bbox[3] - bbox[1]) + 40

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(14))
    img = Image.alpha_composite(img, glow_layer)

    # sharp text pass on top
    draw = ImageDraw.Draw(img)
    y = 200
    for text, size, color in lines_colors:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) / 2 - bbox[0]
        draw.text((x, y), text, font=font, fill=color)
        y += (bbox[3] - bbox[1]) + 40

    img.convert("RGB").save(out_path, quality=95)

lines = [
    ("SoloQ", 130, (255, 255, 255, 255)),
    ("Tagebuch", 130, (200, 140, 255, 255)),
    ("Tag 1", 110, (255, 255, 255, 255)),
]

make_card("/home/user/videotest/assets/fonts/CinzelDecorative-Black.ttf", lines,
          "/home/user/videotest/assets/images/test_title_cinzel.jpg")
make_card("/home/user/videotest/assets/fonts/PlayfairDisplay-Black.ttf", lines,
          "/home/user/videotest/assets/images/test_title_playfair.jpg")
print("done")
