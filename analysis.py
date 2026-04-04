import pandas as pd
from collections import Counter
import re

df = pd.read_csv("/home/perizat/Documents/reddit_data.csv")

print("=== TOTAL POSTS ===")
print(len(df))

print("\n=== TOP 10 POSTS BY SCORE ===")
print(df[["title","score","subreddit"]].head(10).to_string())

print("\n=== BEST SUBREDDIT ===")
print(df.groupby("subreddit")["score"].mean().sort_values(ascending=False))

# Filter out common useless words
STOPWORDS = set([
    "a","an","the","to","of","in","is","it","i","for",
    "and","on","with","my","you","we","be","are","was",
    "at","by","or","as","so","do","if","me","s","4",
    "this","that","have","has","not","but","from","your",
    "can","its","how","why","what","when","they","their",
    "will","about","use","using","just","get","out","up",
    "more","some","been","had","would","could","should",
    "than","then","there","which","who","him","her","his"
])

print("\n=== TOP MEANINGFUL KEYWORDS IN TITLES ===")
words = []
for title in df["title"].dropna():
    for word in re.findall(r'\b[a-z]{3,}\b', title.lower()):
        if word not in STOPWORDS:
            words.append(word)

common = Counter(words).most_common(25)
for word, count in common:
    print(f"{word}: {count}")

print("\n=== CONTENT TYPES THAT GO VIRAL ===")
df["has_question"] = df["title"].str.contains("\?", na=False)
df["has_vs"] = df["title"].str.lower().str.contains(" vs ", na=False)
df["has_tip"] = df["title"].str.lower().str.contains("tip|trick|hack|how|guide|tutorial", na=False)
df["has_code"] = df["title"].str.lower().str.contains("code|coding|programm|script|api", na=False)
df["has_comparison"] = df["title"].str.lower().str.contains("better|worse|vs|compared|switch", na=False)

print("Question posts avg score:", df[df["has_question"]]["score"].mean().round(1))
print("Tip/hack posts avg score:", df[df["has_tip"]]["score"].mean().round(1))
print("Code posts avg score:", df[df["has_code"]]["score"].mean().round(1))
print("Comparison posts avg score:", df[df["has_comparison"]]["score"].mean().round(1))
print("VS posts avg score:", df[df["has_vs"]]["score"].mean().round(1))
    
