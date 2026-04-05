import json

with open('report_data.json') as f:
    data = json.load(f)

posts = data['total_posts']
avg = data['avg_score']
top = data['top_score']
updated = data['generated_at']
alerts = data['alerts']
content = data['content_scores']
subreddits = data['subreddit_scores']
top10 = data['top10_posts']
keywords = data['top_keywords']
lengths = data['length_scores']
h_avg = data.get('higgsfield_avg', 0)
h_top = data.get('higgsfield_top', 0)
h_posts = data.get('higgsfield_total_posts', 0)
h_gap = data.get('higgsfield_gap', 0)
h_sub = data.get('higgsfield_sub_avg', 0)
h_top10 = data.get('higgsfield_top10', [])
h_kw = data.get('higgsfield_keywords', [])
h_cs = data.get('higgsfield_content_scores', {})

viral = next((a for a in alerts if a['type'] == 'viral'), None)
other_alerts = [a for a in alerts if a['type'] != 'viral']

def make_bars(scores_dict):
    valid = {k: v for k, v in scores_dict.items() if str(v) != 'nan'}
    if not valid:
        return ''
    max_v = max(valid.values())
    html = ''
    for name, score in sorted(valid.items(), key=lambda x: -x[1]):
        pct = round(score / max_v * 100)
        html += f'<div class="bar-item"><div class="bar-label"><span>{name}</span><span>{score}</span></div><div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div></div>'
    return html

content_bars = make_bars(content)

max_s = max(subreddits.values()) if subreddits else 1
sub_bars = ''
for name, score in sorted(subreddits.items(), key=lambda x: -x[1]):
    pct = round(score / max_s * 100)
    sub_bars += f'<div class="bar-item"><div class="bar-label"><span>r/{name}</span><span>{score}</span></div><div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div></div>'

posts_html = ''
for p in top10:
    url = p.get('url', '#').replace("'", "")
    title = p['title'][:75].replace("'", "").replace('"', '')
    score = p['score']
    posts_html += f'<div class="post-item" onclick="window.open(this.dataset.url,\'_blank\')" data-url="{url}"><div class="post-title">{title}...</div><div class="post-score">{score}</div></div>'

kw_html = ''
for i, kw in enumerate(keywords):
    big = 'big' if i < 5 else ''
    kw_html += f'<span class="keyword-tag {big}">{kw["word"]} ({kw["count"]})</span>'

length_order = ['very_short', 'short', 'medium', 'long', 'very_long']
length_labels = {
    'very_short': 'Very short (under 30)',
    'short': 'Short (30-60 chars)',
    'medium': 'Medium (60-90 chars)',
    'long': 'Long (90-120 chars)',
    'very_long': 'Very long (120+)'
}
max_l = max((lengths.get(k, 0) for k in length_order), default=1)
length_bars = ''
for key in length_order:
    score = lengths.get(key, 0)
    pct = round(score / max_l * 100) if max_l > 0 else 0
    length_bars += f'<div class="bar-item"><div class="bar-label"><span>{length_labels[key]}</span><span>{score}</span></div><div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div></div>'

h_posts_html = ''
for p in h_top10:
    url = p.get('url', '#').replace("'", "")
    title = p['title'][:75].replace("'", "").replace('"', '')
    score = p['score']
    h_posts_html += f'<div class="post-item" onclick="window.open(this.dataset.url,\'_blank\')" data-url="{url}"><div class="post-title">{title}...</div><div class="post-score">{score}</div></div>'
if not h_posts_html:
    h_posts_html = '<div style="color:#555;font-size:0.8rem">No Higgsfield posts found</div>'

h_kw_html = ''
for i, kw in enumerate(h_kw):
    big = 'big' if i < 5 else ''
    h_kw_html += f'<span class="keyword-tag {big}">{kw["word"]} ({kw["count"]})</span>'

alerts_html = ''
for a in other_alerts:
    msg = a['message']
    color = a['color']
    alerts_html += f'<div class="alert-pill alert-{color}">{msg}</div>'

urgent_html = ''
if viral:
    v_title = viral['post_title'].replace("'", "").replace('"', '')
    v_score = viral['post_score']
    v_sub = viral['post_subreddit']
    v_action = viral['action']
    v_url = viral['post_url']
    urgent_html = f'''<div class="urgent-banner active">
        <div class="urgent-top">
            <div class="urgent-dot"></div>
            <div class="urgent-title">Something is happening right now — immediate action required</div>
        </div>
        <div class="urgent-post-title">{v_title}</div>
        <div class="urgent-meta">
            <span class="urgent-score">Score: {v_score:,}</span>
            <span class="urgent-sub">r/{v_sub}</span>
        </div>
        <div class="urgent-action">{v_action}</div>
        <a class="urgent-btn" href="{v_url}" target="_blank">View Post on Reddit</a>
    </div>'''

h_format = 'Loading...'
h_format_gap = '--'
if h_cs:
    valid = [(k, v) for k, v in h_cs.items() if str(v) != 'nan']
    if valid:
        best = sorted(valid, key=lambda x: -x[1])[0]
        h_format = f'{best[0]} posts ({best[1]})'
        if content.get('Code') and best[1]:
            h_format_gap = f'Claude code scores {round(content["Code"] / best[1], 1)}x more'

h_posts_gap = f'{round(posts / h_posts, 1)}x more discourse' if h_posts > 0 else '--'
h_top_gap = f'{round(top / h_top, 1)}x higher' if h_top > 0 else '--'
h_sub_gap = f'{round(131 / h_sub, 1)}x less' if h_sub > 0 else '--'

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Viral Growth Machine — HackNU 2026</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Segoe UI", sans-serif; background: #0f0f0f; color: #fff; line-height: 1.6; }}
        .header {{ background: #1a1a1a; border-bottom: 2px solid #333; padding: 1.5rem 3rem; display: flex; justify-content: space-between; align-items: center; }}
        .header h1 {{ font-size: 1.6rem; font-weight: 700; }}
        .header p {{ color: #888; font-size: 0.85rem; margin-top: 0.2rem; }}
        .badge {{ background: #ff4500; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-block; }}
        .live-indicator {{ display: inline-flex; align-items: center; gap: 0.4rem; margin-left: 0.75rem; font-size: 0.75rem; color: #22c55e; font-weight: 600; }}
        .live-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #22c55e; animation: pulse 1s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
        .last-updated {{ color: #555; font-size: 0.72rem; margin-top: 0.25rem; }}
        .refresh-btn {{ background: #ff4500; color: white; border: none; padding: 0.5rem 1.2rem; border-radius: 8px; font-size: 0.82rem; cursor: pointer; font-weight: 600; margin-top: 0.5rem; }}
        .refresh-btn:hover {{ background: #e03d00; }}
        .refresh-btn:disabled {{ background: #555; cursor: not-allowed; }}
        .urgent-banner {{ display: none; background: #1a0000; border: 2px solid #ef4444; border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; animation: urgentPulse 2s infinite; }}
        .urgent-banner.active {{ display: block; }}
        @keyframes urgentPulse {{ 0%, 100% {{ border-color: #ef4444; }} 50% {{ border-color: #ff8888; }} }}
        .urgent-top {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }}
        .urgent-dot {{ width: 12px; height: 12px; border-radius: 50%; background: #ef4444; animation: pulse 0.5s infinite; flex-shrink: 0; }}
        .urgent-title {{ font-size: 0.85rem; font-weight: 700; color: #ef4444; text-transform: uppercase; letter-spacing: 0.08em; }}
        .urgent-post-title {{ font-size: 1rem; font-weight: 600; color: #fff; margin-bottom: 0.5rem; line-height: 1.4; }}
        .urgent-meta {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.75rem; }}
        .urgent-score {{ font-size: 0.8rem; color: #ef4444; font-weight: 700; }}
        .urgent-sub {{ font-size: 0.8rem; color: #888; }}
        .urgent-action {{ font-size: 0.82rem; color: #f59e0b; font-weight: 600; margin-bottom: 0.75rem; }}
        .urgent-btn {{ background: #ef4444; color: white; border: none; padding: 0.5rem 1.25rem; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-block; }}
        .alerts-bar {{ margin-bottom: 1.5rem; }}
        .alert-pill {{ display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.78rem; margin-right: 0.5rem; margin-bottom: 0.5rem; cursor: pointer; }}
        .alert-green {{ background: rgba(34,197,94,0.15); border: 1px solid #22c55e; color: #22c55e; }}
        .alert-yellow {{ background: rgba(245,158,11,0.15); border: 1px solid #f59e0b; color: #f59e0b; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem 3rem; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }}
        .metric-card {{ background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 1.5rem; text-align: center; }}
        .metric-card:hover {{ border-color: #ff4500; }}
        .metric-value {{ font-size: 2.2rem; font-weight: 700; color: #ff4500; display: block; }}
        .metric-label {{ font-size: 0.72rem; color: #888; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.25rem; }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }}
        .section {{ background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; }}
        .section h2 {{ font-size: 1rem; font-weight: 600; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid #333; display: flex; align-items: center; gap: 0.5rem; }}
        .dot {{ width: 8px; height: 8px; border-radius: 50%; background: #ff4500; display: inline-block; flex-shrink: 0; }}
        .bar-item {{ margin-bottom: 0.75rem; }}
        .bar-label {{ display: flex; justify-content: space-between; margin-bottom: 0.3rem; font-size: 0.82rem; }}
        .bar-label span:first-child {{ color: #ccc; }}
        .bar-label span:last-child {{ color: #ff4500; font-weight: 600; }}
        .bar-track {{ background: #333; border-radius: 4px; height: 7px; overflow: hidden; }}
        .bar-fill {{ height: 100%; border-radius: 4px; background: #ff4500; }}
        .post-item {{ padding: 0.6rem 0; border-bottom: 1px solid #222; display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; cursor: pointer; }}
        .post-item:hover {{ background: #1f1f1f; padding-left: 0.5rem; border-radius: 4px; }}
        .post-item:last-child {{ border-bottom: none; }}
        .post-title {{ font-size: 0.78rem; color: #ccc; flex: 1; line-height: 1.4; }}
        .post-score {{ font-size: 0.85rem; font-weight: 700; color: #ff4500; white-space: nowrap; }}
        .keyword-cloud {{ display: flex; flex-wrap: wrap; gap: 0.5rem; }}
        .keyword-tag {{ background: #222; border: 1px solid #444; border-radius: 20px; padding: 0.3rem 0.75rem; font-size: 0.75rem; color: #ccc; }}
        .keyword-tag.big {{ border-color: #ff4500; color: #ff4500; font-weight: 600; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
        th {{ background: #222; color: #888; text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.72rem; padding: 0.6rem 0.75rem; text-align: left; }}
        td {{ padding: 0.6rem 0.75rem; border-bottom: 1px solid #222; color: #ccc; }}
        tr:last-child td {{ border-bottom: none; }}
        .win {{ color: #22c55e; font-weight: 600; }}
        .lose {{ color: #ef4444; font-weight: 600; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .footer {{ text-align: center; padding: 2rem; color: #444; font-size: 0.75rem; border-top: 1px solid #222; margin-top: 2rem; }}
        @media (max-width: 768px) {{ .metrics-grid {{ grid-template-columns: repeat(2,1fr); }} .two-col {{ grid-template-columns: 1fr; }} .container {{ padding: 1rem; }} .header {{ padding: 1rem; flex-direction: column; gap: 1rem; }} }}
    </style>
</head>
<body>

<div id="refresh-overlay" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:1000;flex-direction:column;align-items:center;justify-content:center;gap:1rem;">
    <div style="width:50px;height:50px;border:3px solid #333;border-top-color:#ff4500;border-radius:50%;animation:spin 0.8s linear infinite;"></div>
    <div style="color:#fff;font-size:1rem;font-weight:600;">Scraping Reddit...</div>
    <div style="color:#888;font-size:0.8rem;">Please wait — collecting fresh data and rebuilding dashboard</div>
</div>

<div class="header">
    <div>
        <h1>Claude Viral Growth Machine</h1>
        <p>HackNU 2026 — Competitive Intelligence Dashboard</p>
    </div>
    <div style="text-align:right">
        <div>
            <span class="badge">{posts} Real Reddit Posts</span>
            <span class="live-indicator"><span class="live-dot"></span> LIVE</span>
        </div>
        <div class="last-updated">Last updated: {updated}</div>
        <button class="refresh-btn" id="refresh-btn" onclick="triggerRefresh()">Refresh Data</button>
    </div>
</div>

<div class="container">

    {urgent_html}

    <div class="alerts-bar">{alerts_html}</div>

    <div class="metrics-grid">
        <div class="metric-card">
            <span class="metric-value">{posts}</span>
            <div class="metric-label">Posts Scraped</div>
        </div>
        <div class="metric-card">
            <span class="metric-value">{avg}</span>
            <div class="metric-label">Avg Score</div>
        </div>
        <div class="metric-card">
            <span class="metric-value">{top:,}</span>
            <div class="metric-label">Top Post Score</div>
        </div>
        <div class="metric-card">
            <span class="metric-value">691x</span>
            <div class="metric-label">Tip vs Question</div>
        </div>
    </div>

    <div class="two-col">
        <div class="section">
            <h2><span class="dot"></span>Content Type Performance</h2>
            {content_bars}
        </div>
        <div class="section">
            <h2><span class="dot"></span>Subreddit Performance</h2>
            {sub_bars}
        </div>
    </div>

    <div class="two-col">
        <div class="section">
            <h2><span class="dot"></span>Top 10 Claude Posts This Week</h2>
            {posts_html}
        </div>
        <div class="section">
            <h2><span class="dot"></span>Top Keywords</h2>
            <div class="keyword-cloud">{kw_html}</div>
        </div>
    </div>

    <div class="section">
        <h2><span class="dot"></span>Title Length Sweet Spot</h2>
        {length_bars}
    </div>

    <div class="section">
        <h2><span class="dot"></span>ML Model — What Predicts Virality</h2>
        <p style="color:#555;font-size:0.75rem;margin-bottom:1rem">Random Forest trained on {posts} posts. Score out of 1.0</p>
        <div class="bar-item"><div class="bar-label"><span>Title length</span><span>0.771</span></div><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div></div>
        <div class="bar-item"><div class="bar-label"><span>Has number in title</span><span>0.070</span></div><div class="bar-track"><div class="bar-fill" style="width:9%"></div></div></div>
        <div class="bar-item"><div class="bar-label"><span>Has question mark</span><span>0.066</span></div><div class="bar-track"><div class="bar-fill" style="width:8.5%"></div></div></div>
        <div class="bar-item"><div class="bar-label"><span>Has code keywords</span><span>0.062</span></div><div class="bar-track"><div class="bar-fill" style="width:8%"></div></div></div>
        <div class="bar-item"><div class="bar-label"><span>Hour of posting</span><span>0.000</span></div><div class="bar-track"><div class="bar-fill" style="width:0%"></div></div></div>
    </div>

    <div class="section">
        <h2><span class="dot"></span>Claude vs Higgsfield — Live Comparison</h2>
        <p style="color:#555;font-size:0.75rem;margin-bottom:1rem">Both datasets scraped live every Sunday night automatically</p>
        <table>
            <thead><tr><th>Metric</th><th>Claude</th><th>Higgsfield</th><th>Gap</th></tr></thead>
            <tbody>
                <tr><td>Posts scraped</td><td class="win">{posts}</td><td class="lose">{h_posts}</td><td>{h_posts_gap}</td></tr>
                <tr><td>Avg score per post</td><td class="win">{avg}</td><td class="lose">{h_avg}</td><td>{h_gap}x more engagement</td></tr>
                <tr><td>Top post score</td><td class="win">{top:,}</td><td class="lose">{h_top:,}</td><td>{h_top_gap}</td></tr>
                <tr><td>Own subreddit avg</td><td class="win">131</td><td class="lose">{h_sub}</td><td>{h_sub_gap}</td></tr>
                <tr><td>Best content format</td><td class="win">Tip/code posts</td><td class="lose">{h_format}</td><td>{h_format_gap}</td></tr>
            </tbody>
        </table>
        <div style="margin-top:1.5rem">
            <h3 style="font-size:0.9rem;font-weight:600;margin-bottom:0.75rem;color:#ccc">Top Higgsfield posts this week</h3>
            {h_posts_html}
        </div>
        <div style="margin-top:1.5rem">
            <h3 style="font-size:0.9rem;font-weight:600;margin-bottom:0.75rem;color:#ccc">Top Higgsfield keywords this week</h3>
            <div class="keyword-cloud">{h_kw_html}</div>
        </div>
    </div>

    <div class="section">
        <h2><span class="dot"></span>Counter-Playbook — 4 Week Plan for Higgsfield</h2>
        <table>
            <thead><tr><th>Week</th><th>Action</th><th>Target</th><th>Why</th></tr></thead>
            <tbody>
                <tr><td style="color:#ff4500;font-weight:600">Week 1</td><td>Move to r/AfterEffects + r/MotionDesign</td><td>Avg score above 50</td><td>r/HiggsefieldAI avg only 13</td></tr>
                <tr><td style="color:#ff4500;font-weight:600">Week 2</td><td>Short titles 30-60 chars with numbers</td><td>One post above 100</td><td>Short titles score 193 vs 52 for long</td></tr>
                <tr><td style="color:#ff4500;font-weight:600">Week 3</td><td>Post API tutorials on r/LocalLLaMA</td><td>Upvote ratio above 0.90</td><td>Code content scores 3.5x more</td></tr>
                <tr><td style="color:#ff4500;font-weight:600">Week 4</td><td>Double down on best format</td><td>Weekly avg above 100</td><td>Compound what works</td></tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2><span class="dot"></span>Data Visualizations — Engagement Analysis</h2>
        <p style="color:#555;font-size:0.75rem;margin-bottom:1rem">Content type performance, subreddit scores, top posts, distribution</p>
        <img src="charts.png" alt="Charts" style="width:100%;border-radius:8px;border:1px solid #333;margin-bottom:1rem;">
        <img src="sentiment_chart.jpg" alt="Sentiment Analysis" style="width:100%;border-radius:8px;border:1px solid #333;margin-bottom:1rem;">
        <img src="chart_extra.jpg" alt="Extra Chart" style="width:100%;border-radius:8px;border:1px solid #333;margin-bottom:1rem;">
        <img src="chart_extra2.jpg" alt="Extra Chart 2" style="width:100%;border-radius:8px;border:1px solid #333;">
    </div>

    <div class="section">
        <h2><span class="dot"></span>Pipeline Architecture</h2>
        <img src="architecture.png" alt="Architecture" style="width:100%;border-radius:8px;border:1px solid #333;">
    </div>

</div>

<div class="footer">
    HackNU 2026 — Growth Engineering Challenge
    <br>Data refreshes every Sunday 11pm automatically via cron job
</div>

<script>
async function triggerRefresh() {{
    const btn = document.getElementById('refresh-btn');
    const overlay = document.getElementById('refresh-overlay');
    btn.disabled = true;
    btn.textContent = 'Scraping...';
    overlay.style.display = 'flex';
    try {{
        await fetch('http://localhost:8888/refresh');
        setTimeout(() => {{ location.reload(); }}, 35000);
    }} catch(e) {{
        overlay.style.display = 'none';
        btn.disabled = false;
        btn.textContent = 'Refresh Data';
        location.reload();
    }}
}}
</script>

</body>
</html>"""

with open('dashboard.html', 'w') as f:
    f.write(html)
print('Dashboard created successfully!')
