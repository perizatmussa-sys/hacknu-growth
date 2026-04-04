# Claude Viral Growth Machine — HackNU 2026

## What This Is
Automated competitive intelligence pipeline that 
reverse-engineers Claude's viral growth playbook 
from 557 real Reddit posts across 4 subreddits.

## Key Findings
1. Code content gets 3.5x more engagement than questions
2. r/ClaudeAI and r/ChatGPT are equally dominant
3. Tip/hack posts can score 6910 — 2x any other format
4. Technical keywords dominate — code, agents, prompts

## Setup
1. Clone the repo
2. Run: source hacknu-env/bin/activate
3. Run: python3 reddit_scraper2.py
4. Run: python3 analysis.py
5. Run: python3 charts.py

## Files
- reddit_scraper2.py — collects Reddit data
- analysis.py — finds patterns in data
- charts.py — generates visualizations
- counter_playbook.md — growth strategy
- reddit_data.csv — raw dataset (557 posts)
- charts.png — all visualizations

## Assumptions and Tradeoffs
- Used public Reddit JSON endpoint instead of 
  official API due to CAPTCHA issues at venue
- Focused on Reddit only — highest signal platform
- Limited to 4 subreddits for depth over breadth
- 1 month of data — sufficient for pattern finding

## Tools Used
Python, requests, pandas, matplotlib
