#!/usr/bin/env python3
"""綠點時間軸（方案 A 墨韻留白）淺深兩版 SVG。

資料：同目錄 contributions.json（fetch_days.py 產生）。
輸出：repo 的 assets/timeline-{light,dark}.svg。每張都自足（字型子集內嵌、無外部資源），
README 用 <picture> 依 GitHub 主題切換深淺色。同樣輸入產出同樣位元組。
"""
import base64
import datetime as dt
import io
import json
import math
import random
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
DATA = HERE / "contributions.json"
FONTS = HERE / "fonts"
OUT = HERE.parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

W = 846  # GitHub profile README 內容寬（2026-09-25 實測）

# ── 資料與校驗 ─────────────────────────────────────
raw = json.loads(DATA.read_text(encoding="utf-8"))
DAYS = {dt.date.fromisoformat(d): n for d, n in raw["days"]}
TODAY = dt.date.fromisoformat(raw["fetched_at"][:10])
ORDER = sorted(DAYS)
FIRST, SECOND = ORDER[0], ORDER[1]
TOTAL = sum(DAYS.values())
GAP = (SECOND - FIRST).days
assert (FIRST, SECOND, GAP) == (dt.date(2012, 12, 4), dt.date(2025, 6, 22), 4583), \
    "第一、第二個綠點和預期不符"
# 總數只會變多：比 2026-09-25 的快照還少，就是資料抓錯了
assert TOTAL >= 3724 and len(DAYS) >= 333, "貢獻總數比 2026-09-25 的快照還少"

# 回歸後按週彙總（週日起算；2025-06-22 剛好是週日）
N_WEEKS = (TODAY - SECOND).days // 7 + 1
WEEKS = [0] * N_WEEKS
for d, n in DAYS.items():
    if d >= SECOND:
        WEEKS[(d - SECOND).days // 7] += n
assert sum(WEEKS) == TOTAL - 1
MAX_WEEK = max(WEEKS)


def fmt(n):
    return f"{n:,}"


# ── 小工具 ───────────────────────────────────────
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


EASE = "cubic-bezier(.2,.7,.2,1)"


def anim(name, dur, delay, ease=EASE):
    return f' style="animation:{name} {dur}s {ease} {delay:.2f}s backwards"'


MOTION = (
    "@keyframes fade{from{opacity:0}}"
    "@keyframes bloom{from{opacity:0;transform:scale(.2)}}"
    "@keyframes rise{from{opacity:0;transform:translateY(6px)}}"
    "@keyframes draw{from{stroke-dashoffset:1}}"
    ".b{transform-box:fill-box;transform-origin:center}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)


class Doc:
    """極簡 SVG 組裝器：收集 defs / css / 圖層，並記下每種字型用到的字。"""

    def __init__(self, h, title, desc):
        self.h, self.title, self.desc = h, title, desc
        self.defs, self.css, self.body = [], [MOTION], []
        self.used = defaultdict(set)

    def add(self, s):
        self.body.append(s)

    def text(self, x, y, s, face, size, fill, anchor="start", weight=400, a=""):
        self.used[(face, weight)].update(s)
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{face}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{a}>{esc(s)}</text>')

    def render(self, fonts):
        faces = []
        for (face, weight), chars in sorted(self.used.items()):
            family, file = fonts[(face, weight)]
            faces.append(font_face(family, file, "".join(sorted(chars)), weight))
        css = "".join(faces) + "".join(self.css)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" '
                f'viewBox="0 0 {W} {self.h}" role="img" aria-labelledby="t d">'
                f'<title id="t">{esc(self.title)}</title><desc id="d">{esc(self.desc)}</desc>'
                f'<defs>{"".join(self.defs)}<style><![CDATA[{css}]]></style></defs>'
                f'{"".join(self.body)}</svg>')


def font_face(family, file, text, weight):
    # 不重算 head.modified：同樣輸入要產出同樣位元組，排程才不會每天冒出沒意義的 diff
    f = TTFont(FONTS / file, recalcTimestamp=False)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "lnum"]
    sub = subset.Subsetter(options=opts)
    sub.populate(text=text + " ")
    sub.subset(f)
    buf = io.BytesIO()
    subset.save_font(f, buf, opts)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")


# ── 方案 A：墨韻留白（延續 tznthou.com 的墨色＋青墨＋金墨）────────────
def plan_a(theme):
    light = theme == "light"
    ink = "#1A1A2A" if light else "#E5E5E5"
    P = dict(
        bg="#F0EDE6" if light else "#1A1A2A",
        ink=ink,
        muted="#6B6B80" if light else "#9090A8",
        cyan="#5E9A99" if light else "#7FB5B4",
        gold="#8F6F22" if light else "#E8C77B",
        grain="#1A1A2A" if light else "#FFFFFF",
    )
    H = 300
    x0, x1 = 60, W - 60
    base = 200
    span = (TODAY - FIRST).days

    def X(d):
        return x0 + (d - FIRST).days / span * (x1 - x0)

    doc = Doc(H, "4,583 days between my first green square and the next one",
              f"A single contribution on Dec 4, 2012, nothing for 4,583 days, then "
              f"{fmt(TOTAL - 1)} contributions since Jun 22, 2025.")
    doc.css.append(
        ".serif{font-family:'TzSerif',Georgia,'Times New Roman',serif}"
        ".mono{font-family:'TzMono',ui-monospace,Menlo,monospace}"
        f".dot{{mix-blend-mode:{'multiply' if light else 'screen'}}}"
    )
    doc.defs.append(
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" seed="12"/>'
        '<feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.07 0"/>'
        '<feComposite in2="SourceGraphic" operator="in"/></filter>'
        '<filter id="bleed" x="-50%" y="-50%" width="200%" height="200%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="2" seed="4" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="7"/>'
        '<feGaussianBlur stdDeviation="0.5"/></filter>'
        '<filter id="haze" x="-80%" y="-80%" width="260%" height="260%">'
        '<feGaussianBlur stdDeviation="7"/></filter>'
    )
    doc.add(f'<rect width="{W}" height="{H}" rx="12" fill="{P["bg"]}"/>')
    doc.add(f'<rect width="{W}" height="{H}" rx="12" fill="{P["grain"]}" filter="url(#grain)"/>')

    # 年份刻度：13 年的留白，每年一根細針
    for y in range(2013, TODAY.year + 1):
        x = X(dt.date(y, 1, 1))
        doc.add(f'<line x1="{x:.1f}" y1="{base - 4}" x2="{x:.1f}" y2="{base + 4}" '
                f'stroke="{P["muted"]}" stroke-opacity=".45" stroke-width="1"/>')
    # 時間線
    doc.add(f'<path d="M{x0} {base}H{x1}" stroke="{P["ink"]}" stroke-opacity=".3" '
            f'stroke-width="1.2" pathLength="1" stroke-dasharray="1" fill="none"'
            f'{anim("draw", 1.8, 0.1, "cubic-bezier(.4,0,.2,1)")}/>')
    # 第一滴墨
    doc.add(f'<circle cx="{x0}" cy="{base}" r="13" fill="{P["cyan"]}" opacity=".22" '
            f'filter="url(#haze)" class="b"{anim("bloom", .9, .2)}/>')
    doc.add(f'<circle cx="{x0}" cy="{base}" r="6.5" fill="{P["ink"]}" filter="url(#bleed)" '
            f'class="b"{anim("bloom", .7, .2)}/>')

    # 回歸後：每週一滴墨，大小∝√週貢獻，疊成暈開的墨團
    rng = random.Random(20121204)
    ranked = sorted(WEEKS, reverse=True)
    top = ranked[max(0, len([w for w in WEEKS if w]) // 5) - 1]
    for i, w in enumerate(WEEKS):
        if not w:
            continue
        d = SECOND + dt.timedelta(days=7 * i + 3)
        x = X(min(d, TODAY))
        y = base + rng.uniform(-16, 7)
        r = 2.6 + 20 * math.sqrt(w / MAX_WEEK)
        delay = 1.7 + i * 0.022
        if w >= top:
            doc.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 1.6:.1f}" fill="{P["cyan"]}" '
                    f'opacity=".2" filter="url(#haze)" class="b"{anim("bloom", 1.1, delay)}/>')
        doc.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{P["ink"]}" opacity=".5" '
                f'filter="url(#bleed)" class="b dot"{anim("bloom", .9, delay)}/>')
    # 本週：金墨
    xt = X(TODAY)
    doc.add(f'<circle cx="{xt:.1f}" cy="{base}" r="11" fill="{P["gold"]}" opacity=".35" '
            f'filter="url(#haze)" class="b"{anim("bloom", 1, 3.3)}/>')
    doc.add(f'<circle cx="{xt:.1f}" cy="{base}" r="4.2" fill="{P["gold"]}" class="b"'
            f'{anim("bloom", .6, 3.3)}/>')

    # 文字
    cx = 372
    doc.text(cx, 124, "4,583 days", "serif", 86, P["ink"], "middle", 900, anim("rise", 1.1, .5))
    doc.text(cx, 164, "between my first green square and the next one", "mono", 20,
             P["muted"], "middle", 400, anim("fade", 1, .9))
    doc.text(x0 - 6, base + 46, "Dec 4, 2012", "mono", 20, P["muted"], "start", 400,
             anim("fade", .8, 2.4))
    doc.text(x1 + 6, base + 46, "Jun 22, 2025 →", "mono", 20, P["muted"], "end", 400,
             anim("fade", .8, 2.6))
    doc.text(x1 + 6, 112, fmt(TOTAL), "mono", 30, P["gold"], "end", 500, anim("fade", .8, 3.1))
    doc.text(x1 + 6, 138, "and counting", "mono", 18, P["gold"], "end", 400,
             anim("fade", .8, 3.2))
    fonts = {("serif", 900): ("TzSerif", "noto-serif-900.woff2"),
             ("mono", 400): ("TzMono", "jetbrains-mono-400.woff2"),
             ("mono", 500): ("TzMono", "jetbrains-mono-500.woff2")}
    return doc.render(fonts), dict(ink_drops=sum(1 for w in WEEKS if w), weeks=N_WEEKS)


def main():
    print(f"資料：first={FIRST} second={SECOND} gap={GAP} total={TOTAL} "
          f"green_days={len(DAYS)} weeks={N_WEEKS} max_week={MAX_WEEK} today={TODAY}")
    for theme in ("light", "dark"):
        svg, info = plan_a(theme)
        ET.fromstring(svg)  # 必須是合法 XML
        path = OUT / f"timeline-{theme}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"{path.name:20} {len(svg) / 1024:6.1f} KB  {info}")


if __name__ == "__main__":
    main()
