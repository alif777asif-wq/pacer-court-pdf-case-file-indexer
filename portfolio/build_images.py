"""Generate the five portfolio images (1280 x 960 HTML boards) from the measured results.

Every figure on every board is read from proof/outputs/results.json, proof/outputs/records.json,
proof/test-summary.json or proof/env.json. Only headlines and labels are typed text.
Run: python portfolio/build_images.py   (writes portfolio/html/*.html and portfolio/build-report.json)
"""
import base64
import json
import os
import pathlib
import re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/alif777asif-wq/pacer-court-pdf-case-file-indexer"
P = ROOT / "proof"
res = json.loads((P / "outputs/results.json").read_text())
recs = json.loads((P / "outputs/records.json").read_text())
tests = json.loads((P / "test-summary.json").read_text())
env = json.loads((P / "env.json").read_text())
V = res["verification"]

# ---------------------------------------------------------------- palette and contrast (WCAG 2.x)
PAL = {"ink": "#0E1A2B", "paper": "#F4F0E6", "text_paper": "#101B2C", "muted_dark": "#A9B5C6",
       "muted_paper": "#4B5565", "amber": "#EBAA3A", "amber_deep": "#8A5200"}


def lum(hex_):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


PAIRS = {"text on ink": (PAL["paper"], PAL["ink"]), "muted on ink": (PAL["muted_dark"], PAL["ink"]),
         "amber on ink": (PAL["amber"], PAL["ink"]), "text on paper": (PAL["text_paper"], PAL["paper"]),
         "muted on paper": (PAL["muted_paper"], PAL["paper"]), "deep amber on paper": (PAL["amber_deep"], PAL["paper"])}
CONTRAST = {k: ratio(*v) for k, v in PAIRS.items()}
assert all(v >= 4.5 for v in CONTRAST.values()), CONTRAST

# ---------------------------------------------------------------- fonts embedded as base64 (SIL OFL 1.1)
FONTS = [("Newsreader", 400, "normal", "newsreader-latin-400-normal"), ("Newsreader", 500, "normal", "newsreader-latin-500-normal"),
         ("Newsreader", 400, "italic", "newsreader-latin-400-italic"), ("IBM Plex Mono", 400, "normal", "ibm-plex-mono-latin-400-normal"),
         ("IBM Plex Mono", 500, "normal", "ibm-plex-mono-latin-500-normal")]
font_css = "".join(
    '@font-face{font-family:"%s";font-weight:%d;font-style:%s;src:url(data:font/woff2;base64,%s) format("woff2")}'
    % (fam, w, st, base64.b64encode((ROOT / "portfolio/fonts" / (f + ".woff2")).read_bytes()).decode())
    for fam, w, st, f in FONTS)

CSS = """
*{box-sizing:border-box;margin:0;padding:0}html,body{width:1280px;height:960px;overflow:hidden}
.dark{--bg:%(ink)s;--fg:%(paper)s;--muted:%(muted_dark)s;--acc:%(amber)s;--rule:rgba(244,240,230,.055);--line:rgba(244,240,230,.24);--track:rgba(244,240,230,.12)}
.light{--bg:%(paper)s;--fg:%(text_paper)s;--muted:%(muted_paper)s;--acc:%(amber_deep)s;--rule:rgba(16,27,44,.07);--line:rgba(16,27,44,.28);--track:rgba(16,27,44,.10)}
.board{position:relative;width:1280px;height:960px;overflow:hidden;background-color:var(--bg);color:var(--fg);font-family:Newsreader,Georgia,serif;font-variant-numeric:tabular-nums lining-nums;
background-image:repeating-linear-gradient(to bottom,transparent 0 47px,var(--rule) 47px 48px)}
.board:before{content:"";position:absolute;left:118px;top:0;bottom:0;width:2px;background:var(--acc);opacity:.5}
.m{font-family:"IBM Plex Mono",ui-monospace,monospace}
.top,.foot{position:absolute;left:160px;right:160px;display:flex;justify-content:space-between;font:500 18px/1 "IBM Plex Mono",monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
.top{top:72px}.foot{bottom:72px;font-weight:400;font-size:16px;letter-spacing:.03em;text-transform:none}
.core{position:absolute;left:160px;top:120px;width:960px;height:720px}
h1,h2{font-weight:500;letter-spacing:-.015em;line-height:1.04}
.lab{font:500 18px/1 "IBM Plex Mono",monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
.acc{color:var(--acc)}.nw{white-space:nowrap}
.bar{height:16px;background:var(--track);position:relative}.bar b{position:absolute;left:0;top:0;bottom:0;background:var(--acc)}
""" % PAL


def page(theme, label, idx, body, foot):
    return ('<!-- Source repository: ' + REPO_URL + ' (available only after the push command in the entry sheet has been run) -->\n'
            '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>%s</title><style>%s%s%s</style></head><body>'
            '<div class="board %s"><div class="top" data-z="safe"><span>%s</span><span>%02d / 05</span></div>'
            '<div class="core">%s</div><div class="foot" data-z="safe">%s</div></div></body></html>'
            % (label, font_css, CSS, EXTRA[idx], theme, label, idx, body, foot))


corp, ext, ide, cls = res["corpus"], res["extraction"], res["identification"], res["classification"]
ce, fv, ps, ci, rl = V["cross_extractor"], V["filename_vs_text"], V["planted_error_selftest"], V["copy_integrity"], V["reference_labels"]
FOOT = "Source code linked in project · %d real public filings · pinned by commit and SHA-256" % corp["documents"]
EXTRA = {1: """
h1{font-size:76px;margin-bottom:34px}.stamp{position:absolute;right:8px;top:14px;width:262px;border:2px solid var(--acc);padding:12px 14px;
font:500 17px/1.5 "IBM Plex Mono",monospace;letter-spacing:.05em;color:var(--acc);transform:rotate(-2deg);text-transform:uppercase}
.num{font-size:292px;line-height:.82;font-weight:400;letter-spacing:-.03em;color:var(--acc);margin:0 0 20px 0}
.lede{font-style:italic;font-size:36px;line-height:1.2;margin-bottom:34px}.chips{display:flex;gap:44px;font:500 22px/1 "IBM Plex Mono",monospace}
.chips span{border-top:2px solid var(--line);padding-top:14px}""",
2: """
h2{font-size:56px;margin-bottom:34px}.g{display:grid;grid-template-columns:372px 40px 1fr;align-items:center;height:40px;border-top:1px solid var(--line);font:400 18px/1 "IBM Plex Mono",monospace;white-space:nowrap}
.g.h{height:44px;border-top:0}.g span:first-child{color:var(--muted)}.ar{display:block;width:24px;height:2px;background:var(--acc);position:relative}
.ar:after{content:"";position:absolute;right:-1px;top:-5px;border:6px solid transparent;border-left:9px solid var(--acc);border-right:0}.fl span:last-child{color:var(--acc);font-weight:500}""",
3: """
h2{font-size:64px;margin-bottom:40px}.r{display:grid;grid-template-columns:230px 1fr 150px;align-items:start;height:92px;border-top:1px solid var(--line);padding-top:18px}
.r .n{font:500 22px/1.1 "IBM Plex Mono",monospace;letter-spacing:.04em;text-transform:uppercase}.r .d{font-size:24px;font-style:italic;color:var(--muted);margin-top:12px;white-space:nowrap}
.r .v{font:500 28px/1 "IBM Plex Mono",monospace;text-align:right;color:var(--acc);white-space:nowrap}.ax{display:flex;justify-content:space-between;margin:2px 150px 0 230px;font:400 17px/1 "IBM Plex Mono",monospace;color:var(--muted);border-top:2px solid var(--fg);padding-top:10px}
.tot{margin-top:22px;display:flex;justify-content:space-between;font:500 24px/1 "IBM Plex Mono",monospace}""",
4: """
h2{font-size:56px;margin-bottom:34px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:64px}.lab{margin-bottom:12px}
.it{height:64px;border-top:1px solid var(--line);padding-top:12px}.it .t{display:flex;justify-content:space-between;align-items:baseline;font-size:27px;margin-bottom:9px;white-space:nowrap}
.it .t b{font:500 24px/1 "IBM Plex Mono",monospace;color:var(--acc)}.sub{font-style:italic;font-size:27px;color:var(--muted);margin-bottom:6px;white-space:nowrap}""",
5: """
h2{font-size:64px;margin-bottom:34px}.split{display:grid;grid-template-columns:280px 1fr;gap:40px}
.pan{border:2px solid var(--line);padding:26px;height:560px;display:flex;flex-direction:column}.big{font-size:172px;line-height:.9;letter-spacing:-.03em;color:var(--acc);margin:26px 0 8px}
.of{font-size:30px;font-style:italic}.env{font:400 18px/1.75 "IBM Plex Mono",monospace;color:var(--muted);margin-top:auto;border-top:1px solid var(--line);padding-top:16px;white-space:nowrap}
.k{display:grid;grid-template-columns:152px 1fr;height:112px;border-top:1px solid var(--line);align-items:center}
.k .f{font-size:46px;letter-spacing:-.02em;color:var(--acc);white-space:nowrap}.k .f.o{color:var(--fg)}
.k .l{font-size:26px;line-height:1.1;white-space:nowrap}.k .e{font:400 17px/1.2 "IBM Plex Mono",monospace;color:var(--muted);margin-top:9px;white-space:nowrap}"""
}

# ------------------------------------------------------------------ board 1: outcome
complaint = next(r for r in recs if r["doc_type"] == "Complaint")
b1 = ('<div class="stamp nw" data-z="core">Case %s<br>Document %s<br>Filed %s<br>Page %d of %d</div>'
      '<h1 data-z="core">Federal court PDFs,<br>indexed.</h1>'
      '<div class="num" data-z="core">%d/%d</div>'
      '<p class="lede" data-z="core">case numbers read identically by two independent PDF readers</p>'
      '<div class="chips" data-z="core"><span>%d real PDFs</span><span>%d courts</span><span>%s s end to end</span></div>'
      % (complaint["case_number"], complaint["doc_number"], complaint["filed"], complaint["stamp_page"], complaint["stamp_total"],
         ce["case_number_agree"], ce["documents_compared"], corp["documents"], len(corp["courts"]), res["run_seconds"]))

# ------------------------------------------------------------------ board 2: before / after
rows = ""
for r in recs:
    name = re.sub(r"^[a-z]+__", "", r["filename"])
    dest = os.path.dirname(r["new_path"]) + " · " + r["doc_type"]
    rows += '<div class="g %s"><span>%s</span><i class="ar"></i><span>%s</span></div>' % ("fl" if r["status"] != "ok" else "", name, dest)
b2 = ('<h2 data-z="core">Loose PDFs in.<br>A filed case record out.</h2>'
      '<div class="g h" data-z="core"><span class="lab">Input file</span><i></i><span class="lab">Organised as court/case · type</span></div>'
      '<div data-z="core">%s</div>' % rows)

# ------------------------------------------------------------------ board 3: stages
STAGE = {"1 read + OCR": ("read + OCR", "poppler text layer, Tesseract on scanned pages"),
         "2 organise": ("organise", "court/case folders, every copy hash-checked"),
         "3 report": ("report", "CSV case index"),
         "4 verify": ("verify", "independent checks and planted-error test"),
         "5 workbook": ("workbook", "Excel index, case roll-up, exceptions sheet")}
sec = res["stage_seconds"]
total = res["run_seconds"]
rows, t = "", 0.0
for k, (name, desc) in STAGE.items():
    sv = sec[k]
    val = "%s s" % sv
    left, width = 100 * t / total, (0 if sv == 0 else max(0.6, 100 * sv / total))
    rows += ('<div class="r"><span class="n">%s</span><div><div class="bar"><b style="left:%.3f%%;width:%.3f%%"></b></div><div class="d">%s</div></div>'
             '<span class="v">%s</span></div>' % (name, left, width, desc, val))
    t += sv
b3 = ('<h2 data-z="core">Five stages, each one timed.</h2><div data-z="core">%s'
      '<div class="ax"><span>0 s</span><span>%s s</span></div>'
      '<div class="tot"><span>Total</span><span>%d PDFs · %d pages</span></div></div>'
      % (rows, total, corp["documents"], corp["pages"]))

# ------------------------------------------------------------------ board 4: types and flags
types = sorted(cls["by_type"].items(), key=lambda kv: (-kv[1], kv[0]))
reasons = Counter(x for r in recs for x in r["review_reasons"])
reason_rows = sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0]))


def bars(items, top):
    return "".join('<div class="it"><div class="t"><span>%s</span><b>%d</b></div><div class="bar"><b style="width:%.2f%%"></b></div></div>'
                   % (k[0].upper() + k[1:], v, 100 * v / top) for k, v in items)


b4 = ('<h2 data-z="core">Typed and routed.<br>Doubtful files flagged.</h2><div class="cols" data-z="core">'
      '<div><div class="lab">Document types · %d files</div>%s</div>'
      '<div><div class="lab">Why %d files were flagged</div>%s</div></div>'
      % (corp["documents"], bars(types, max(v for _, v in types)), res["review"]["needs_review"],
         bars(reason_rows, max(v for _, v in types))))

# ------------------------------------------------------------------ board 5: proof ledger
miss = rl["misses"][0] if rl["misses"] else None
LEDGER = [
    ("%d/%d" % (fv["agree"], fv["fields_compared"]), "stamp fields match an independent source", "court and document number vs file names", fv["agree"] == fv["fields_compared"]),
    ("%d/%d" % (ce["case_number_agree"], ce["documents_compared"]), "case numbers agree across two readers", "poppler vs pdfminer.six", ce["case_number_agree"] == ce["documents_compared"]),
    ("%d/%d" % (ps["errors_caught"], ps["errors_planted"]), "planted errors caught", "checks fail when inputs are corrupted on purpose", ps["errors_caught"] == ps["errors_planted"]),
    ("%d/%d" % (ci["files_checked"] - len(ci["mismatches"]), ci["files_checked"]), "organised copies byte-identical", "SHA-256 of every copied PDF", not ci["mismatches"]),
    ("%d/%d" % (rl["correct"], rl["documents_scored"]), "document types match hand labels",
     ("miss: a %s, sent to review" % rl["misses"][0]["reference"].lower()) if rl["misses"] else "no misses", not rl["misses"]),
]
rows = "".join('<div class="k"><span class="f %s">%s</span><div><div class="l">%s</div><div class="e">%s</div></div></div>'
               % ("" if ok else "o", n, t, e) for n, t, e, ok in LEDGER)
pan = ('<div class="pan" data-z="core"><div class="lab">Automated tests</div><div class="big">%d</div><div class="of">of %d pass</div>'
       '<div class="env">Python %s<br>poppler %s<br>Tesseract %s<br>pytest %s</div></div>'
       % (tests["passed"], tests["tests"], env["python"], env["poppler_pdftotext"].split()[-1], env["tesseract"].split()[-1], env["packages"]["pytest"]))
b5 = '<h2 data-z="core">Verified, not assumed.</h2><div class="split" data-z="core">%s<div>%s</div></div>' % (pan, rows)

BOARDS = [
    ("1-federal-court-pdf-indexer-python-outcome", page("dark", "Python toolkit · federal court records", 1, b1, FOOT)),
    ("2-court-pdf-organiser-before-after", page("light", "The input and the output", 2, b2, "Input names and the folders built from them · amber rows were flagged for review")),
    ("3-court-pdf-automation-pipeline-timing", page("dark", "How it runs", 3, b3, "Stage timings from one measured run on %s" % env["recorded_at"][:10])),
    ("4-court-document-classification-results", page("light", "What it found", 4, b4, "Counts from the case index · flagged files carry a written reason, not a guess")),
    ("5-court-pdf-indexer-verified-tests", page("dark", "Proof", 5, b5, "Run %s · rules were written on these same files, so scores describe this set only" % env["recorded_at"][:10])),
]
out = ROOT / "portfolio/html"
out.mkdir(exist_ok=True)
for name, html in BOARDS:
    (out / f"{name}.html").write_text(html, encoding="utf-8")
(ROOT / "portfolio/build-report.json").write_text(json.dumps({"contrast_ratios": CONTRAST, "palette": PAL,
                                                               "boards": [n for n, _ in BOARDS]}, indent=2) + "\n")
print("built", [n for n, _ in BOARDS], CONTRAST)
