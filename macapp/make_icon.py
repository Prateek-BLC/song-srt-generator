"""Build the app icon and favicon from macapp/icon-source.png.

The source is a full-bleed 1024 px rounded square on black corners. This makes the
corners transparent, places the artwork on Apple's macOS icon grid (824 px inside a
1024 px canvas, with a soft shadow like other Dock icons), and writes:

  macapp/AppIcon.icns            the .app icon
  frontend/public/favicon.png    the browser favicon (artwork only, no padding)

Run with any Python that has Pillow (the app venv does):  python macapp/make_icon.py
Needs macOS `iconutil`. The outputs are committed, so this only runs when the icon changes.
"""

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

HERE = Path(__file__).parent
SOURCE = HERE / "icon-source.png"
FAVICON = HERE.parent / "frontend" / "public" / "favicon.png"
CANVAS, ARTWORK = 1024, 824  # Apple's macOS icon grid
INSET = 8  # px the "reference colour" is sampled inward from each edge pixel
PAD = 48  # temporary black margin while filtering


def cut_out(src: Image.Image) -> Image.Image:
    """Make the black corners transparent, keeping the source's own anti-aliased edge.

    An edge pixel is the artwork colour blended with black, so its opacity is its
    brightness relative to the artwork just inside it. Edge pixels get that inner
    colour back, so no dark fringe survives on a light Dock or tab.
    """
    src = src.convert("RGB")
    w, h = src.size
    # The source's outermost 2 px are darkened where the artwork meets the canvas
    # edge; take each from the pixel just inside it when that one is brighter.
    sp = src.load()
    for y in range(h):
        for x in range(w):
            if 2 <= x < w - 2 and 2 <= y < h - 2:
                continue
            inside = sp[min(max(x, 2), w - 3), min(max(y, 2), h - 3)]
            if max(inside) > max(sp[x, y]):
                sp[x, y] = inside
    # Black margin so the min/max filters below never touch the image border.
    padded = Image.new("RGB", (w + 2 * PAD, h + 2 * PAD))
    padded.paste(src, (PAD, PAD))
    return _cut_out_padded(padded).crop((PAD, PAD, PAD + w, PAD + h))


def _cut_out_padded(src: Image.Image) -> Image.Image:
    w, h = src.size
    bright = src.split()
    bright = ImageChops.lighter(ImageChops.lighter(bright[0], bright[1]), bright[2])  # max channel

    # Artwork colour just inside each pixel: shrink the opaque area, then spread its
    # colours back outward with repeated max filters (cheap "nearest interior" fill).
    solid = bright.point(lambda v: 255 if v > 60 else 0).filter(ImageFilter.MinFilter(2 * INSET + 1))
    inner = Image.composite(src, Image.new("RGB", src.size), solid)
    for _ in range(4):
        inner = Image.composite(inner, inner.filter(ImageFilter.MaxFilter(2 * INSET + 1)), solid)
        solid = solid.filter(ImageFilter.MaxFilter(2 * INSET + 1))
    inner_bright = inner.split()
    inner_bright = ImageChops.lighter(ImageChops.lighter(inner_bright[0], inner_bright[1]), inner_bright[2])

    out = Image.new("RGBA", (w, h))
    sp, ip, bp, ibp = src.load(), inner.load(), bright.load(), inner_bright.load()
    op = out.load()
    for y in range(h):
        for x in range(w):
            b, ref = bp[x, y], ibp[x, y]
            if b <= 8 or ref == 0:
                continue  # black corner, or nowhere near the artwork: stays transparent
            alpha = 255 if b >= ref else round(255 * b / ref)
            colour = sp[x, y] if alpha == 255 else ip[x, y]
            op[x, y] = colour + (alpha,)
    # Anything fully inside the rounded square is opaque, whatever its colour
    # (the dark caption bar must not turn see-through).
    core = bright.point(lambda v: 255 if v > 8 else 0).filter(ImageFilter.MinFilter(9))
    filled = Image.new("RGBA", (w, h))
    filled.paste(src.convert("RGBA"), (0, 0))
    return Image.composite(filled, out, core)


def on_grid(art: Image.Image) -> Image.Image:
    art = art.resize((ARTWORK, ARTWORK), Image.LANCZOS)
    offset = (CANVAS - ARTWORK) // 2
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))

    shadow_alpha = art.getchannel("A").point(lambda a: a * 0.35)
    shadow = Image.new("RGBA", art.size, (0, 0, 0, 0))
    shadow.putalpha(shadow_alpha)
    shadow_layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    shadow_layer.paste(shadow, (offset, offset + 10))
    canvas.alpha_composite(shadow_layer.filter(ImageFilter.GaussianBlur(14)))

    canvas.alpha_composite(art, (offset, offset))
    return canvas


def main():
    art = cut_out(Image.open(SOURCE))
    master = on_grid(art)
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "AppIcon.iconset"
        iconset.mkdir()
        for size in (16, 32, 128, 256, 512):
            master.resize((size, size), Image.LANCZOS).save(iconset / f"icon_{size}x{size}.png")
            master.resize((size * 2, size * 2), Image.LANCZOS).save(iconset / f"icon_{size}x{size}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(HERE / "AppIcon.icns")], check=True)
    # Favicon: the artwork edge to edge, so it isn't tiny in a browser tab.
    art.resize((128, 128), Image.LANCZOS).save(FAVICON, optimize=True)
    print(f"wrote {HERE / 'AppIcon.icns'} and {FAVICON}")


if __name__ == "__main__":
    main()
