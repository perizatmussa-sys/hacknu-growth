import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("/home/perizat/Documents/reddit_data.csv")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Claude Viral Growth Analysis", fontsize=16)

# Chart 1 - avg score by subreddit
df.groupby("subreddit")["score"].mean().sort_values().plot(
    kind="barh", ax=axes[0,0], color="#378ADD"
)
axes[0,0].set_title("Avg Score by Subreddit")

# Chart 2 - content type performance
content_scores = {
    "Comparison": df[df["title"].str.lower().str.contains("vs|better|worse|compared", na=False)]["score"].mean(),
    "Code": df[df["title"].str.lower().str.contains("code|coding|script|api", na=False)]["score"].mean(),
    "Tips/Hacks": df[df["title"].str.lower().str.contains("tip|trick|hack|how|guide", na=False)]["score"].mean(),
    "Questions": df[df["title"].str.contains("\?", na=False)]["score"].mean(),
}
pd.Series(content_scores).sort_values().plot(
    kind="barh", ax=axes[0,1], color="#1D9E75"
)
axes[0,1].set_title("Avg Score by Content Type")

# Chart 3 - top 10 posts
top10 = df.nlargest(10, "score")
axes[1,0].barh(
    range(len(top10)),
    top10["score"],
    color="#D85A30"
)
axes[1,0].set_yticks(range(len(top10)))
axes[1,0].set_yticklabels(
    [t[:40]+"..." for t in top10["title"]],
    fontsize=7
)
axes[1,0].set_title("Top 10 Posts by Score")

# Chart 4 - posts per subreddit
df["subreddit"].value_counts().plot(
    kind="pie", ax=axes[1,1],
    autopct="%1.1f%%"
)
axes[1,1].set_title("Posts Distribution")

plt.tight_layout()
plt.savefig("/home/perizat/Documents/charts.png", dpi=150)
print("Charts saved to charts.png")
