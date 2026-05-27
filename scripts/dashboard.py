#!/usr/bin/env python3
"""dashboard.py — ASCII art dashboard for feedback trends.

Reads ratings.ndjson and implicit_signals.ndjson, prints a
terminal-friendly overview with ASCII bar charts.

Usage:
  dashboard.py              full dashboard
  dashboard.py --summary    compact one-liner
  dashboard.py --html       generate HTML file with proper charts
"""

import json, os, sys
from collections import Counter
from datetime import datetime, timezone

FEED_DIR = os.path.expanduser("~/.hermes/feedback")

def load_ndjson(filename):
    path = os.path.join(FEED_DIR, filename)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries

def ascii_bar(count, max_count, width=20):
    """Generate an ASCII bar with proportional width."""
    if max_count == 0:
        return " " * width
    filled = max(1, int(count / max_count * width))
    return "█" * filled

def star_line(label, value, max_value, width=30):
    bar = ascii_bar(value, max_value, width)
    return f"  {label}: {bar} ({value})"

def dashboard():
    ratings = load_ndjson("ratings.ndjson")
    implicit = load_ndjson("implicit_signals.ndjson")
    all_feedback = ratings + implicit
    # Deduplicate by timestamp
    seen = set()
    unique = []
    for e in all_feedback:
        ts = e.get("timestamp", "")
        if ts not in seen:
            seen.add(ts)
            unique.append(e)

    total = len(unique)
    explicit = len(ratings)
    implicit_count = len(implicit)

    print("╔══════════════════════════════════════╗")
    print("║      HERMES FEEDBACK DASHBOARD       ║")
    print("╚══════════════════════════════════════╝")
    print()

    if total == 0:
        print("  No feedback recorded yet.")
        print()
        print("  Rate responses with:  /r ★★★★")
        print()
        return

    # Summary stats
    print(f"  Total feedback:  {total}")
    print(f"  Explicit (/r):   {explicit}")
    print(f"  Implicit:        {implicit_count}")
    print()

    # Rating distribution
    all_ratings = [e["rating"] for e in unique if "rating" in e]
    if all_ratings:
        avg = sum(all_ratings) / len(all_ratings)
        counter = Counter(all_ratings)
        max_c = max(counter.values()) if counter else 1

        # Average display
        stars_filled = "★" * round(avg)
        stars_empty = "☆" * (5 - round(avg))
        print(f"  Average:  {avg:.2f}/5  ({stars_filled}{stars_empty})")
        print()

        # Bar chart
        print(f"  Rating Distribution:")
        for r in range(1, 6):
            c = counter.get(r, 0)
            bar = ascii_bar(c, max_c)
            print(f"    {r}★  {bar}  {c}")
        print()

    # Signal breakdown (implicit)
    if implicit:
        signals = Counter(e.get("signal", "unknown") for e in implicit)
        if signals:
            print(f"  Implicit Signals:")
            for sig, count in signals.most_common():
                bar = ascii_bar(count, max(signals.values()))
                print(f"    {sig:15s}  {bar}  {count}")
            print()

    # Recent activity
    sorted_unique = sorted(unique, key=lambda e: e.get("timestamp", ""), reverse=True)
    print(f"  Recent Feedback (last 5):")
    for e in sorted_unique[:5]:
        ts = e.get("timestamp", "?")[11:19]  # HH:MM:SS
        r = e.get("rating", "?")
        sig = e.get("signal", "/r")
        ctx = e.get("context", "-")[:40]
        print(f"    {ts}  {r}★  [{sig:8s}]  {ctx}")
    print()

    # Trend arrow
    if len(all_ratings) >= 5:
        recent_5 = all_ratings[-5:]
        older = all_ratings[:-5]
        recent_avg = sum(recent_5) / 5
        older_avg = sum(older) / len(older) if older else recent_avg
        diff = recent_avg - older_avg
        if diff > 0.3:
            arrow = "▲ UP"
        elif diff < -0.3:
            arrow = "▼ DOWN"
        else:
            arrow = "→ STABLE"
        print(f"  Trend (last 5 vs before):  {arrow}  ({recent_avg:.1f} vs {older_avg:.1f})")
    print()

def html():
    """Generate a proper HTML version of the dashboard."""
    ratings = load_ndjson("ratings.ndjson")
    implicit = load_ndjson("implicit_signals.ndjson")
    all_feedback = ratings + implicit

    if not all_feedback:
        html_content = "<html><body><h1>No feedback yet</h1></body></html>"
    else:
        all_ratings = [e["rating"] for e in all_feedback if "rating" in e]
        avg = sum(all_ratings) / len(all_ratings)
        counter = Counter(all_ratings)
        total = len(all_feedback)

        bars_html = ""
        for r in range(1, 6):
            c = counter.get(r, 0)
            pct = c / total * 100
            bars_html += f"""
            <div style="margin: 8px 0;">
              <span style="width:30px;display:inline-block">{r}★</span>
              <div style="display:inline-block;width:300px;height:20px;background:#eee;border-radius:4px;">
                <div style="width:{pct}%;height:100%;background:#4CAF50;border-radius:4px;"></div>
              </div>
              <span style="margin-left:8px;">{c} ({pct:.0f}%)</span>
            </div>"""

        html_content = f"""<html>
<head><title>Hermes Feedback Dashboard</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; }}
  h1 {{ color: #333; }}
  .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
  .stat {{ background: #f5f5f5; padding: 12px 20px; border-radius: 8px; text-align: center; }}
  .stat-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
  .stat-label {{ font-size: 12px; color: #666; }}
  .recent {{ margin-top: 20px; }}
  .entry {{ padding: 6px 0; border-bottom: 1px solid #eee; font-size: 14px; }}
</style>
</head>
<body>
<h1>📊 Hermes Feedback</h1>
<div class="stats">
  <div class="stat"><div class="stat-value">{total}</div><div class="stat-label">Total ratings</div></div>
  <div class="stat"><div class="stat-value">{avg:.1f}</div><div class="stat-label">Average ★</div></div>
  <div class="stat"><div class="stat-value">{len(implicit)}</div><div class="stat-label">Implicit</div></div>
</div>
<h3>Distribution</h3>
{bars_html}
<div class="recent">
<h3>Recent</h3>"""

        for e in sorted(all_feedback, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]:
            ts = e.get("timestamp", "?")
            r = e.get("rating", "?")
            sig = e.get("signal", "/r")
            ctx = e.get("context", "-")[:60]
            html_content += f'<div class="entry">{ts} | {r}★ | {sig} | {ctx}</div>'

        html_content += "</div></body></html>"

    out_path = os.path.join(FEED_DIR, "dashboard.html")
    with open(out_path, "w") as f:
        f.write(html_content)
    print(f"✓ Dashboard HTML: {out_path}")

if __name__ == "__main__":
    if "--html" in sys.argv:
        html()
    elif "--summary" in sys.argv:
        ratings = load_ndjson("ratings.ndjson")
        if ratings:
            avg = sum(e["rating"] for e in ratings) / len(ratings)
            stars = "★★★★★" if avg >= 4.5 else "★★★★☆" if avg >= 3.5 else "★★★☆☆" if avg >= 2.5 else "★★☆☆☆" if avg >= 1.5 else "★☆☆☆☆"
            print(f"{stars}  {avg:.1f}/5  ({len(ratings)} ratings)")
        else:
            print("No ratings yet.")
    else:
        dashboard()
