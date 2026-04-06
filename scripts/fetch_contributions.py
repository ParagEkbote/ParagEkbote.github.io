import os
import requests
import subprocess
import time
import urllib.parse
from pathlib import Path
from collections import Counter
import logging
import sys
import argparse

# -------------------------------------------------------
# LOGGING SETUP
# -------------------------------------------------------

def setup_logger():
    logger = logging.getLogger("oss_tracker")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = setup_logger()

# -------------------------------------------------------
# AUTH & HEADERS
# -------------------------------------------------------

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN is required")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
}

GRAPHQL_URL = "https://api.github.com/graphql"
REST_URL    = "https://api.github.com"

CONTRIBUTIONS_URL = (
    "https://raw.githubusercontent.com/"
    "ParagEkbote/ParagEkbote.github.io/main/contributions.md"
)

# -------------------------------------------------------
# UTILS
# -------------------------------------------------------

def safe_json(resp: requests.Response):
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")
    return resp.json()


def get_repo_root() -> Path:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return Path(root)
    except Exception:
        return Path.cwd()

# -------------------------------------------------------
# GRAPHQL: MERGED EXTERNAL PRs
# -------------------------------------------------------

def fetch_merged_external_prs(author="ParagEkbote"):
    logger.info("Fetching merged external PRs")

    all_prs = []
    cursor  = None

    while True:
        after_clause = f', after: "{cursor}"' if cursor else ""
        query = (
            f'{{ search(query: "author:{author} is:pr is:merged", '
            f'type: ISSUE, first: 100{after_clause}) '
            f'{{ pageInfo {{ hasNextPage endCursor }} '
            f'nodes {{ ... on PullRequest {{ title url repository {{ nameWithOwner }} }} }} }} }}'
        )

        resp = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query})
        data = safe_json(resp)

        search = data["data"]["search"]
        all_prs.extend(search["nodes"])
        logger.debug(f"Fetched {len(search['nodes'])} PRs (batch)")

        if not search["pageInfo"]["hasNextPage"]:
            break

        cursor = search["pageInfo"]["endCursor"]

    return [
        pr for pr in all_prs
        if not pr["repository"]["nameWithOwner"].startswith(f"{author}/")
    ]

# -------------------------------------------------------
# REST: PYTORCH PRs
# -------------------------------------------------------

def fetch_pytorch_prs():
    logger.info("Fetching PyTorch PRs")

    url    = "https://api.github.com/search/issues"
    params = {
        "q": "repo:pytorch/pytorch author:ParagEkbote is:pr is:closed label:Merged"
    }

    resp = requests.get(url, headers=HEADERS, params=params)
    data = resp.json()

    return [
        {
            "title": pr["title"],
            "url":   pr["html_url"],
            "repository": {"nameWithOwner": "pytorch/pytorch"},
        }
        for pr in data.get("items", [])
    ]

# -------------------------------------------------------
# REPO METADATA
# -------------------------------------------------------

def fetch_repo_metadata(repo_name):
    resp = requests.get(f"{REST_URL}/repos/{repo_name}", headers=HEADERS)

    if resp.status_code == 200:
        data = safe_json(resp)
        return {
            "stars":       data.get("stargazers_count", 0),
            "forks":       data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
        }

    logger.warning(f"Failed to fetch metadata for {repo_name}")
    return {"stars": 0, "forks": 0, "open_issues": 0}


def calculate_repo_stats(prs):
    unique_repos = sorted({pr["repository"]["nameWithOwner"] for pr in prs})
    repo_stats   = {}

    logger.info(f"Fetching metadata for {len(unique_repos)} repositories")

    for repo in unique_repos:
        repo_stats[repo] = fetch_repo_metadata(repo)
        logger.debug(f"{repo} → ⭐ {repo_stats[repo]['stars']}")
        time.sleep(0.2)

    return {
        "total_stars": sum(m["stars"] for m in repo_stats.values()),
        "repo_stats":  repo_stats,
    }

# -------------------------------------------------------
# PR ENRICHMENT
# -------------------------------------------------------

def enrich_prs_with_efficiency(prs, repo_stats):
    logger.info("Enriching PRs with efficiency metrics")

    for pr in prs:
        repo    = pr["repository"]["nameWithOwner"]
        api_url = (
            pr["url"]
            .replace("https://github.com/", "https://api.github.com/repos/")
            .replace("/pull/", "/pulls/")
        )

        resp = requests.get(api_url, headers=HEADERS)

        if resp.status_code == 200:
            data      = resp.json()
            additions = data.get("additions", 0)
            deletions = data.get("deletions", 0)
        else:
            additions, deletions = 0, 0
            logger.warning(f"Failed PR stats fetch: {pr['url']}")

        pr_size    = additions + deletions
        stars      = repo_stats.get(repo, {}).get("stars", 0)
        efficiency = stars / pr_size if pr_size > 0 else 0

        pr["stats"] = {"size": pr_size, "efficiency": efficiency}
        logger.debug(f"{repo} | size={pr_size} | efficiency={efficiency:.4f}")
        time.sleep(0.1)

    return prs


def compute_repo_contribution_stats(prs):
    logger.info("Computing repository contribution stats")
    return {
        "repo_counts": Counter(pr["repository"]["nameWithOwner"] for pr in prs)
    }

# -------------------------------------------------------
# CHAT PROMPT GENERATION
# -------------------------------------------------------

def generate_chat_prompt(pr_count: int, repo_count: int, top_repos: list) -> str:
    top_repos_str = "\n".join(f"  - {r}" for r in top_repos[:5])

    return f"""You are an expert open-source contributor and reviewer, analyzing ParagEkbote's contribution profile.

Primary source of truth:
{CONTRIBUTIONS_URL}

Context:
- Total merged PRs: {pr_count}
- Unique repositories: {repo_count}
- Top repositories by stars:
{top_repos_str}

Instructions:
1. Read and internalize the contributions page.
2. Provide a concise but structured summary including:
   - Overall contribution profile (breadth vs depth)
   - Most impactful repositories
   - Patterns in contributions (e.g., repeated repos, types of changes)
   - Signals of specialization or strength

3. Then transition into an interactive Q&A mode.

You may guide the reader by suggesting questions such as:

- What does this contribution profile suggest about the contributor’s engineering strengths?
- Does the contribution profile indicate depth in specific projects or breadth across ecosystems?
- What patterns can be observed in contribution behavior (e.g., repeated contributions vs one-off contributions)?
- Which repositories represent the highest impact contributions, and why?
- What types of contributions dominate (e.g., bug fixes, features, infrastructure), and what does that imply?
- Which contributions appear to have the highest leverage relative to their size?

4. Be analytical, not generic. Prefer insight over description.

5. Stay grounded strictly in the data from the page. If a question cannot be answered, explicitly state that.

End your response by inviting deeper questions about specific repositories, contribution patterns, or technical impact.
""".strip()

# -------------------------------------------------------
# BADGE URL BUILDERS
# -------------------------------------------------------

# Badge styles  (shields.io for-the-badge)
_BADGE_STYLE = "for-the-badge"

CHAT_PROVIDERS = [
    {
        "name":       "Claude",
        "url_prefix": "https://claude.ai/new?q=",
        "badge_label": "Ask%20Claude",
        "badge_msg":   "Chat%20about%20this%20page",
        "badge_color": "f4a261",
        "logo":        "anthropic",
    },
    {
        "name":       "ChatGPT",
        "url_prefix": "https://chatgpt.com/?q=",
        "badge_label": "Ask%20ChatGPT",
        "badge_msg":   "Chat%20about%20this%20page",
        "badge_color": "10a37f",
        "logo":        "openai",
    },
    {
        "name":       "HuggingChat",
        "url_prefix": "https://huggingface.co/chat?q=",
        "badge_label": "Ask%20HuggingChat",
        "badge_msg":   "Chat%20about%20this%20page",
        "badge_color": "ff9d00",
        "logo":        "huggingface",
    },
]


def build_chat_badge(provider: dict, encoded_prompt: str) -> str:
    """Return a markdown badge that opens the provider with the prompt pre-filled."""
    badge_url = (
        f"https://img.shields.io/badge/"
        f"{provider['badge_label']}-{provider['badge_msg']}"
        f"-{provider['badge_color']}"
        f"?style={_BADGE_STYLE}&logo={provider['logo']}"
    )
    chat_url = f"{provider['url_prefix']}{encoded_prompt}"
    return f"[![{provider['name']}]({badge_url})]({chat_url})"


def build_all_chat_badges(prs, repo_stats) -> str:
    """
    Generate the prompt once, URL-encode it once, then produce
    one badge per provider — all pointing to the same prompt.
    """
    top_repos = [
        repo for repo, _ in
        sorted(
            repo_stats["repo_stats"].items(),
            key=lambda x: x[1]["stars"],
            reverse=True,
        )
    ]

    prompt  = generate_chat_prompt(
        pr_count=len(prs),
        repo_count=len(repo_stats["repo_stats"]),
        top_repos=top_repos,
    )
    encoded = urllib.parse.quote(prompt, safe="")

    badges = [build_chat_badge(p, encoded) for p in CHAT_PROVIDERS]
    return " ".join(badges)   # single line, space-separated


# -------------------------------------------------------
# MARKDOWN OUTPUT
# -------------------------------------------------------

def write_markdown(prs, repo_stats, contrib_stats,
                   filename="contributions.md",
                   include_chat_prompt=True):
    logger.info("Writing markdown output")

    repo_root = get_repo_root()
    out_path  = repo_root / filename

    # Build chat badges once (reused in header)
    chat_badges = build_all_chat_badges(prs, repo_stats) if include_chat_prompt else ""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# 💼 External Open-Source Contributions\n\n")

        # ---- existing static badges ----
        f.write(
            f"[![View Raw Markdown](https://img.shields.io/badge/View-Raw%20Markdown"
            f"-blue?style=for-the-badge)]({CONTRIBUTIONS_URL})\n\n"
        )

        # ---- chat badges injected right after the static ones ----
        if chat_badges:
            f.write(f"{chat_badges}\n\n")

        f.write("---\n\n")

        f.write(f"**Total merged PRs:** {len(prs)}\n\n")
        f.write(f"**Unique repositories:** {len(repo_stats['repo_stats'])}\n\n")
        f.write(f"**Combined repository stars:** {repo_stats['total_stars']:,} ⭐\n\n")

        f.write("![Open Source Contributions](./src/assets/oss_hero_img.webp)\n\n")

        for idx, pr in enumerate(prs, start=1):
            repo = pr["repository"]["nameWithOwner"]
            f.write(f"{idx}. [{pr['title']}]({pr['url']}) — `{repo}`\n")

        f.write("\n## 📊 Contribution Insights\n\n")

        f.write("### 🔁 PRs per Repository\n")
        for repo, count in contrib_stats["repo_counts"].most_common():
            f.write(f"- `{repo}`: {count} PRs\n")

        f.write("\n### 📦 Repository Activity (sorted by stars)\n")
        sorted_repos = sorted(
            repo_stats["repo_stats"].items(),
            key=lambda x: x[1]["stars"],
            reverse=True,
        )
        for repo, meta in sorted_repos:
            f.write(
                f"- `{repo}` → ⭐ {meta['stars']:,}, "
                f"forks {meta['forks']:,}, "
                f"open issues {meta['open_issues']:,}\n"
            )

    logger.info(f"Output written to: {out_path}")
    print(f"📝 Wrote contributions file to: {out_path}")

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    logger.setLevel(getattr(logging, args.log_level))
    logger.info("Starting OSS contribution aggregation")

    merged_external = fetch_merged_external_prs()
    pytorch_prs     = fetch_pytorch_prs()

    logger.info("Merging PR datasets")
    combined = {pr["url"]: pr for pr in merged_external + pytorch_prs}.values()
    combined = sorted(
        combined,
        key=lambda pr: (
            pr["repository"]["nameWithOwner"].lower(),
            pr["title"].lower(),
        ),
    )

    repo_stats    = calculate_repo_stats(combined)
    combined      = enrich_prs_with_efficiency(combined, repo_stats["repo_stats"])
    contrib_stats = compute_repo_contribution_stats(combined)

    write_markdown(combined, repo_stats, contrib_stats)

    logger.info("Done")
    print("✅ Done!")