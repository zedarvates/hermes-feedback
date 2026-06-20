#!/usr/bin/env python3
"""
Hermes Feedback — Dashboard HTML Generator
Auto-génère un dashboard visuel depuis les fichiers ndjson de feedback.
Peut être appelé en cron ou manuellement.

Usage:
  python3 dashboard_gen.py                         # Generate HTML
  python3 dashboard_gen.py --watch                  # Watch mode (continuous)
  python3 dashboard_gen.py --output ./dashboard.html
  python3 dashboard_gen.py --serve                  # Serve via HTTP
"""
import json, os, sys, glob, datetime, textwrap, html as html_mod
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter, defaultdict

FEEDBACK_DIR = Path.home() / ".hermes" / "feedback"
OUTPUT_FILE = Path.home() / ".hermes" / "feedback" / "dashboard.html"
STARS_FILE = FEEDBACK_DIR / "stars.ndjson"
POLLS_FILE = FEEDBACK_DIR / "polls.ndjson"
IMPLICIT_FILE = FEEDBACK_DIR / "implicit.ndjson"

# ── Data Loading ─────────────────────────────────────────────

def load_ndjson(path: Path) -> List[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries

def load_all_feedback() -> dict:
    return {
        "stars": load_ndjson(STARS_FILE),
        "polls": load_ndjson(POLLS_FILE),
        "implicit": load_ndjson(IMPLICIT_FILE),
    }

# ── Analytics ─────────────────────────────────────────────────

def compute_stats(data: dict) -> dict:
    stars = data["stars"]
    implicit = data["implicit"]
    polls = data["polls"]
    
    # Star ratings
    ratings = [s.get("rating", 0) for s in stars if "rating" in s]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    rating_dist = Counter(ratings)
    
    # Trends (last 7 days)
    now = datetime.datetime.now()
    week_ago = now - datetime.timedelta(days=7)
    recent_stars = [s for s in stars if 
                    datetime.datetime.fromisoformat(s.get("timestamp", "2000")).replace(tzinfo=None) > week_ago]
    
    # Implicit signals
    signal_types = Counter(i.get("signal", "unknown") for i in implicit)
    
    # Per-context ratings
    context_ratings = defaultdict(list)
    for s in stars:
        ctx = s.get("context", "general")[:30]
        context_ratings[ctx].append(s.get("rating", 0))
    context_avg = {ctx: sum(v)/len(v) for ctx, v in context_ratings.items()}
    top_contexts = sorted(context_avg.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Poll results
    poll_results = {}
    for p in polls:
        topic = p.get("topic", "unknown")
        response = p.get("response", "unknown")
        if topic not in poll_results:
            poll_results[topic] = Counter()
        poll_results[topic][response] += 1
    
    return {
        "total_ratings": len(stars),
        "avg_rating": round(avg_rating, 2),
        "rating_distribution": dict(rating_dist),
        "recent_ratings_7d": len(recent_stars),
        "recent_avg": round(sum(s.get("rating", 0) for s in recent_stars) / len(recent_stars), 2) if recent_stars else 0,
        "total_implicit": len(implicit),
        "signal_types": dict(signal_types),
        "total_polls": len(polls),
        "top_contexts": top_contexts,
        "poll_results": {k: dict(v) for k, v in poll_results.items()},
        "weekly_trend": compute_weekly_trend(stars),
    }

def compute_weekly_trend(stars: List[dict]) -> List[dict]:
    """Compute weekly average ratings for trend chart"""
    weekly = defaultdict(list)
    for s in stars:
        try:
            ts = datetime.datetime.fromisoformat(s.get("timestamp", "")).replace(tzinfo=None)
            week = ts.isocalendar()[:2]  # (year, week)
            weekly[week].append(s.get("rating", 0))
        except:
            continue
    
    sorted_weeks = sorted(weekly.keys())[-12:]  # Last 12 weeks
    return [
        {"week": f"W{w[1]}", "avg": round(sum(weekly[w])/len(weekly[w]), 2), "count": len(weekly[w])}
        for w in sorted_weeks
    ]

# ── HTML Generation ──────────────────────────────────────────

def generate_html(stats: dict) -> str:
    rating_dist = stats["rating_distribution"]
    dist_bars = "".join(
        f'<div class="bar-row"><span class="bar-label">{r}★</span>'
        f'<div class="bar-bg"><div class="bar-fill" style="width:{count/max(rating_dist.values())*100 if rating_dist.values() else 0}%"></div></span>'
        f'<span class="bar-count">{count}</span></div>\n'
        for r in [5,4,3,2,1] if (count := rating_dist.get(r, 0)) > 0
    )
    
    trend_chart = "".join(
        f'<div class="trend-bar" style="height:{w["avg"]*20}px" title="W{w}: {w["avg"]} ({w["count"]} ratings)"></div>'
        for w in stats["weekly_trend"]
    )
    
    contexts = "".join(
        f'<tr><td>{html_mod.escape(ctx)}</td><td>{"⭐" * int(avg)} ({avg:.1f})</td></tr>'
        for ctx, avg in stats["top_contexts"]
    )
    
    implicit_bars = "".join(
        f'<div class="bar-row"><span class="bar-label">{sig}</span>'
        f'<div class="bar-bg"><div class="bar-fill bar-implicit" style="width:{min(count/5*100, 100)}%"></div></div>'
        f'<span class="bar-count">{count}</span></div>'
        for sig, count in sorted(stats["signal_types"].items(), key=lambda x: -x[1])[:8]
    )
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hermes Feedback Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0f0f1a; color: #e0e0e0; font-family: 'Inter', system-ui, sans-serif; padding: 40px; }}
h1 {{ font-size: 28px; font-weight: 600; margin-bottom: 5px; color: #fff; }}
h2 {{ font-size: 18px; font-weight: 500; margin: 30px 0 15px; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
.subtitle {{ color: #666; font-size: 14px; margin-bottom: 30px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
.card {{ background: #1a1a2e; border-radius: 12px; padding: 20px; border: 1px solid #2a2a3e; }}
.card .value {{ font-size: 36px; font-weight: 700; color: #7c3aed; }}
.card .label {{ font-size: 12px; color: #666; margin-top: 5px; text-transform: uppercase; letter-spacing: 1px; }}
.bar-row {{ display: flex; align-items: center; gap: 10px; margin: 6px 0; }}
.bar-label {{ width: 40px; font-size: 13px; color: #888; }}
.bar-bg {{ flex: 1; height: 20px; background: #2a2a3e; border-radius: 4px; overflow: hidden; }}
.bar-fill {{ height: 100%; background: linear-gradient(90deg, #7c3aed, #a855f7); border-radius: 4px; transition: width 0.3s; }}
.bar-implicit {{ background: linear-gradient(90deg, #f59e0b, #f97316); }}
.bar-count {{ width: 30px; font-size: 13px; color: #aaa; text-align: right; }}
.trend-chart {{ display: flex; align-items: flex-end; gap: 6px; height: 120px; padding: 10px 0; }}
.trend-bar {{ flex: 1; background: linear-gradient(180deg, #7c3aed, #a855f7); border-radius: 4px 4px 0 0; min-width: 8px; transition: height 0.3s; }}
table {{ width: 100%; border-collapse: collapse; }}
td {{ padding: 8px 0; border-bottom: 1px solid #2a2a3e; font-size: 14px; }}
td:last-child {{ text-align: right; color: #f59e0b; }}
.footer {{ margin-top: 40px; font-size: 12px; color: #444; text-align: center; }}
</style></head><body>
<h1>⭐ Hermes Feedback Dashboard</h1>
<p class="subtitle">Generated: {now} &middot; {stats["total_ratings"]} ratings &middot; {stats["total_implicit"]} implicit signals</p>

<div class="grid">
<div class="card"><div class="value">{stats["avg_rating"]:.1f}</div><div class="label">Average Rating</div></div>
<div class="card"><div class="value" style="color:#f59e0b">{stats["recent_avg"]:.1f}</div><div class="label">7-Day Average</div></div>
<div class="card"><div class="value" style="color:#a855f7">{stats["total_implicit"]}</div><div class="label">Implicit Signals</div></div>
<div class="card"><div class="value" style="color:#22c55e">{stats["recent_ratings_7d"]}</div><div class="label">Ratings (7 days)</div></div>
</div>

<h2>Rating Distribution</h2>
<div class="card">{dist_bars}</div>

<h2>Weekly Trend</h2>
<div class="card"><div class="trend-chart">{trend_chart}</div></div>

<h2>Top Contexts</h2>
<div class="card"><table>{contexts}</table></div>

<h2>Implicit Signals</h2>
<div class="card">{implicit_bars}</div>

<h2>Poll Results</h2>
<div class="card">
{''.join(f'<h3 style="margin:10px 0 5px;font-size:14px;color:#a855f7">{html_mod.escape(topic)}</h3>' + 
         ''.join(f'<div class="bar-row"><span class="bar-label">{html_mod.escape(resp[:20])}</span>'
                 f'<div class="bar-bg"><div class="bar-fill" style="width:{min(count*20,100)}%"></div></div>'
                 f'<span class="bar-count">{count}</span></div>'
                 for resp, count in sorted(responses.items(), key=lambda x: -x[1]))
         for topic, responses in stats["poll_results"].items()) or '<p style="color:#666">No polls yet</p>'}
</div>

<div class="footer">Hermes Feedback &middot; Zero LLM tokens &middot; Open source</div>
</body></html>"""

# ── Main ─────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hermes Feedback Dashboard")
    parser.add_argument("--output", default=str(OUTPUT_FILE), help="Output HTML path")
    parser.add_argument("--serve", action="store_true", help="Serve via HTTP")
    parser.add_argument("--watch", action="store_true", help="Watch mode")
    parser.add_argument("--port", type=int, default=8890, help="HTTP port (default: 8890)")
    args = parser.parse_args()
    
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    data = load_all_feedback()
    stats = compute_stats(data)
    html = generate_html(stats)
    output.write_text(html)
    print(f"✅ Dashboard generated: {output} ({len(html)} bytes)")
    print(f"   {stats['total_ratings']} ratings, avg {stats['avg_rating']}/5")
    print(f"   {stats['total_implicit']} implicit signals")
    
    if args.watch:
        print("   Watching for changes (Ctrl+C to stop)...")
        import time
        last_mtime = max(
            p.stat().st_mtime for p in [STARS_FILE, POLLS_FILE, IMPLICIT_FILE] if p.exists()
        )
        while True:
            time.sleep(30)
            current = max(
                p.stat().st_mtime for p in [STARS_FILE, POLLS_FILE, IMPLICIT_FILE] if p.exists()
            )
            if current > last_mtime:
                data = load_all_feedback()
                stats = compute_stats(data)
                output.write_text(generate_html(stats))
                print(f"   Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")
                last_mtime = current
    
    if args.serve:
        print(f"   Serving at http://localhost:{args.port}")
        httpd = __import__('http.server').HTTPServer(
            ('', args.port),
            __import__('http.server').SimpleHTTPRequestHandler
        )
        os.chdir(output.parent)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("   Stopped")

if __name__ == "__main__":
    main()
