"""Scrape the public contribution calendar (no auth, no API token) and
write data/contributions.json with raw days plus derived stats.

Source: https://github.com/users/<username>/contributions -- the same
HTML fragment GitHub's own profile page fetches to render the calendar.
"""

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "Abdul-Qadir-Dev"
URL = f"https://github.com/users/{USERNAME}/contributions"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; profile-readme-bot)"}


def fetch_html() -> str:
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str):
    soup = BeautifulSoup(html, "html.parser")
    cells = soup.find_all(attrs={"data-date": True})

    tooltips = {}
    for tip in soup.find_all("tool-tip"):
        key = tip.get("for") or tip.get("id")
        if key:
            tooltips[key] = tip.get_text(strip=True)

    days = []
    for cell in cells:
        date_str = cell["data-date"]

        if cell.get("data-count") is not None:
            count = int(cell["data-count"])
        else:
            level = int(cell.get("data-level", 0) or 0)
            tip_text = None
            for key in (cell.get("aria-describedby"), cell.get("id")):
                if key and key in tooltips:
                    tip_text = tooltips[key]
                    break
            if tip_text:
                m = re.search(r"(\d+)\s+contribution", tip_text)
                count = int(m.group(1)) if m else 0
            else:
                count = level  # last-resort proxy if no tooltip is found

        days.append({"date": date_str, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def compute_streaks(days):
    current = 0
    today_skipped = False
    for i in range(len(days) - 1, -1, -1):
        if days[i]["count"] > 0:
            current += 1
        elif i == len(days) - 1 and not today_skipped:
            today_skipped = True  # today may legitimately still be at 0
            continue
        else:
            break

    longest = run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    return current, longest


def compute_monthly_totals(days):
    totals = defaultdict(int)
    for d in days:
        month = d["date"][:7]  # YYYY-MM
        totals[month] += d["count"]
    return dict(sorted(totals.items()))


def main():
    html = fetch_html()
    days = parse_days(html)

    if not days:
        raise SystemExit("no contribution cells parsed -- GitHub markup may have changed")

    current_streak, longest_streak = compute_streaks(days)
    best_day = max(days, key=lambda d: d["count"])

    data = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_contributions": sum(d["count"] for d in days),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": compute_monthly_totals(days),
        "days": days,
    }

    out = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(days)} days, {data['total_contributions']} contributions)")


if __name__ == "__main__":
    main()
