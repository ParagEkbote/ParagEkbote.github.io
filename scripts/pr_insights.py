import os
import json
import subprocess
import requests
from datetime import datetime
from statistics import mean, median
from collections import defaultdict
from pathlib import Path


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

SEARCH_AUTHOR = "ParagEkbote"
MERGED_PRS_JSON = "merged_prs.json"


def parse_time(t):
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")

def get_repo_root() -> Path:
    """
    Return the git repository root as a Path if available.
    Falls back to current working directory if not in a git repo or git isn't available.
    """
    try:
        root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        return Path(root)
    except Exception:
        # Not a git repo or git not installed; fallback to cwd
        cwd = Path.cwd()
        print(
            f"⚠️ Could not determine git root. Falling back to current directory: {cwd}"
        )
        return cwd

def fetch_all_merged_prs():
    print("📥 Fetching merged PRs via GraphQL...")

    url = "https://api.github.com/graphql"
    cursor = None
    all_prs = []

    while True:
        query = f"""
        {{
          search(
            query: "author:{SEARCH_AUTHOR} is:pr is:merged sort:created-desc",
            type: ISSUE,
            first: 100
            {f', after: "{cursor}"' if cursor else ""}
          ) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}
            nodes {{
              ... on PullRequest {{
                url
                title
                createdAt
                mergedAt
                additions
                deletions
                changedFiles
                repository {{
                  nameWithOwner
                }}
              }}
            }}
          }}
        }}
        """

        resp = requests.post(url, headers=HEADERS, json={"query": query})
        data = resp.json()

        if "errors" in data:
            raise Exception(data["errors"])

        search = data["data"]["search"]
        all_prs.extend(search["nodes"])

        if not search["pageInfo"]["hasNextPage"]:
            break

        cursor = search["pageInfo"]["endCursor"]

    external = [
        pr for pr in all_prs
        if not pr["repository"]["nameWithOwner"].startswith(f"{SEARCH_AUTHOR}/")
    ]

    print(f"✔️ Found {len(external)} merged external PRs.")
    return external


def fetch_pr_reviews_comments_files(pr_url):
    parts = pr_url.split("/")
    owner, repo, number = parts[3], parts[4], parts[-1]

    base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"

    pr_reviews = requests.get(base + "/reviews", headers=HEADERS).json()
    pr_comments = requests.get(base + "/comments", headers=HEADERS).json()
    pr_files = requests.get(base + "/files", headers=HEADERS).json()

    return pr_reviews, pr_comments, pr_files

FOLDER_MAP = {
    "docs": "docs",
    "documentation": "docs",
    "examples": "examples",
    "example": "examples",
    "tests": "tests",
    "test": "tests",
    "models": "models",
    "model": "models",
    "utils": "utils",
    "ops": "ops",
    "src": "src",
}

def categorize_file(path):
    parts = path.split("/")
    if len(parts) == 0:
        return "other"

    first = parts[0].lower()
    for key, label in FOLDER_MAP.items():
        if first.startswith(key):
            return label
    return "other"


def compute_pr_insights(prs):
    merge_durations = []
    review_iterations = []
    review_comments_count = []
    pr_sizes = []
    touched_files = []
    first_try_merge_flags = []
    repo_contribution_count = defaultdict(int)
    folder_counts = defaultdict(int)

    # For summarized monthly trends
    monthly_merge = defaultdict(list)
    monthly_first_try = defaultdict(list)

    for pr in prs:
        url = pr["url"]
        repo = pr["repository"]["nameWithOwner"]
        created = parse_time(pr["createdAt"])
        merged = parse_time(pr["mergedAt"])
        month = created.strftime("%Y-%m")

        repo_contribution_count[repo] += 1

        # Merge time
        merge_days = (merged - created).total_seconds() / 86400
        merge_durations.append(merge_days)
        monthly_merge[month].append(merge_days)

        # PR size
        size = pr["additions"] + pr["deletions"]
        pr_sizes.append(size)
        touched_files.append(pr["changedFiles"])

        # Reviews & comments
        reviews, comments, files = fetch_pr_reviews_comments_files(url)

        review_iterations.append(len(reviews))
        review_comments_count.append(len(comments))

        # First-try merge
        states = [r.get("state", "").lower() for r in reviews]
        ok = "changes_requested" not in states
        first_try_merge_flags.append(ok)
        monthly_first_try[month].append(int(ok))

        # Folder categories
        for f in files:
            folder = categorize_file(f["filename"])
            folder_counts[folder] += 1

    # Summaries
    repeat_repos = sum(1 for repo, cnt in repo_contribution_count.items() if cnt > 1)
    top_repo = max(repo_contribution_count, key=lambda r: repo_contribution_count[r])

    # Summarize monthly trends (not raw tables)
    merge_trend = mean([mean(v) for v in monthly_merge.values()])
    first_try_trend = mean([mean(v) for v in monthly_first_try.values()])

    return {
        "avg_merge_days": mean(merge_durations),
        "avg_review_iterations": mean(review_iterations),
        "avg_review_comments": mean(review_comments_count),
        "avg_pr_size": mean(pr_sizes),
        "median_pr_size": median(pr_sizes),
        "max_pr_size": max(pr_sizes),
        "avg_files_touched": mean(touched_files),
        "first_try_merge_rate": sum(first_try_merge_flags) / len(first_try_merge_flags),
        "repeat_repos": repeat_repos,
        "top_repo": top_repo,
        "contribution_summary": folder_counts,
        "merge_trend_summary": merge_trend,
        "first_try_trend_summary": first_try_trend,
    }


def export_insights_to_markdown(insights, filename="oss_insights.md"):
    repo_root = get_repo_root()
    out_path = repo_root / filename
    lines = []
    lines.append("# 📊 Open Source Contribution Insights\n")
    lines.append(
        "A distilled summary of **high-signal, engineering-relevant metrics** "
        "from open-source contributions by **Parag Ekbote**.\n"
    )

    # High-signal metrics
    lines.append("## 🔥 Core Contributor Metrics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|--------|")
    lines.append(f"| Average PR Merge Time | {insights['avg_merge_days']:.2f} days |")
    lines.append(f"| Review Iterations (avg) | {insights['avg_review_iterations']:.2f} |")
    lines.append(f"| Review Comments (avg) | {insights['avg_review_comments']:.2f} |")
    lines.append(f"| First-Try Merge Rate | {insights['first_try_merge_rate']*100:.1f}% |")
    lines.append(f"| Repeat Repositories | {insights['repeat_repos']} |")

    # PR size quality metrics
    lines.append("\n## 📦 PR Size & Scope\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|--------|")
    lines.append(f"| Average PR Size | {insights['avg_pr_size']:.2f} LoC |")
    lines.append(f"| Median PR Size | {insights['median_pr_size']} LoC |")
    lines.append(f"| Largest PR Shipped | {insights['max_pr_size']} LoC |")
    lines.append(f"| Files Touched per PR | {insights['avg_files_touched']:.2f} |")

    # Contribution area summary
    lines.append("\n## 🗂 Contribution Areas ( summarized )\n")
    top_folders = sorted(
        insights["contribution_summary"].items(), key=lambda x: x[1], reverse=True
    )[:5]
    for folder, count in top_folders:
        lines.append(f"- **{folder}**: {count} file touches")

    # Summarized monthly trends
    lines.append("\n## 📈 High-Level Contribution Trends\n")
    lines.append(f"- Merge times trend around **{insights['merge_trend_summary']:.1f} days**")
    lines.append(f"- First-try merges consistently around **{insights['first_try_trend_summary']*100:.1f}%**")
    lines.append(f"- Most contributed repository: **{insights['top_repo']}**\n")

    # Done
    with open(filename, "w") as f:
        f.write("\n".join(lines))

    print(f"📄 Markdown exported: {filename}")


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if __name__ == "__main__":
    prs = fetch_all_merged_prs()

    with open(MERGED_PRS_JSON, "w") as f:
        json.dump(prs, f, indent=2)
    print(f"💾 Saved PR list to {MERGED_PRS_JSON}")

    insights = compute_pr_insights(prs)

    print("\n===== OSS PR Insights =====")
    for key, val in insights.items():
        if isinstance(val, (int, float)):
            print(f"{key}: {val}")

    export_insights_to_markdown(insights)
    print("✅ Done!")
