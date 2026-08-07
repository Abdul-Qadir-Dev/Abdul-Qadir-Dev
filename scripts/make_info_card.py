"""Render info-card.svg: a neofetch-style panel that fades in line by line.

Content is fixed and lives in ROWS below -- this script only lays it out.
Set STATIC=1 to emit a frozen (non-animated) frame for local preview.
"""

import os
import textwrap
from pathlib import Path

WIDTH = 490
PAD_X = 24
LABEL_COL = 92
VALUE_CHARS = 44          # wrap budget for the value column
LINE_H = 17                # continuation-line spacing within a row
ROW_GAP = 27                # baseline-to-baseline gap between rows
HEADER_H = 46
BOTTOM_PAD = 22

BG = "#0d1117"
BORDER = "#30363d"
ACCENT = "#58a6ff"          # the one accent color
VALUE_COLOR = "#c9d1d9"
MUTED = "#6e7681"

ROWS = [
    ("role", "Product Support Engineer, payments infrastructure"),
    ("domain", "Card issuing, ISO 8583, Metro 2, disputes, PCI reporting"),
    ("stack", "Python, SQL, REST APIs, ETL, Linux, Cloudflare Workers"),
    ("now", "Payments infrastructure, moving into applied AI"),
    ("writing", "medium.com/@TechByQadir"),
]

FONT = "ui-monospace,'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_rows(static: bool):
    y = HEADER_H + 20
    parts = []
    delay = 0.15
    for label, value in ROWS:
        lines = textwrap.wrap(value, width=VALUE_CHARS) or [""]
        label_x = PAD_X
        value_x = PAD_X + LABEL_COL

        style = "" if static else f' style="animation-delay:{delay:.2f}s"'
        cls = "" if static else ' class="row"'
        parts.append(f'<g{cls}{style}>')
        parts.append(
            f'<text x="{label_x}" y="{y}" font-family="{FONT}" font-size="13" '
            f'fill="{ACCENT}">{esc(label)}</text>'
        )
        for i, line in enumerate(lines):
            ly = y + i * LINE_H
            parts.append(
                f'<text x="{value_x}" y="{ly}" font-family="{FONT}" font-size="13" '
                f'fill="{VALUE_COLOR}">{esc(line)}</text>'
            )
        parts.append("</g>")

        y += (len(lines) - 1) * LINE_H + ROW_GAP
        delay += 0.16

    height = y - ROW_GAP + BOTTOM_PAD
    return "\n".join(parts), height


def build_svg(static: bool) -> str:
    rows_svg, height = build_rows(static)

    style_block = ""
    if not static:
        style_block = """
  <style>
    .row { opacity: 0; animation: fadeIn 0.5s ease-out forwards; }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to   { opacity: 1; transform: translateY(0); }
    }
  </style>"""

    dots = "".join(
        f'<circle cx="{24 + i * 16}" cy="23" r="4.5" fill="{MUTED}" opacity="0.55"/>'
        for i in range(3)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}">{style_block}
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <line x1="0" y1="{HEADER_H}" x2="{WIDTH}" y2="{HEADER_H}" stroke="{BORDER}"/>
  {dots}
  {rows_svg}
</svg>
"""


def main():
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(static)
    out = Path(__file__).resolve().parent.parent / "info-card.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({'static' if static else 'animated'})")


if __name__ == "__main__":
    main()
