import requests
import pandas as pd
import time

SUBREDDITS = ["ClaudeAI", "ChatGPT", "artificial", "LocalLLaMA"]
headers = {"User-Agent": "Mozilla/5.0 hacknu-scraper"}
posts_data = []

def scrape_subreddit(sub):
    print(f"Scraping r/{sub}...")
    url = f"https://www.reddit.com/r/{sub}/hot.json?limit=100"
    try:
        r = requests.get(url, headers=headers)
        data = r.json()
        for post in data["data"]["children"]:
            p = post["data"]
            posts_data.append({
                "id": p["id"],
                "subreddit": sub,
                "title": p["title"],
                "score": p["score"],
                "upvote_ratio": p["upvote_ratio"],
                "num_comments": p["num_comments"],
                "created_utc": p["created_utc"],
                "url": p["url"],
                "selftext": str(p["selftext"])[:300],
                "author": str(p["author"]),
                "source": "hot"
            })
        time.sleep(2)
    except Exception as e:
        print(f"Error: {e}")

for sub in SUBREDDITS:
    scrape_subreddit(sub)

df = pd.DataFrame(posts_data)
df = df.drop_duplicates(subset="id")
df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s")
df = df.sort_values("score", ascending=False)
df.to_csv("reddit_data.csv", index=False)
print(f"Done. {len(df)} posts saved to reddit_data.csv")
