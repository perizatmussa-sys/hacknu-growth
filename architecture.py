import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(1, 1, figsize=(10, 14))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')

def draw_box(ax, x, y, width, height, text, color):
    box = mpatches.FancyBboxPatch(
        (x - width/2, y - height/2),
        width, height,
        boxstyle="round,pad=0.1",
        facecolor=color,
        edgecolor='white',
        linewidth=2
    )
    ax.add_patch(box)
    ax.text(x, y, text,
        ha='center', va='center',
        fontsize=9, fontweight='bold',
        color='white', wrap=True,
        multialignment='center'
    )

def draw_arrow(ax, x, y1, y2):
    ax.annotate('',
        xy=(x, y2 + 0.35),
        xytext=(x, y1 - 0.35),
        arrowprops=dict(
            arrowstyle='->',
            color='gray',
            lw=2
        )
    )

boxes = [
    (5, 13, 6, 0.6, "Reddit Public JSON API\n(r/ClaudeAI, r/ChatGPT, r/LocalLLaMA, r/artificial)", "#185FA5"),
    (5, 11.5, 6, 0.6, "reddit_scraper2.py\n(requests library — no API key needed)", "#1D9E75"),
    (5, 10, 6, 0.6, "reddit_data.csv\n(557 posts — id, title, score, subreddit, date)", "#5F5E5A"),
    (5, 8.5, 6, 0.6, "analysis.py\n(keywords, content types, subreddit scores)", "#534AB7"),
    (5, 7, 6, 0.6, "charts.py\n(4 visualizations saved as charts.png)", "#993C1D"),
    (5, 5.5, 6, 0.6, "counter_playbook.md\n(data-backed growth strategy)", "#3B6D11"),
    (5, 4, 6, 0.6, "Monday Morning Report\n(findings + charts + recommendations)", "#185FA5"),
    (5, 2.5, 6, 0.6, "Cron Job — runs every Sunday 11pm\n(fully automated, no human needed)", "#A32D2D"),
]

for (x, y, w, h, text, color) in boxes:
    draw_box(ax, x, y, w, h, text, color)

arrow_positions = [13, 11.5, 10, 8.5, 7, 5.5, 4]
for i in range(len(arrow_positions) - 1):
    draw_arrow(ax, 5, arrow_positions[i], arrow_positions[i+1])

ax.text(5, 13.7,
    "Claude Viral Growth Machine — Architecture",
    ha='center', va='center',
    fontsize=13, fontweight='bold',
    color='#2C2C2A'
)

labels = [
    (8.5, 12.75, "DATA SOURCE", "#185FA5"),
    (8.5, 11.25, "SCRAPER", "#1D9E75"),
    (8.5, 9.75, "STORAGE", "#5F5E5A"),
    (8.5, 8.25, "ANALYSIS", "#534AB7"),
    (8.5, 6.75, "VISUALISATION", "#993C1D"),
    (8.5, 5.25, "STRATEGY", "#3B6D11"),
    (8.5, 3.75, "OUTPUT", "#185FA5"),
    (8.5, 2.25, "AUTOMATION", "#A32D2D"),
]

for (x, y, label, color) in labels:
    ax.text(x, y, label,
        ha='center', va='center',
        fontsize=7, color=color,
        fontweight='bold'
    )

plt.tight_layout()
plt.savefig("/home/perizat/Documents/architecture.png", dpi=150, bbox_inches='tight')
print("Architecture diagram saved to architecture.png")
