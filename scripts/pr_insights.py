import os
import json
import subprocess
import requests
from datetime import datetime
from statistics import mean, median, stdev
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
                  description
                  stargazerCount
                  primaryLanguage {{
                    name
                  }}
                }}
                author {{
                  login
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
    "api": "api",
    "core": "core",
    "config": "config",
    "lib": "lib",
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


def extract_notable_prs(prs):
    """Extract notable PRs for case study examples"""
    notable = []
    
    for pr in prs:
        size = pr["additions"] + pr["deletions"]
        repo = pr["repository"]["nameWithOwner"]
        stars = pr["repository"]["stargazerCount"]
        
        # High-impact criteria
        if size > 500 or stars > 1000 or pr["changedFiles"] > 10:
            notable.append({
                "title": pr["title"],
                "url": pr["url"],
                "repo": repo,
                "size": size,
                "stars": stars,
                "files": pr["changedFiles"],
                "created": pr["createdAt"]
            })
    
    # Sort by stars and size
    notable.sort(key=lambda x: (x["stars"], x["size"]), reverse=True)
    return notable[:10]  # Top 10


def compute_pr_insights(prs):
    merge_durations = []
    review_iterations = []
    review_comments_count = []
    pr_sizes = []
    touched_files = []
    first_try_merge_flags = []
    repo_contribution_count = defaultdict(int)
    folder_counts = defaultdict(int)
    language_counts = defaultdict(int)
    
    # For case study analysis
    impact_scores = []
    monthly_merge = defaultdict(list)
    monthly_first_try = defaultdict(list)
    monthly_pr_count = defaultdict(int)
    
    # Notable contributions
    large_prs = []
    quick_merges = []

    for pr in prs:
        url = pr["url"]
        repo = pr["repository"]["nameWithOwner"]
        created = parse_time(pr["createdAt"])
        merged = parse_time(pr["mergedAt"])
        month = created.strftime("%Y-%m")

        repo_contribution_count[repo] += 1
        monthly_pr_count[month] += 1

        # Language tracking
        lang = pr["repository"].get("primaryLanguage")
        if lang:
            language_counts[lang["name"]] += 1

        # Merge time
        merge_days = (merged - created).total_seconds() / 86400
        merge_durations.append(merge_days)
        monthly_merge[month].append(merge_days)
        
        if merge_days < 1:
            quick_merges.append((pr["title"], pr["url"], merge_days))

        # PR size
        size = pr["additions"] + pr["deletions"]
        pr_sizes.append(size)
        touched_files.append(pr["changedFiles"])
        
        if size > 500:
            large_prs.append((pr["title"], pr["url"], size))

        # Impact score (stars * size weight)
        stars = pr["repository"]["stargazerCount"]
        impact = stars * (1 + size / 1000)
        impact_scores.append(impact)

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
    
    # Calculate consistency metrics
    merge_stdev = stdev(merge_durations) if len(merge_durations) > 1 else 0
    size_stdev = stdev(pr_sizes) if len(pr_sizes) > 1 else 0

    return {
        "total_prs": len(prs),
        "avg_merge_days": mean(merge_durations),
        "median_merge_days": median(merge_durations),
        "merge_stdev": merge_stdev,
        "avg_review_iterations": mean(review_iterations),
        "avg_review_comments": mean(review_comments_count),
        "avg_pr_size": mean(pr_sizes),
        "median_pr_size": median(pr_sizes),
        "max_pr_size": max(pr_sizes),
        "min_pr_size": min(pr_sizes),
        "size_stdev": size_stdev,
        "avg_files_touched": mean(touched_files),
        "first_try_merge_rate": sum(first_try_merge_flags) / len(first_try_merge_flags),
        "repeat_repos": repeat_repos,
        "total_repos": len(repo_contribution_count),
        "top_repo": top_repo,
        "top_repo_count": repo_contribution_count[top_repo],
        "contribution_summary": folder_counts,
        "language_distribution": language_counts,
        "avg_impact_score": mean(impact_scores),
        "monthly_activity": monthly_pr_count,
        "large_prs": sorted(large_prs, key=lambda x: x[2], reverse=True)[:5],
        "quick_merges": sorted(quick_merges, key=lambda x: x[2])[:5],
        "repo_contributions": dict(sorted(repo_contribution_count.items(), 
                                         key=lambda x: x[1], reverse=True)[:10])
    }


def export_case_study_markdown(insights, prs, filename="oss_case_study.md"):
    """Generate comprehensive case study markdown"""
    repo_root = get_repo_root()
    out_path = repo_root / filename
    
    notable_prs = extract_notable_prs(prs)
    
    lines = []
    
    # Header
    lines.append("# 📊 Open Source Contribution Case Study")
    lines.append("\n**Developer:** Parag Ekbote")
    lines.append(f"**Analysis Date:** {datetime.now().strftime('%B %d, %Y')}")
    lines.append(f"**Total Contributions Analyzed:** {insights['total_prs']} merged PRs\n")
    lines.append("---\n")
    
    # Executive Summary
    lines.append("## 🎯 Executive Summary\n")
    lines.append(f"This case study analyzes **{insights['total_prs']} merged pull requests** across "
                f"**{insights['total_repos']} open-source repositories**. The analysis reveals consistent "
                f"contribution patterns with a **{insights['first_try_merge_rate']*100:.1f}%** first-try merge rate "
                f"and an average merge time of **{insights['avg_merge_days']:.2f} days**.\n")
    
    # Key Highlights
    lines.append("### Key Highlights\n")
    lines.append(f"- ✅ **{insights['first_try_merge_rate']*100:.1f}%** of PRs merged without change requests")
    lines.append(f"- 🔄 Contributed to **{insights['repeat_repos']}** repositories multiple times")
    lines.append(f"- 📦 Average PR size: **{insights['avg_pr_size']:.0f} lines** (showing focused, reviewable changes)")
    lines.append(f"- ⚡ **{len(insights['quick_merges'])}** PRs merged within 24 hours")
    lines.append(f"- 🏗️ Largest contribution: **{insights['max_pr_size']:,} lines of code**\n")
    
    # Contribution Metrics
    lines.append("---\n")
    lines.append("## 📈 Contribution Metrics\n")
    
    lines.append("### Merge Performance\n")
    lines.append("| Metric | Value | Insight |")
    lines.append("|--------|-------|---------|")
    lines.append(f"| Average Merge Time | {insights['avg_merge_days']:.2f} days | "
                f"{'Fast turnaround' if insights['avg_merge_days'] < 3 else 'Standard process'} |")
    lines.append(f"| Median Merge Time | {insights['median_merge_days']:.2f} days | "
                f"Consistent with average |")
    lines.append(f"| Standard Deviation | {insights['merge_stdev']:.2f} days | "
                f"{'Low variance' if insights['merge_stdev'] < 5 else 'Varied timelines'} |")
    lines.append(f"| First-Try Merge Rate | {insights['first_try_merge_rate']*100:.1f}% | "
                f"{'Excellent' if insights['first_try_merge_rate'] > 0.7 else 'Good'} code quality |")
    
    lines.append("\n### Code Review Engagement\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Avg Review Iterations | {insights['avg_review_iterations']:.2f} |")
    lines.append(f"| Avg Review Comments | {insights['avg_review_comments']:.2f} |")
    
    lines.append("\n### PR Size & Complexity\n")
    lines.append("| Metric | Value | Context |")
    lines.append("|--------|-------|---------|")
    lines.append(f"| Average PR Size | {insights['avg_pr_size']:.0f} LoC | "
                f"{'Small, focused' if insights['avg_pr_size'] < 200 else 'Moderate scope'} |")
    lines.append(f"| Median PR Size | {insights['median_pr_size']:.0f} LoC | Typical contribution size |")
    lines.append(f"| Largest PR | {insights['max_pr_size']:,} LoC | Capability for large-scale work |")
    lines.append(f"| Smallest PR | {insights['min_pr_size']} LoC | Attention to detail |")
    lines.append(f"| Files per PR | {insights['avg_files_touched']:.2f} | "
                f"{'Focused' if insights['avg_files_touched'] < 5 else 'Cross-cutting'} changes |")
    
    # Repository Landscape
    lines.append("\n---\n")
    lines.append("## 🌐 Repository Landscape\n")
    
    lines.append(f"### Top Repositories ({len(insights['repo_contributions'])} shown)\n")
    for i, (repo, count) in enumerate(insights['repo_contributions'].items(), 1):
        lines.append(f"{i}. **[{repo}](https://github.com/{repo})** — {count} PR{'s' if count > 1 else ''}")
    
    lines.append(f"\n**Most Active Repository:** {insights['top_repo']} "
                f"({insights['top_repo_count']} contributions)\n")
    
    # Technology Stack
    lines.append("### 💻 Technology Stack\n")
    top_langs = sorted(insights['language_distribution'].items(), 
                      key=lambda x: x[1], reverse=True)[:8]
    for lang, count in top_langs:
        percentage = (count / insights['total_prs']) * 100
        lines.append(f"- **{lang}**: {count} PRs ({percentage:.1f}%)")
    
    # Contribution Areas
    lines.append("\n### 🗂️ Contribution Focus Areas\n")
    top_folders = sorted(insights['contribution_summary'].items(), 
                        key=lambda x: x[1], reverse=True)[:8]
    for folder, count in top_folders:
        lines.append(f"- **{folder.title()}**: {count} file modifications")
    
    # Notable Contributions
    lines.append("\n---\n")
    lines.append("## 🏆 Notable Contributions\n")
    
    if insights['large_prs']:
        lines.append("### Significant PRs (by size)\n")
        for i, (title, url, size) in enumerate(insights['large_prs'], 1):
            lines.append(f"{i}. [{title}]({url}) — {size:,} LoC")
    
    if insights['quick_merges']:
        lines.append("\n### Fast-Tracked Merges (< 24 hours)\n")
        for i, (title, url, hours) in enumerate(insights['quick_merges'], 1):
            lines.append(f"{i}. [{title}]({url}) — {hours*24:.1f} hours")
    
    if notable_prs:
        lines.append("\n### High-Impact Projects\n")
        lines.append("*Based on repository popularity and contribution size*\n")
        for i, pr in enumerate(notable_prs[:5], 1):
            lines.append(f"{i}. **[{pr['repo']}]({pr['url']})** "
                        f"(⭐ {pr['stars']:,}) — {pr['size']:,} LoC, {pr['files']} files")
    
    # Activity Patterns
    lines.append("\n---\n")
    lines.append("## 📅 Activity Patterns\n")
    
    if insights['monthly_activity']:
        sorted_months = sorted(insights['monthly_activity'].items())
        total_months = len(sorted_months)
        avg_per_month = insights['total_prs'] / total_months if total_months > 0 else 0
        
        lines.append(f"**Active Period:** {sorted_months[0][0]} to {sorted_months[-1][0]}")
        lines.append(f"**Average PRs per Month:** {avg_per_month:.1f}")
        lines.append(f"**Most Active Month:** {max(sorted_months, key=lambda x: x[1])[0]} "
                    f"({max(insights['monthly_activity'].values())} PRs)\n")
    
    # Insights & Patterns
    lines.append("---\n")
    lines.append("## 💡 Key Insights\n")
    
    lines.append("### Code Quality Indicators")
    lines.append(f"- High first-try merge rate ({insights['first_try_merge_rate']*100:.1f}%) suggests strong "
                "understanding of project standards")
    lines.append(f"- Average of {insights['avg_review_comments']:.1f} review comments indicates constructive "
                "collaboration")
    lines.append(f"- Consistent PR sizing (σ = {insights['size_stdev']:.0f}) shows disciplined contribution approach\n")
    
    lines.append("### Community Engagement")
    lines.append(f"- Repeat contributions to {insights['repeat_repos']} repositories demonstrates sustained engagement")
    lines.append(f"- Work spans {insights['total_repos']} different projects showing adaptability")
    lines.append(f"- Diverse technology stack ({len(insights['language_distribution'])} languages) "
                "indicates technical versatility\n")
    
    # Methodology
    lines.append("---\n")
    lines.append("## 📋 Methodology\n")
    lines.append("This case study analyzes merged pull requests using GitHub's GraphQL API. "
                "Metrics include:\n")
    lines.append("- **Merge Performance**: Time from PR creation to merge, review iterations")
    lines.append("- **Code Metrics**: Lines changed, files modified, PR complexity")
    lines.append("- **Impact Analysis**: Repository popularity, contribution scope")
    lines.append("- **Quality Indicators**: First-try merge rate, review engagement\n")
    
    lines.append("---\n")
    lines.append(f"*Generated automatically from GitHub data on {datetime.now().strftime('%Y-%m-%d')}*")
    
    # Write to project root
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    
    print(f"📄 Case study exported to: {out_path}")
    return out_path


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if __name__ == "__main__":
    print("🚀 Starting OSS Case Study Generation...\n")
    
    # Fetch data
    prs = fetch_all_merged_prs()

    # Save raw data
    with open(MERGED_PRS_JSON, "w") as f:
        json.dump(prs, f, indent=2)
    print(f"💾 Saved PR list to {MERGED_PRS_JSON}\n")

    # Compute insights
    print("🔍 Analyzing contribution patterns...")
    insights = compute_pr_insights(prs)

    # Display summary
    print("\n" + "="*50)
    print("ANALYSIS SUMMARY")
    print("="*50)
    print(f"Total PRs: {insights['total_prs']}")
    print(f"Total Repositories: {insights['total_repos']}")
    print(f"Avg Merge Time: {insights['avg_merge_days']:.2f} days")
    print(f"First-Try Merge Rate: {insights['first_try_merge_rate']*100:.1f}%")
    print(f"Most Active Repo: {insights['top_repo']}")
    print("="*50 + "\n")

    # Generate case study
    output_file = export_case_study_markdown(insights, prs)
    
    print("✅ Case study generation complete!")
    print(f"📍 File location: {output_file}")