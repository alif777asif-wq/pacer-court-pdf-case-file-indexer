"""Render the HTML boards to 4000 x 3000 PNG + JPG, measure layout, and write portfolio/export-report.json.

Run after build_images.py: python portfolio/export_images.py   (needs playwright + chromium)
"""
import io
import json
import pathlib

from PIL import Image, ImageCms, JpegImagePlugin
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML, EXPORT = ROOT / "portfolio/html", ROOT / "portfolio/export"
EXPORT.mkdir(exist_ok=True)
(ROOT / "portfolio/thumbs").mkdir(exist_ok=True)
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()

MEASURE = """() => {
  const out = {safe: [], core: [], overflow: [], minFont: 999, fonts: [], overlaps: []};
  const inside = (r, l, t, rt, b) => r.left >= l - 0.5 && r.top >= t - 0.5 && r.right <= rt + 0.5 && r.bottom <= b + 0.5;
  document.querySelectorAll('[data-z]').forEach(el => {
    const r = el.getBoundingClientRect(), z = el.dataset.z;
    if (z === 'safe' && !inside(r, 70, 70, 1210, 890)) out.safe.push(el.className + ' ' + [r.left, r.top, r.right, r.bottom].map(Math.round));
    if (z === 'core' && !inside(r, 160, 120, 1120, 840)) out.core.push(el.className + el.tagName + ' ' + [r.left, r.top, r.right, r.bottom].map(Math.round));
  });
  document.querySelectorAll('.core *, .top, .foot, .top *, .foot *').forEach(el => {
    if (el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).display !== 'inline') out.overflow.push(el.tagName + '.' + el.className);
    const hasText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (hasText) out.minFont = Math.min(out.minFont, parseFloat(getComputedStyle(el).fontSize));
    const r = el.getBoundingClientRect();
    if (hasText && (r.right > 1210.5 || r.bottom > 890.5 || r.left < 69.5 || r.top < 69.5)) out.safe.push('text outside safe zone: ' + el.tagName + '.' + el.className);
  });
  const h = document.querySelector('h1,h2'), st = document.querySelector('.stamp');
  if (h && st) { const a = h.getBoundingClientRect(), b = st.getBoundingClientRect();
    const hr = document.createRange(); hr.selectNodeContents(h); const t = hr.getBoundingClientRect();
    if (!(t.right < b.left || t.left > b.right || t.bottom < b.top || t.top > b.bottom)) out.overlaps.push('headline text overlaps stamp'); }
  document.fonts.forEach(f => out.fonts.push(f.family + ' ' + f.weight + ' ' + f.style + ' ' + f.status));
  return out;
}"""


def measure_file(path: pathlib.Path) -> dict:
    """Re-open an exported file and record what is really in it."""
    im = Image.open(path)
    prof = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(im.info["icc_profile"]))).strip() if "icc_profile" in im.info else None
    out = {"width": im.size[0], "height": im.size[1], "dpi_tag": [round(v) for v in im.info.get("dpi", (0, 0))],
           "icc_profile": prof, "bytes": path.stat().st_size, "mode": im.mode}
    if im.format == "JPEG":
        out["chroma_subsampling"] = {0: "4:4:4", 1: "4:2:2", 2: "4:2:0"}.get(JpegImagePlugin.get_sampling(im), "unknown")
        out["exceeds_5MB"] = path.stat().st_size > 5_000_000
    return out


def main():
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1280, "height": 960}, device_scale_factor=3.125)
        for html in sorted(HTML.glob("*.html")):
            page = ctx.new_page()
            page.goto(html.as_uri())
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(300)
            m = page.evaluate(MEASURE)
            png = page.screenshot(type="png", clip={"x": 0, "y": 0, "width": 1280, "height": 960})
            img = Image.open(io.BytesIO(png)).convert("RGB")
            assert img.size == (4000, 3000), img.size
            stem = html.stem
            img.save(EXPORT / f"{stem}.png", dpi=(300, 300), icc_profile=SRGB, optimize=True)
            img.save(EXPORT / f"{stem}.jpg", quality=100, subsampling=0, dpi=(300, 300), icc_profile=SRGB)
            img.resize((300, 225), Image.LANCZOS).save(ROOT / f"portfolio/thumbs/{stem}.png")
            report[stem] = {"size": list(img.size), "png_bytes": (EXPORT / f"{stem}.png").stat().st_size,
                            "jpg_bytes": (EXPORT / f"{stem}.jpg").stat().st_size,
                            "png": measure_file(EXPORT / f"{stem}.png"), "jpg": measure_file(EXPORT / f"{stem}.jpg"),
                            "outside_safe_zone": m["safe"],
                            "outside_core_zone": m["core"], "overflowing_elements": m["overflow"],
                            "smallest_text_px": m["minFont"], "overlaps": m["overlaps"],
                            "fonts": sorted(set(m["fonts"]))}
            page.close()
        report["_chromium"] = browser.version
        browser.close()
    (ROOT / "portfolio/export-report.json").write_text(json.dumps(report, indent=2) + "\n")
    for k, v in report.items():
        if k.startswith("_"):
            continue
        print(k, v["size"], "png %.2f MB" % (v["png_bytes"] / 1e6), "jpg %.2f MB" % (v["jpg_bytes"] / 1e6),
              "| safe:", v["outside_safe_zone"], "core:", v["outside_core_zone"], "overflow:", v["overflowing_elements"],
              "overlap:", v["overlaps"], "min px:", v["smallest_text_px"])


if __name__ == "__main__":
    main()
