"""Render the favicon files in src/static from src/static/favicon.svg (the logo; a plain star at 16 px).

    uv run --no-project --with playwright --with pillow python -I tools/make_favicons.py src/static
"""
import sys, io
from playwright.sync_api import sync_playwright
from PIL import Image
out = sys.argv[1]
star = '<path d="M50 10 L60 36.2 L88 37.6 L66.2 55.3 L73.5 82.4 L50 67 L26.5 82.4 L33.8 55.3 L12 37.6 L40 36.2 Z" fill="#a31f34" stroke="#a31f34" stroke-width="10" stroke-linejoin="round"/>'
full = open(out + "/favicon.svg").read()
def render(svg, px, bg="transparent", pad=0):
    html = f'<html><body style="margin:0;background:{bg}"><div style="width:{px}px;height:{px}px;box-sizing:border-box;padding:{pad}px">{svg.replace("<svg ", "<svg width=\"100%\" height=\"100%\" ", 1)}</div></body></html>'
    p.set_content(html); return Image.open(io.BytesIO(p.screenshot(clip={"x":0,"y":0,"width":px,"height":px}, omit_background=(bg=="transparent"))))
with sync_playwright() as pw:
    b = pw.chromium.launch(); p = b.new_page(viewport={"width":512,"height":512})
    small = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{star}</svg>'
    i16 = render(small, 16); i32 = render(full, 32); i48 = render(full, 48)
    i32.save(out + "/favicon-32.png")
    render(full, 180, bg="#ffffff", pad=22).convert("RGB").save(out + "/apple-touch-icon.png")
    i48.save(out + "/favicon.ico", sizes=[(16,16),(32,32),(48,48)], append_images=[i16, i32])
    b.close()
print("ok")
