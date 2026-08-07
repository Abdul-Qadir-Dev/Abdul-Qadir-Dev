"""Render contrib-heatmap.svg from data/contributions.json.

A 53(ish)-week x 7-day grid of rounded boxes, GitHub's own dark-theme
green ramp, a diagonal line-after-line reveal that plays once on load
and freezes (no looping glow), a Less->More legend, and a stats footer.
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

CELL = 11
GAP = 3
STEP = CELL + GAP
MARGIN_LEFT = 28
MARGIN_TOP = 34
MARGIN_BOTTOM = 50
MARGIN_RIGHT = 14

BG = "transparent"
BORDER = "#30363d"
TEXT = "#8b949e"
TEXT_STRONG = "#c9d1d9"

# GitHub's dark-theme contribution ramp: none, then levels 1-4.
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def level_for(count: int) -> int:
    if count <= 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def build_grid(days):
    parsed = [
        (datetime.strptime(d["date"], "%Y-%m-%d").date(), d["count"])
        for d in days
    ]
    parsed.sort(key=lambda p: p[0])
    start = parsed[0][0]
    pad_start = start - timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday

    cells = {}
    max_col = 0
    for d, count in parsed:
        offset = (d - pad_start).days
        col, row = divmod(offset, 7)
        cells[(col, row)] = (d, count)
        max_col = max(max_col, col)

    return cells, max_col


def month_labels(cells, max_col):
    labels = []
    last_month = None
    for col in range(max_col + 1):
        day = cells.get((col, 0))
        if day is None:
            continue
        month = day[0].month
        if month != last_month:
            labels.append((col, MONTH_ABBR[month - 1]))
            last_month = month
    return labels


def build_svg(data: dict) -> str:
    cells, max_col = build_grid(data["days"])
    num_cols = max_col + 1

    grid_w = num_cols * STEP - GAP
    width = MARGIN_LEFT + grid_w + MARGIN_RIGHT
    height = MARGIN_TOP + 7 * STEP - GAP + MARGIN_BOTTOM

    boxes = []
    for (col, row), (day, count) in cells.items():
        x = MARGIN_LEFT + col * STEP
        y = MARGIN_TOP + row * STEP
        fill = PALETTE[level_for(count)]
        delay = (col + row) * 0.012
        boxes.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{fill}" style="animation-delay:{delay:.3f}s">'
            f'<title>{count} contribution{"s" if count != 1 else ""} on {day.isoformat()}</title>'
            f"</rect>"
        )

    months = [
        f'<text x="{MARGIN_LEFT + col * STEP}" y="{MARGIN_TOP - 12}" '
        f'font-size="11" fill="{TEXT}" font-family="sans-serif">{name}</text>'
        for col, name in month_labels(cells, max_col)
    ]

    weekdays = [
        f'<text x="0" y="{MARGIN_TOP + row * STEP + CELL - 2}" '
        f'font-size="10" fill="{TEXT}" font-family="sans-serif">{label}</text>'
        for row, label in WEEKDAY_LABELS.items()
    ]

    legend_y = MARGIN_TOP + 7 * STEP - GAP + 22
    legend_x = MARGIN_LEFT
    legend = [
        f'<text x="{legend_x}" y="{legend_y + 9}" font-size="11" fill="{TEXT}" '
        f'font-family="sans-serif">Less</text>'
    ]
    lx = legend_x + 32
    for i, color in enumerate(PALETTE):
        legend.append(
            f'<rect x="{lx + i * (CELL + 3)}" y="{legend_y}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{color}"/>'
        )
    legend.append(
        f'<text x="{lx + len(PALETTE) * (CELL + 3) + 6}" y="{legend_y + 9}" '
        f'font-size="11" fill="{TEXT}" font-family="sans-serif">More</text>'
    )

    footer_y = legend_y
    stats = (
        f'{data["total_contributions"]} contributions in the last year &#183; '
        f'current streak {data["current_streak"]}d &#183; '
        f'longest streak {data["longest_streak"]}d'
    )
    footer = (
        f'<text x="{width - MARGIN_RIGHT}" y="{footer_y + 9}" text-anchor="end" '
        f'font-size="11" fill="{TEXT_STRONG}" font-family="sans-serif">{stats}</text>'
    )

    style = """
  <style>
    .cell { opacity: 0; transform-box: fill-box; transform-origin: center;
            animation: reveal 0.35s ease-out forwards; }
    @keyframes reveal {
      from { opacity: 0; transform: translateY(-5px); }
      to   { opacity: 1; transform: translateY(0); }
    }
  </style>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">{style}
  {''.join(months)}
  {''.join(weekdays)}
  {''.join(boxes)}
  {''.join(legend)}
  {footer}
</svg>
"""


def main():
    root = Path(__file__).resolve().parent.parent
    data = json.loads((root / "data" / "contributions.json").read_text(encoding="utf-8"))
    svg = build_svg(data)
    out = root / "contrib-heatmap.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
