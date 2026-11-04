"""Render the public GitHub contribution calendar as a static SVG that mirrors
the stock profile graph (same layout, labels, legend and per-day tooltips)."""
import datetime as dt
import html as htmllib
import os
import re
import sys
import urllib.request

USER = sys.argv[1] if len(sys.argv) > 1 else "keminbtepe"
OUT = sys.argv[2] if len(sys.argv) > 2 else "dist/contribution-grid.svg"

COLORS = ["#1E293B", "#134E4A", "#0F766E", "#14B8A6", "#5EEAD4"]
BG, TEXT, MUTED = "#0F172A", "#E2E8F0", "#94A3B8"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CELL, PITCH = 10, 13
LEFT, TOP = 40, 56

req = urllib.request.Request(
    f"https://github.com/users/{USER}/contributions",
    headers={"User-Agent": "contribution-grid-action"},
)
page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

tips = {}
for target, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
    tips[target] = " ".join(htmllib.unescape(text).split())

days = {}
for tag in re.findall(r"<td[^>]*data-date=[^>]*>", page):
    date = re.search(r'data-date="([\d-]+)"', tag)
    level = re.search(r'data-level="(\d)"', tag)
    ident = re.search(r'id="([^"]+)"', tag)
    if date and level:
        tip = tips.get(ident.group(1), "") if ident else ""
        days[dt.date.fromisoformat(date.group(1))] = (int(level.group(1)), tip)
if not days:
    sys.exit("No contribution data found")

total_match = re.search(r"([\d,.]+)\s+contributions?\s+in\s+the\s+last\s+year", page)
total = total_match.group(1) if total_match else "0"

first = min(days)
start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday
weeks = (max(days) - start).days // 7 + 1
width = LEFT + weeks * PITCH + 12
height = TOP + 7 * PITCH + 38

out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
    f'font-family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif">',
    f'<rect width="{width}" height="{height}" rx="10" fill="{BG}"/>',
    f'<text x="{LEFT - 28}" y="26" fill="{TEXT}" font-size="15">{total} contributions in the last year</text>',
]

prev_col, prev_month = -10, None
for col in range(weeks):
    month = (start + dt.timedelta(weeks=col)).month
    if month != prev_month:
        if col - prev_col >= 3 or prev_month is None:
            out.append(f'<text x="{LEFT + col * PITCH}" y="{TOP - 8}" fill="{MUTED}" font-size="11">{MONTHS[month - 1]}</text>')
            prev_col = col
        prev_month = month

for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    out.append(f'<text x="{LEFT - 10}" y="{TOP + row * PITCH + 9}" fill="{MUTED}" font-size="10" text-anchor="end">{label}</text>')

for day, (level, tip) in sorted(days.items()):
    col = (day - start).days // 7
    row = (day.weekday() + 1) % 7
    title = f"<title>{htmllib.escape(tip)}</title>" if tip else ""
    out.append(
        f'<rect x="{LEFT + col * PITCH}" y="{TOP + row * PITCH}" width="{CELL}" height="{CELL}" rx="2" '
        f'fill="{COLORS[level]}" stroke="rgba(255,255,255,0.05)" stroke-width="1">{title}</rect>'
    )

foot = TOP + 7 * PITCH + 24
leg = width - 12 - 5 * PITCH - 62
out.append(f'<text x="{leg}" y="{foot}" fill="{MUTED}" font-size="11" text-anchor="end">Less</text>')
for i, color in enumerate(COLORS):
    out.append(f'<rect x="{leg + 6 + i * PITCH}" y="{foot - 9}" width="{CELL}" height="{CELL}" rx="2" fill="{color}" stroke="rgba(255,255,255,0.05)"/>')
out.append(f'<text x="{leg + 12 + 5 * PITCH}" y="{foot}" fill="{MUTED}" font-size="11">More</text>')
out.append("</svg>")

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
print(f"{OUT}: {len(days)} days, {sum(1 for v in days.values() if v[0])} active, total {total}, tips {sum(1 for v in days.values() if v[1])}")
