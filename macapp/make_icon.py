"""Draw the app icon (indigo, matching the UI accent) and write macapp/AppIcon.icns.

Run with any Python that has Pillow (the app venv does):  python macapp/make_icon.py
Needs macOS `iconutil`. The .icns is committed, so this only runs when the icon changes.
"""

import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
SS = 4  # supersampling factor for smooth edges
SIZE = 1024
TOP = (107, 125, 255)     # --accent (dark theme)
BOTTOM = (44, 63, 209)    # --accent-hover (light theme)
WHITE = (244, 246, 255)   # --accent-ink


def draw_master() -> Image.Image:
    s = SIZE * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))

    # macOS Big Sur grid: 824 px rounded square centred on a 1024 canvas.
    inset, radius = 100 * SS, 185 * SS
    box = (inset, inset, s - inset, s - inset)

    shadow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (box[0], box[1] + 12 * SS, box[2], box[3] + 12 * SS), radius, fill=(10, 13, 40, 110))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18 * SS)))

    gradient = Image.new("RGBA", (s, s))
    gd = ImageDraw.Draw(gradient)
    for y in range(s):
        t = min(max((y - inset) / (s - 2 * inset), 0), 1)
        gd.line([(0, y), (s, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM)) + (255,))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius, fill=255)
    img.paste(gradient, (0, 0), mask)

    d = ImageDraw.Draw(img)
    cx = s // 2

    # Waveform: rounded vertical bars with a sung-phrase envelope.
    bars, bar_w, gap = 13, 26 * SS, 20 * SS
    total = bars * bar_w + (bars - 1) * gap
    mid_y = 430 * SS
    for i in range(bars):
        x = cx - total // 2 + i * (bar_w + gap)
        env = math.sin(math.pi * (i + 0.5) / bars)
        h = (60 + 240 * env * (0.65 + 0.35 * abs(math.sin(i * 1.7)))) * SS
        d.rounded_rectangle((x, mid_y - h / 2, x + bar_w, mid_y + h / 2), bar_w // 2, fill=WHITE + (255,))

    # Two caption bars underneath (the SRT).
    for y, w, alpha in ((660, 520, 255), (740, 360, 170)):
        y, w = y * SS, w * SS
        d.rounded_rectangle((cx - w // 2, y, cx + w // 2, y + 40 * SS), 20 * SS, fill=WHITE + (alpha,))

    return img.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    master = draw_master()
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "AppIcon.iconset"
        iconset.mkdir()
        for size in (16, 32, 128, 256, 512):
            master.resize((size, size), Image.LANCZOS).save(iconset / f"icon_{size}x{size}.png")
            master.resize((size * 2, size * 2), Image.LANCZOS).save(iconset / f"icon_{size}x{size}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(HERE / "AppIcon.icns")], check=True)
    print(f"wrote {HERE / 'AppIcon.icns'}")


if __name__ == "__main__":
    main()
