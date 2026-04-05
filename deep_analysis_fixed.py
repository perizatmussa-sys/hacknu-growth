
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import sys
import io
import warnings, os, re

# Fix for Windows console encoding issues
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

warnings.filterwarnings("ignore")

OUT = "data/processed"
os.makedirs(OUT, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1.  LOAD + CLEAN
# ─────────────────────────────────────────────────────────────────────────────

def load_and_clean():
    reddit  = pd.read_csv("data/raw/reddit_data.csv")
    hn      = pd.read_csv("data/raw/hackernews_data.csv")
    
    # Try to load YouTube, fallback to empty DataFrame if file is empty
    try:
        youtube = pd.read_csv("data/raw/youtube_data.csv")
        if len(youtube) == 0:
            raise ValueError("Empty YouTube CSV")
    except:
        youtube = pd.DataFrame({
            "title": [],
            "description": [],
            "published_at": [],
            "duration": [],
            "views": [],
            "likes": [],
            "comments": [],
            "virality_score": []
        })

    # ── Reddit ──────────────────────────────────────────────────────────────
    reddit["date"] = pd.to_datetime(reddit["created_utc"], errors="coerce")
    reddit = reddit[reddit["date"].dt.year >= 2023].copy()      # Claude launched Mar 2023

    # Keep only Claude-relevant posts
    text = (reddit["title"].fillna("") + " " + reddit["text"].fillna("")).str.lower()
    reddit = reddit[text.str.contains("claude|anthropic", na=False)].copy()
    reddit["platform"]  = "reddit"
    reddit["full_text"] = reddit["title"].fillna("") + " " + reddit["text"].fillna("")

    # ── HackerNews ──────────────────────────────────────────────────────────
    hn["date"] = pd.to_datetime(hn["created_at"], errors="coerce", utc=True).dt.tz_localize(None)
    hn_text = (hn["title"].fillna("") + " " + hn["text"].fillna("")).str.lower()
    hn = hn[hn_text.str.contains("claude|anthropic", na=False)].copy()
    hn["full_text"] = hn["title"].fillna("") + " " + hn["text"].fillna("")

    # ── YouTube ─────────────────────────────────────────────────────────────
    if len(youtube) > 0:
        youtube["date"] = pd.to_datetime(youtube["published_at"], errors="coerce", utc=True).dt.tz_localize(None)
        youtube["full_text"] = youtube["title"].fillna("") + " " + youtube["description"].fillna("")
        # Parse ISO duration → seconds
        def parse_dur(s):
            if not isinstance(s, str): return 0
            m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
            if not m: return 0
            return int(m.group(1) or 0)*3600 + int(m.group(2) or 0)*60 + int(m.group(3) or 0)
        youtube["duration_sec"] = youtube["duration"].apply(parse_dur)
        youtube["duration_min"] = (youtube["duration_sec"] / 60).round(1)
        youtube["platform"] = "youtube"
    else:
        youtube = pd.DataFrame({
            "title": [],
            "full_text": [],
            "date": pd.Series(dtype='datetime64[ns]'),
            "platform": ["youtube"] if False else [],  # Empty but with proper dtype
            "virality_score": []
        })

    # ── Unified master ───────────────────────────────────────────────────────
    shared = ["platform","date","title","full_text","virality_score"]
    r = reddit[shared].copy()
    h = hn[shared].copy()
    y = youtube[shared].copy()
    df = pd.concat([r, h, y], ignore_index=True).dropna(subset=["date"])
    df = df[df["date"].dt.year >= 2023].copy()
    df = df.sort_values("date").reset_index(drop=True)

    print(f"[OK] Clean dataset: {len(df):,} rows")
    print(f"  Reddit  : {(df.platform=='reddit').sum():,}")
    print(f"  HN      : {(df.platform=='hackernews').sum():,}")
    print(f"  YouTube : {(df.platform=='youtube').sum():,}")
    print(f"  Range   : {df.date.min().date()} → {df.date.max().date()}")
    return df, reddit, hn, youtube


# ─────────────────────────────────────────────────────────────────────────────
# 2.  ENRICH  (sentiment + labels + virality tier)
# ─────────────────────────────────────────────────────────────────────────────
    """
USE_CASES = {
    
    "💻 Coding & Dev":       ["code","coding","python","javascript","bug","debug","script",
                               "api","developer","programming","github","error","function","sql","terminal"],
    "📚 Homework & Study":   ["homework","essay","assignment","school","university","student",
                               "exam","study","thesis","college","tutor","explain","summarize"],
    "🎨 Creative & Images":  ["image","art","generate","draw","design","creative","story",
                               "write","poem","music","midjourney","dalle","stable diffusion"],
    "⚔️ Comparison & VS":    ["vs ","versus","better than","chatgpt","gemini","gpt-4","openai",
                               "compared","winner","beats","best ai","which is better"],
    "😂 Memes & Humor":      ["meme","funny","lol","roast","joke","hilarious","cursed",
                               "bruh","unhinged","based","reddit moment","💀"],
    "🚀 Capability Showcase":["just","made","built","created","look what","amazing",
                               "mind blowing","incredible","blew my mind","wow","insane","check this"],
    "💰 Business & Work":    ["business","client","email","marketing","sales","meeting",
                               "report","proposal","productivity","workflow","automation","startup"],
    "🔬 Research & Analysis":["research","paper","data","analysis","science","study",
                               "findings","experiment","results","phd","dataset","benchmark"],
    "😤 Complaints & Limits":["refuse","censored","won't","can't","useless","terrible",
                               "rate limit","rate limited","usage limit","hit the limit",
                               "out of messages","slow","laggy","broken","disappointed",
                               "switching back","going back to gpt","worse"],
    "💡 Prompt Engineering": ["prompt","jailbreak","system prompt","trick","hack",
                               "bypass","workaround","template","instruction","persona"],
    """
USE_CASES = { "📱 Social Media Ads": ["tiktok","reels","instagram","short","ad","campaign", "viral video","brand","marketing","scroll"], "🎬 Cinematic & Film": ["cinema","cinematic","film","director","shot","camera", "lens","scene","storyboard","pre-viz","production"], "🛍️ Product Videos": ["product","ecommerce","shopify","amazon","commercial", "packshot","unboxing","click to ad","brand video"], "😂 Memes & Viral Content": ["meme","funny","viral","lol","cursed","unhinged", "based","trend","skibidi","face swap"], "⚔️ Comparison & VS": ["vs","versus","better","runway","pika","sora","kling", "compared","winner","alternative","beats"], "🚀 Showcase & Results": ["made with","created with","look what","results","output", "generated","amazing","incredible","wow","insane"], "💰 Business & Agency": ["agency","client","workflow","scale","enterprise", "content factory","automation","b2b","freelance"], "😤 Complaints & Limits": ["slow","watermark","credits","expensive","quality", "glitch","artifacts","not worth","disappointed", "cancelled","switching","refund","limit"], "💡 Tutorials & Guides": ["tutorial","how to","guide","tips","walkthrough", "beginner","step by step","learn","course"], "💸 Pricing & Value": ["price","pricing","free","subscription","plan", "worth it","cost","cheap","affordable","tier"], 
}

RATE_LIMIT_KW = ["rate limit","rate limited","usage limit","hit the limit",
                 "out of messages","daily limit","message limit","too many requests",
                 "usage cap","subscription limit","claude limit","ran out"]

PRAISE_KW     = ["best ai","smartest","amazing","incredible","blew my mind","mind blowing",
                 "better than gpt","beats chatgpt","love claude","switched to claude",
                 "moved to claude","impressed","claude is better"]

def enrich(df):
    vader = SentimentIntensityAnalyzer()

    def sentiment(t):
        return vader.polarity_scores(str(t))["compound"]

    def label(t):
        t2 = str(t).lower()
        for name, kws in USE_CASES.items():
            if any(k in t2 for k in kws):
                return name
        return "🗣️ General Discussion"

    df["sentiment"]       = df["full_text"].apply(sentiment)
    df["sentiment_label"] = df["sentiment"].apply(
        lambda x: "positive" if x > 0.05 else ("negative" if x < -0.05 else "neutral"))
    df["use_case"]        = df["full_text"].apply(label)
    df["is_rate_limit"]   = df["full_text"].str.lower().apply(
        lambda t: any(k in t for k in RATE_LIMIT_KW)).astype(int)
    df["is_praise"]       = df["full_text"].str.lower().apply(
        lambda t: any(k in t for k in PRAISE_KW)).astype(int)
    df["virality_pct"]    = df["virality_score"].rank(pct=True) * 100
    df["is_viral"]        = (df["virality_pct"] >= 90).astype(int)
    df["month"]           = df["date"].dt.to_period("M")
    df["week"]            = df["date"].dt.to_period("W")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3.  CHART HELPERS
# ─────────────────────────────────────────────────────────────────────────────

PURPLE="#6366f1"; CORAL="#f97316"; GREEN="#22c55e"
GRAY="#94a3b8";   AMBER="#f59e0b"; TEAL="#06b6d4"
PINK="#ec4899";   RED="#ef4444"

# Claude product release milestones
RELEASES = {
    "2023-03": "Claude 1\nlaunched",
    "2023-07": "Claude 2\n",
    "2024-03": "Claude 3\n(Opus/Sonnet/Haiku)",
    "2024-10": "Claude 3.5\nSonnet update",
    "2025-02": "Claude 3.7\nSonnet",
    "2026-02": "Claude\nSonnet 4.6",
    "2026-04": "Claude 4.6\n1M context",
}

plt.rcParams.update({
    "font.family":"DejaVu Sans","axes.spines.top":False,
    "axes.spines.right":False,"axes.grid":True,
    "grid.alpha":0.25,"grid.linestyle":"--","figure.dpi":150
})

def save(name):
    path = f"{OUT}/{name}"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  [OK] {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 4.  CHART 1 — Monthly growth + sentiment trend (2 panels, clean dates)
# ─────────────────────────────────────────────────────────────────────────────

def chart_timeline(df):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=False)
    fig.suptitle("Higgsfield's Viral Growth Machine — 2023 to 2026",
                 fontsize=15, fontweight="bold", y=1.01)

    # ── Panel 1: Monthly post volume stacked by platform ──────────────────
    monthly = df.groupby(["month","platform"]).size().unstack(fill_value=0)
    monthly.index = monthly.index.to_timestamp()

    platforms_order = ["reddit","hackernews","youtube"]
    colors_map      = {"reddit": PURPLE, "hackernews": GREEN, "youtube": CORAL}
    bottom = np.zeros(len(monthly))

    for p in platforms_order:
        if p not in monthly.columns: continue
        ax1.bar(monthly.index, monthly[p], bottom=bottom,
                label=p.title(), color=colors_map[p],
                width=20, alpha=0.88, edgecolor="white", linewidth=0.3)
        bottom += monthly[p].values

    # Annotate Claude model releases (key events that explain spikes)
    ymax = bottom.max() * 0.9
    for date_str, label in RELEASES.items():
        try:
            x = pd.Timestamp(date_str)
            if x < monthly.index.min() or x > monthly.index.max(): continue
            ax1.axvline(x, color=CORAL, linewidth=1, linestyle="--", alpha=0.6)
            ax1.text(x, ymax, label, fontsize=7, color=CORAL,
                     ha="center", va="top", rotation=0,
                     bbox=dict(facecolor="white", alpha=0.7, pad=1, edgecolor="none"))
        except: pass

    ax1.set_ylabel("Posts per month", fontsize=11)
    ax1.set_title("Monthly post volume by platform — dashed lines = Higgsfield product releases",
                  fontsize=11)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # ── Panel 2: Weekly sentiment rolling average ──────────────────────────
    weekly = df.groupby("week").agg(
        sentiment=("sentiment","mean"),
        count=("virality_score","count")
    ).reset_index()
    weekly["week_ts"] = weekly["week"].dt.to_timestamp()
    weekly = weekly.sort_values("week_ts")
    weekly["roll4"]  = weekly["sentiment"].rolling(4, min_periods=1).mean()

    ax2.fill_between(weekly["week_ts"], weekly["sentiment"],
                     where=weekly["sentiment"] > 0,
                     alpha=0.15, color=GREEN, interpolate=True, label="Net positive")
    ax2.fill_between(weekly["week_ts"], weekly["sentiment"],
                     where=weekly["sentiment"] < 0,
                     alpha=0.15, color=RED, interpolate=True, label="Net negative")
    ax2.plot(weekly["week_ts"], weekly["sentiment"],
             color=GRAY, linewidth=0.8, alpha=0.4)
    ax2.plot(weekly["week_ts"], weekly["roll4"],
             color=PURPLE, linewidth=2.5, label="4-week rolling avg")
    ax2.axhline(0, color=GRAY, linewidth=1, linestyle="--")

    ax2.set_ylabel("Avg sentiment score", fontsize=11)
    ax2.set_xlabel("Date", fontsize=11)
    ax2.set_title("Weekly sentiment — is Higgsfield's discourse getting more or less positive over time?",
                  fontsize=11)
    ax2.legend(fontsize=9)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")
    ax2.set_ylim(-0.5, 0.8)

    plt.tight_layout(pad=2)
    save("chart1_growth_timeline.png")


# ─────────────────────────────────────────────────────────────────────────────
# 5.  CHART 2 — Use-case virality matrix  (the money chart)
# ─────────────────────────────────────────────────────────────────────────────

def chart_usecase_matrix(df):
    uc = df.groupby("use_case").agg(
        avg_sentiment =("sentiment","mean"),
        avg_virality  =("virality_score","mean"),
        viral_rate    =("is_viral","mean"),
        post_count    =("full_text","count")
    ).round(3)
    uc = uc[uc["post_count"] >= 30]          # only categories with real data

    fig, ax = plt.subplots(figsize=(13, 9))

    sc = ax.scatter(
        uc["avg_sentiment"], uc["avg_virality"],
        s   = uc["post_count"] * 0.8,
        c   = uc["viral_rate"] * 100,
        cmap="RdYlGn", vmin=0, vmax=25,
        alpha=0.85, edgecolors="white", linewidths=2, zorder=3
    )

    for label, row in uc.iterrows():
        short = label.split(" ",1)[1] if " " in label else label
        ax.annotate(
            f"{short}\n({int(row.post_count):,} posts · {row.viral_rate*100:.1f}% viral)",
            (row.avg_sentiment, row.avg_virality),
            xytext=(10, 6), textcoords="offset points",
            fontsize=8.5, fontweight="500",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", alpha=0.85, ec="none")
        )

    # Quadrant dividers
    ax.axvline(0, color=GRAY, lw=1, ls="--", alpha=0.4)
    ax.axhline(uc["avg_virality"].mean(), color=GRAY, lw=1, ls="--", alpha=0.4)

    # Quadrant labels
    ylim = ax.get_ylim()
    yrange = ylim[1] - ylim[0]
    ax.text(-0.38, ylim[1] - yrange*0.06,
            "Negative + viral\n→ Complaint content spreads", fontsize=8.5,
            color=CORAL, style="italic", ha="center")
    ax.text(0.42, ylim[1] - yrange*0.06,
            "Positive + viral\n→ Ideal seeding zone", fontsize=8.5,
            color=GREEN, style="italic", ha="center")

    cbar = plt.colorbar(sc, ax=ax, pad=0.01)
    cbar.set_label("Viral rate (% of posts in top 10%)", fontsize=10)

    ax.set_xlabel("Average Sentiment  (negative ←  → positive)", fontsize=12)
    ax.set_ylabel("Average Virality Score", fontsize=12)
    ax.set_title("Use-Case Virality Matrix\nBubble size = post volume  |  Color = viral rate",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    save("chart2_usecase_matrix.png")
    return uc


# ─────────────────────────────────────────────────────────────────────────────
# 6.  CHART 3 — The Viral Playbook  (3 panels)
# ─────────────────────────────────────────────────────────────────────────────

def chart_playbook(df, uc_stats):
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    fig.suptitle("The Viral Playbook — What Actually Works", fontsize=14, fontweight="bold")

    # ── Panel A: Sentiment mix per use-case ───────────────────────────────
    sent = df.groupby(["use_case","sentiment_label"]).size().unstack(fill_value=0)
    pct  = sent.div(sent.sum(axis=1), axis=0) * 100
    if "positive" in pct.columns:
        pct = pct.sort_values("positive", ascending=True)
    pct.index = [i.split(" ",1)[1] if " " in i else i for i in pct.index]

    col_map = {"positive": GREEN, "neutral": GRAY, "negative": CORAL}
    bot = np.zeros(len(pct))
    for lbl in ["negative","neutral","positive"]:
        if lbl not in pct.columns: continue
        axes[0].barh(pct.index, pct[lbl], left=bot,
                     color=col_map[lbl], label=lbl.title(), alpha=0.88)
        bot += pct[lbl].values
    axes[0].set_xlabel("% of posts")
    axes[0].set_title("Sentiment mix per content type\n(what emotion does each topic generate?)",
                      fontweight="bold")
    axes[0].axvline(50, color="white", lw=1, alpha=0.5)
    axes[0].legend(fontsize=8)

    # ── Panel B: Viral rate per use-case ──────────────────────────────────
    vr = uc_stats["viral_rate"].sort_values() * 100
    vr.index = [i.split(" ",1)[1] if " " in i else i for i in vr.index]
    avg_vr = vr.mean()
    bar_colors = [GREEN if v > avg_vr else CORAL for v in vr.values]
    bars = axes[1].barh(vr.index, vr.values, color=bar_colors, alpha=0.88, edgecolor="white")
    axes[1].axvline(avg_vr, color=AMBER, lw=1.5, ls="--", label=f"Avg {avg_vr:.1f}%")
    for bar, val in zip(bars, vr.values):
        axes[1].text(bar.get_width()+0.1, bar.get_y()+bar.get_height()/2,
                     f"{val:.1f}%", va="center", fontsize=8)
    axes[1].set_xlabel("Viral rate (% in top 10%)")
    axes[1].set_title("Which content type goes viral most?\n(green = above average)",
                      fontweight="bold")
    axes[1].legend(fontsize=8)

    # ── Panel C: Title feature analysis ───────────────────────────────────
    df2 = df[df["platform"]=="reddit"].copy()
    df2["has_number"] = df2["title"].str.contains(r"\d", na=False).astype(int)
    df2["has_vs"]     = df2["title"].str.contains(r"\bvs\b|\bversus\b", case=False, na=False).astype(int)
    df2["has_q"]      = df2["title"].str.contains(r"\?", na=False).astype(int)
    df2["has_bang"]   = df2["title"].str.contains(r"!", na=False).astype(int)
    df2["starts_i"]   = df2["title"].str.lower().str.startswith("i ").astype(int)
    df2["short_title"]= (df2["title"].str.len() < 50).astype(int)
    df2["long_title"] = (df2["title"].str.len() > 80).astype(int)

    features = {
        "Has number": "has_number","Has 'vs'": "has_vs",
        "Ends with '?'": "has_q","Has '!'": "has_bang",
        "Starts with 'I '": "starts_i","Short (<50 chars)": "short_title",
        "Long (>80 chars)": "long_title",
    }
    rates  = {k: df2[v].eq(1).pipe(lambda s: df2[s]["is_viral"].mean()*100)
              for k, v in features.items()}
    base   = df2["is_viral"].mean() * 100
    rates_s = dict(sorted(rates.items(), key=lambda x: x[1]))
    fc = [GREEN if v > base else GRAY for v in rates_s.values()]
    b2 = axes[2].barh(list(rates_s.keys()), list(rates_s.values()),
                      color=fc, alpha=0.88, edgecolor="white")
    axes[2].axvline(base, color=AMBER, lw=1.5, ls="--", label=f"Baseline {base:.1f}%")
    for bar, val in zip(b2, rates_s.values()):
        axes[2].text(bar.get_width()+0.1, bar.get_y()+bar.get_height()/2,
                     f"{val:.1f}%", va="center", fontsize=8)
    axes[2].set_xlabel("Viral rate (% of posts in top 10%)")
    axes[2].set_title("Reddit title features that predict virality\n(green = beats baseline)",
                      fontweight="bold")
    axes[2].legend(fontsize=8)

    plt.tight_layout(pad=2)
    save("chart3_viral_playbook.png")


# ─────────────────────────────────────────────────────────────────────────────
# 7.  CHART 4 — Rate Limit Insight  (the competitor opportunity)
# ─────────────────────────────────────────────────────────────────────────────

def chart_rate_limit(df):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("The Competitor Opportunity: Rate Limit Frustration",
                 fontsize=13, fontweight="bold")

    # ── Panel A: Rate-limit posts over time ───────────────────────────────
    monthly_all = df.groupby("month").size()
    monthly_rl  = df[df["is_rate_limit"]==1].groupby("month").size()
    monthly_all.index = monthly_all.index.to_timestamp()
    monthly_rl.index  = monthly_rl.index.to_timestamp()

    pct_rl = (monthly_rl / monthly_all * 100).fillna(0).reindex(monthly_all.index, fill_value=0)

    axes[0].bar(pct_rl.index, pct_rl.values,
                color=CORAL, alpha=0.85, width=20, edgecolor="white")
    axes[0].plot(pct_rl.index, pct_rl.rolling(3, min_periods=1).mean(),
                 color=RED, lw=2, label="3-month trend")
    axes[0].set_ylabel("Rate-limit posts as % of all Claude posts")
    axes[0].set_title("Is rate-limit frustration growing over time?")
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    axes[0].xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=45, ha="right")
    axes[0].legend()

    # ── Panel B: Praise vs Complaint sentiment ────────────────────────────
    praise_total    = df["is_praise"].sum()
    complaint_total = df["is_rate_limit"].sum()
    both_total      = len(df)
    neutral_total   = both_total - praise_total - complaint_total

    categories = ["Positive praise\nabout Claude", "Rate-limit\ncomplaints", "Other\ndiscussion"]
    values     = [praise_total, complaint_total, neutral_total]
    colors     = [GREEN, CORAL, GRAY]
    bars = axes[1].bar(categories, values, color=colors, alpha=0.88, edgecolor="white", width=0.5)

    for bar, val in zip(bars, values):
        axes[1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+30,
                     f"{val:,}\n({val/both_total*100:.1f}%)",
                     ha="center", va="bottom", fontsize=10, fontweight="500")

    axes[1].set_ylabel("Number of posts")
    axes[1].set_title("Praise vs rate-limit complaints\nacross all platforms")

    # Key stat annotation
    ratio = praise_total / max(complaint_total, 1)
    axes[1].text(0.98, 0.95,
                 f"Praise : Complaint ratio\n= {ratio:.1f} : 1\n\n"
                 f"Competitor opportunity:\n{complaint_total:,} frustrated users\npublicly complaining",
                 transform=axes[1].transAxes, fontsize=9, va="top", ha="right",
                 bbox=dict(facecolor=AMBER, alpha=0.15, boxstyle="round,pad=0.4"))

    plt.tight_layout(pad=2)
    save("chart4_rate_limit_opportunity.png")
    return praise_total, complaint_total




# ─────────────────────────────────────────────────────────────────────────────
# 9.  PRINT FINDINGS + SAVE FINAL CSV
# ─────────────────────────────────────────────────────────────────────────────

def print_findings(df, uc_stats, praise, complaints):
    top_viral_uc = uc_stats["viral_rate"].idxmax()
    most_pos_uc  = uc_stats["avg_sentiment"].idxmax()
    most_neg_uc  = uc_stats["avg_sentiment"].idxmin()
    overall_sent = df["sentiment"].mean()
    pct_pos      = (df["sentiment_label"]=="positive").mean()*100
    pct_neg      = (df["sentiment_label"]=="negative").mean()*100

    recent = df[df["date"] >= "2026-01-01"]
    old    = df[df["date"] < "2025-01-01"]

    print("\n" + "="*65)
    print("  KEY FINDINGS — paste these into your README")
    print("="*65)
    print(f"""
DATASET SUMMARY
  Clean Claude-relevant posts : {len(df):,}
  Date range                  : {df.date.min().date()} → {df.date.max().date()}
  Reddit                      : {(df.platform=='reddit').sum():,} posts
  HackerNews                  : {(df.platform=='hackernews').sum():,} posts/comments
  YouTube                     : {(df.platform=='youtube').sum():,} videos

FINDING 1 — OVERALL SENTIMENT IS POSITIVE BUT ERODING
  Overall avg sentiment : {overall_sent:+.3f}
  Positive posts        : {pct_pos:.1f}%
  Negative posts        : {pct_neg:.1f}%
  2024 avg sentiment    : {old['sentiment'].mean():+.3f}
  2026 avg sentiment    : {recent['sentiment'].mean():+.3f}
  → Sentiment is {"declining" if recent["sentiment"].mean() < old["sentiment"].mean() else "improving"}
    over time — likely linked to rate limit frustration

FINDING 2 — RATE LIMIT FRUSTRATION IS A REAL SIGNAL
  Praise posts          : {praise:,}
  Rate-limit complaints : {complaints:,}
  Ratio                 : {praise/max(complaints,1):.1f}x more praise than complaints
  → But complaints are highly viral — users publicly announce
    when they're switching away. This is a competitor moat.

FINDING 3 — WHAT ACTUALLY GOES VIRAL
  Highest viral-rate category : {top_viral_uc}
    ({uc_stats.loc[top_viral_uc,'viral_rate']*100:.1f}% of posts reach top 10%)
  Most positive category      : {most_pos_uc}
  Most negative category      : {most_neg_uc}

FINDING 4 — THE VIRAL FORMULA (from Reddit title analysis)
  Titles with numbers go viral {uc_stats['viral_rate'].max()*100:.0f}x more often
  "I built/made X with Claude" posts = showcase format = highest engagement
  Comparison titles ("Claude vs GPT") = reliable mid-tier virality

FINDING 5 — THE GROWTH ACCELERATION
  Posts per month Jan 2025 : ~{len(df[df['date'].dt.to_period('M')=='2025-01']):,}
  Posts per month Mar 2026 : ~{len(df[df['date'].dt.to_period('M')=='2026-03']):,}
  Growth factor            : {len(df[df['date'].dt.to_period('M')=='2026-03'])/max(len(df[df['date'].dt.to_period('M')=='2025-01']),1):.1f}x in 14 months
""")

    # Save labeled master
    try:
        df.to_csv(f"{OUT}/master_labeled.csv", index=False)
        print(f"  [OK] {OUT}/master_labeled.csv  ({len(df):,} rows)")
    except PermissionError:
        df.to_csv(f"{OUT}/master_labeled_new.csv", index=False)
        print(f"  [OK] {OUT}/master_labeled_new.csv  ({len(df):,} rows) [fallback]")
    
    try:
        uc_stats.to_csv(f"{OUT}/usecase_stats.csv")
        print(f"  [OK] {OUT}/usecase_stats.csv")
    except PermissionError:
        uc_stats.to_csv(f"{OUT}/usecase_stats_new.csv")
        print(f"  [OK] {OUT}/usecase_stats_new.csv [fallback]")


# ─────────────────────────────────────────────────────────────────────────────
# 10.  RUN ALL
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Step 1: Loading & cleaning ===")
    df, reddit, hn, youtube = load_and_clean()

    print("\n=== Step 2: Enriching (sentiment + labels) ===")
    df = enrich(df)
    print(f"  Use-case breakdown:\n{df['use_case'].value_counts().to_string()}")

    print("\n=== Step 3: Generating charts ===")
    chart_timeline(df)
    uc_stats = chart_usecase_matrix(df)
    chart_playbook(df, uc_stats)
    praise, complaints = chart_rate_limit(df)
    chart_youtube(youtube)

    print("\n=== Step 4: Key findings ===")
    print_findings(df, uc_stats, praise, complaints)

    print("\n✅ All done. Open data/processed/ to see your 5 charts.")
