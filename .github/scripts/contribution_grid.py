"""Render the public GitHub contribution calendar as a static teal SVG."""
import datetime as dt
import re
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "keminbtepe"
OUT = sys.argv[2] if len(sys.argv) > 2 else "dist/contribution-grid.svg"

COLORS = ["#1E293B", "#134E4A", "#0F766E", "#14B8A6", "#5EEAD4"]
BG, TEXT, MUTED = "#0F172A", "#E2E8F0", "#94A3B8"
MONTHS = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
CELL, GAP = 11, 3
PITCH = CELL + GAP
LEFT, TOP = 44, 42

req = urllib.request.Request(
    f"https://github.com/users/{USER}/contributions",
    headers={"User-Agent": "contribution-grid-action"},
)
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

days = {}
for tag in re.findall(r"<td[^>]*data-date=[^>]*>", html):
    date = re.search(r'data-date="([\d-]+)"', tag)
    level = re.search(r'data-level="(\d)"', tag)
    if date and level:
        days[dt.date.fromisoformat(date.group(1))] = int(level.group(1))
if not days:
    sys.exit("No contribution data found")

total_match = re.search(r"([\d,.]+)\s+contributions?\s+in the last year", html)
total = total_match.group(1).replace(",", "") if total_match else str(sum(1 for v in days.values() if v))

first = min(days)
start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday
weeks = (max(days) - start).days // 7 + 1
width = LEFT + weeks * PITCH + 16
height = TOP + 7 * PITCH + 44

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
    f'font-family="Segoe UI, Helvetica, Arial, sans-serif">',
    f'<rect width="{width}" height="{height}" rx="10" fill="{BG}"/>',
]

last_month_col = -10
for col in range(weeks):
    week_start = start + dt.timedelta(weeks=col)
    for offset in range(7):
        day = week_start + dt.timedelta(days=offset)
        if day.day == 1 and col - last_month_col >= 3:
            parts.append(f'<text x="{LEFT + col * PITCH}" y="{TOP - 10}" fill="{MUTED}" font-size="11">{MONTHS[day.month - 1]}</text>')
            last_month_col = col
            break

for row, label in ((1, "Pzt"), (3, "Çar"), (5, "Cum")):
    parts.append(f'<text x="{LEFT - 10}" y="{TOP + row * PITCH + CELL - 2}" fill="{MUTED}" font-size="10" text-anchor="end">{label}</text>')

for day, level in sorted(days.items()):
    col = (day - start).days // 7
    row = (day.weekday() + 1) % 7
    parts.append(
        f'<rect x="{LEFT + col * PITCH}" y="{TOP + row * PITCH}" width="{CELL}" height="{CELL}" rx="2" fill="{COLORS[level]}"/>'
    )

footer_y = TOP + 7 * PITCH + 22
parts.append(f'<text x="{LEFT}" y="{footer_y}" fill="{TEXT}" font-size="12">Son bir yılda {total} katkı</text>')
legend_x = width - 16 - 5 * PITCH - 28
parts.append(f'<text x="{legend_x - 6}" y="{footer_y}" fill="{MUTED}" font-size="11" text-anchor="end">Az</text>')
for i, color in enumerate(COLORS):
    parts.append(f'<rect x="{legend_x + i * PITCH}" y="{footer_y - 10}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
parts.append(f'<text x="{legend_x + 5 * PITCH + 4}" y="{footer_y}" fill="{MUTED}" font-size="11">Çok</text>')
parts.append("</svg>")

import os

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(parts))
print(f"{OUT}: {len(days)} days, {sum(1 for v in days.values() if v)} active, total {total}")
