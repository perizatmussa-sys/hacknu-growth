import requests
import pandas as pd
import json
import time
from datetime import datetime
from collections import Counter
import re

print("Starting weekly data collection...")

headers = {"User-Agent": "Mozilla/5.0 hacknu-scraper"}

def scrape_reddit(subreddits, search_terms=None):
    posts = []
    for sub in subreddits:
        print(f"Scraping r/{sub}...")
        for sort in ["hot", "top"]:
            url = f"https://www.reddit.com/r/{sub}/{sort}.json?limit=100"
            try:
                r = requests.get(url, headers=headers)
                data = r.json()
                for post in data["data"]["children"]:
                    p = post["data"]
                    posts.append({
                        "id": p["id"],
                        "subreddit": sub,
                        "title": p["title"],
                        "score": p["score"],
                        "upvote_ratio": p["upvote_ratio"],
                        "num_comments": p["num_comments"],
                        "created_utc": p["created_utc"],
                        "url": f"https://reddit.com{p.get('permalink','')}",
                        "author": str(p["author"]),
                        "source": sort
                    })
                time.sleep(2)
            except Exception as e:
                print(f"Error on r/{sub}: {e}")

    if search_terms:
        for term in search_terms:
            print(f"Searching Reddit for '{term}'...")
            url = f"https://www.reddit.com/search.json?q={term.replace(' ','+')}&sort=top&t=month&limit=100"
            try:
                r = requests.get(url, headers=headers)
                data = r.json()
                for post in data["data"]["children"]:
                    p = post["data"]
                    posts.append({
                        "id": p["id"],
                        "subreddit": p["subreddit"],
                        "title": p["title"],
                        "score": p["score"],
                        "upvote_ratio": p["upvote_ratio"],
                        "num_comments": p["num_comments"],
                        "created_utc": p["created_utc"],
                        "url": f"https://reddit.com{p.get('permalink','')}",
                        "author": str(p["author"]),
                        "source": f"search_{term}"
                    })
                time.sleep(2)
            except Exception as e:
                print(f"Error searching '{term}': {e}")

    df = pd.DataFrame(posts)
    if len(df) > 0:
        df = df.drop_duplicates(subset="id")
        df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s")
        df = df.sort_values("score", ascending=False)
    return df

CLAUDE_SUBREDDITS = ["ClaudeAI", "ChatGPT", "LocalLLaMA", "artificial"]
CLAUDE_TERMS = ["Claude AI", "Anthropic Claude"]

HIGGSFIELD_SUBREDDITS = ["HiggsefieldAI", "AIVideo", "MediaSynthesis", "StableDiffusion", "artificial", "generativeAI"]
HIGGSFIELD_TERMS = ["Higgsfield AI", "Higgsfield video"]

print("\n=== Scraping Claude data ===")
claude_df = scrape_reddit(CLAUDE_SUBREDDITS, CLAUDE_TERMS)
claude_df.to_csv("reddit_data.csv", index=False)
print(f"Claude: {len(claude_df)} posts collected")

print("\n=== Scraping Higgsfield data ===")
higgsfield_df = scrape_reddit(HIGGSFIELD_SUBREDDITS, HIGGSFIELD_TERMS)
higgsfield_df.to_csv("higgsfield_live_data.csv", index=False)
print(f"Higgsfield: {len(higgsfield_df)} posts collected")

STOPWORDS = set(["a","an","the","to","of","in","is","it","i",
"for","and","on","with","my","you","we","be","are","was","at",
"by","or","as","so","do","if","me","s","this","that","have",
"has","not","but","from","your","can","its","how","why","what",
"when","they","their","will","about","use","using","just","get",
"out","up","more","some","been","had","would","could","should"])

def get_keywords(df):
    words = []
    for title in df["title"].dropna():
        for word in re.findall(r'\b[a-z]{3,}\b', title.lower()):
            if word not in STOPWORDS:
                words.append(word)
    return Counter(words).most_common(15)

def get_content_scores(df):
    return {
        "Code": round(df[df["title"].str.lower().str.contains(
            "code|api|script|python|token", na=False)]["score"].mean(), 1),
        "Tips": round(df[df["title"].str.lower().str.contains(
            "tip|trick|hack|how|guide", na=False)]["score"].mean(), 1),
        "Comparison": round(df[df["title"].str.lower().str.contains(
            "vs|better|worse|compared", na=False)]["score"].mean(), 1),
        "Questions": round(df[df["title"].str.contains(
            r"\?", na=False)]["score"].mean(), 1),
    }

def get_length_scores(df):
    df = df.copy()
    df["title_length"] = df["title"].str.len()
    df["length_bucket"] = pd.cut(
        df["title_length"],
        bins=[0,30,60,90,120,999],
        labels=["very_short","short","medium","long","very_long"]
    )
    return df.groupby(
        "length_bucket", observed=True
    )["score"].mean().round(1).to_dict()

claude_avg = round(claude_df["score"].mean(), 1)
claude_top = int(claude_df["score"].max())
claude_top_post = claude_df.iloc[0]

higgsfield_avg = round(higgsfield_df["score"].mean(), 1) if len(higgsfield_df) > 0 else 0
higgsfield_top = int(higgsfield_df["score"].max()) if len(higgsfield_df) > 0 else 0
higgsfield_top_post = higgsfield_df.iloc[0] if len(higgsfield_df) > 0 else None
higgsfield_sub_avg = round(
    higgsfield_df[higgsfield_df["subreddit"]=="HiggsefieldAI"]["score"].mean(), 1
) if len(higgsfield_df) > 0 else 0

higgsfield_top10 = []
if len(higgsfield_df) > 0:
    higgsfield_top10 = higgsfield_df.head(10)[
        ["title","score","subreddit","url"]
    ].to_dict("records")

higgsfield_keywords = get_keywords(higgsfield_df) if len(higgsfield_df) > 0 else []
higgsfield_content_scores = get_content_scores(higgsfield_df) if len(higgsfield_df) > 0 else {}
higgsfield_subreddit_scores = higgsfield_df.groupby("subreddit")["score"].mean().round(1).to_dict() if len(higgsfield_df) > 0 else {}

alerts = []

if claude_top > 1000:
    alerts.append({
        "type": "viral",
        "message": f"VIRAL ALERT: Claude post scored {claude_top} this week",
        "color": "red",
        "post_title": claude_top_post["title"],
        "post_url": claude_top_post["url"],
        "post_score": claude_top,
        "post_subreddit": claude_top_post["subreddit"],
        "action": "Engage immediately — analyse this post format and replicate it"
    })

if higgsfield_avg > 0 and claude_avg / higgsfield_avg > 3:
    alerts.append({
        "type": "warning",
        "message": f"GAP ALERT: Claude scores {(claude_avg/higgsfield_avg):.1f}x more than Higgsfield",
        "color": "yellow",
        "post_title": "",
        "post_url": "",
        "post_score": 0,
        "post_subreddit": "",
        "action": "Higgsfield needs to switch content format immediately"
    })

claude_keywords = get_keywords(claude_df)
new_keywords = [w for w, c in claude_keywords[:3]]
alerts.append({
    "type": "info",
    "message": f"Top Claude topics this week: {', '.join(new_keywords)}",
    "color": "green",
    "post_title": "",
    "post_url": "",
    "post_score": 0,
    "post_subreddit": "",
    "action": f"Create Higgsfield content about {new_keywords[0]} this week"
})

if len(higgsfield_df) > 0 and higgsfield_top > 100:
    h_top = higgsfield_df.iloc[0]
    alerts.append({
        "type": "info",
        "message": f"Higgsfield top post this week: score {higgsfield_top}",
        "color": "green",
        "post_title": h_top["title"],
        "post_url": h_top["url"],
        "post_score": higgsfield_top,
        "post_subreddit": h_top["subreddit"],
        "action": "Analyse this Higgsfield post — replicate what worked"
    })

report = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "total_posts": len(claude_df),
    "avg_score": claude_avg,
    "top_score": claude_top,
    "top_post_title": claude_top_post["title"],
    "top_post_url": claude_top_post["url"],
    "top_post_subreddit": claude_top_post["subreddit"],
    "subreddit_scores": claude_df.groupby("subreddit")["score"].mean().round(1).to_dict(),
    "content_scores": get_content_scores(claude_df),
    "top_keywords": [{"word": w, "count": c} for w, c in claude_keywords],
    "top10_posts": claude_df.head(10)[["title","score","subreddit","url"]].to_dict("records"),
    "length_scores": get_length_scores(claude_df),
    "higgsfield_total_posts": len(higgsfield_df),
    "higgsfield_avg": higgsfield_avg,
    "higgsfield_top": higgsfield_top,
    "higgsfield_top_title": higgsfield_top_post["title"] if higgsfield_top_post is not None else "",
    "higgsfield_top_url": higgsfield_top_post["url"] if higgsfield_top_post is not None else "",
    "higgsfield_sub_avg": higgsfield_sub_avg,
    "higgsfield_gap": round(claude_avg / higgsfield_avg, 1) if higgsfield_avg > 0 else 0,
    "higgsfield_top10": higgsfield_top10,
    "higgsfield_keywords": [{"word": w, "count": c} for w, c in higgsfield_keywords],
    "higgsfield_content_scores": higgsfield_content_scores,
    "higgsfield_subreddit_scores": higgsfield_subreddit_scores,
    "alerts": alerts
}

with open("report_data.json", "w") as f:
    json.dump(report, f, indent=2)

print(f"\nReport saved.")
print(f"Claude: {len(claude_df)} posts, avg {claude_avg}, top {claude_top}")
print(f"Higgsfield: {len(higgsfield_df)} posts, avg {higgsfield_avg}, top {higgsfield_top}")
print(f"Alerts: {len(alerts)}")
print("Done.")
