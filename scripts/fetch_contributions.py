import os
import requests
import subprocess
from pathlib import Path
from statistics import median

# 🔐 Read token from environment variable
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

def get_repo_root() -> Path:
    """
    Return the git repository root as a Path if available.
    Falls back to current working directory if not in a git repo or git isn't available.
    """
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return Path(root)
    except Exception:
        # Not a git repo or git not installed; fallback to cwd
        cwd = Path.cwd()
        print(f"⚠️ Could not determine git root. Falling back to current directory: {cwd}")
        return cwd

def fetch_merged_external_prs():
    url = "https://api.github.com/graphql"
    all_prs = []
    cursor = None

    while True:
        query = f"""
        {{
          search(query: "author:ParagEkbote is:pr is:merged", type: ISSUE, first: 100{f', after: "{cursor}"' if cursor else ""}) {{
            pageInfo {{
              hasNextPage
              endCursor
            }}
            nodes {{
              ... on PullRequest {{
                title
                url
                repository {{
                  nameWithOwner
                }}
              }}
            }}
          }}
        }}
        """
        resp = requests.post(url, headers=HEADERS, json={"query": query})
        if resp.status_code != 200:
            raise Exception(f"GraphQL API Error: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        if "errors" in data:
            raise Exception(f"GraphQL Query Error: {data['errors']}")

        search = data["data"]["search"]
        all_prs.extend(search["nodes"])

        if not search["pageInfo"]["hasNextPage"]:
            break

        cursor = search["pageInfo"]["endCursor"]

    # Filter out your own repos
    return [
        pr for pr in all_prs
        if not pr["repository"]["nameWithOwner"].startswith("ParagEkbote/")
    ]


def fetch_pytorch_labeled_prs():
    url = "https://api.github.com/search/issues"
    params = {
        "q": "repo:pytorch/pytorch author:ParagEkbote is:pr is:closed label:Merged"
    }
    resp = requests.get(url, headers=HEADERS, params=params)
    if resp.status_code != 200:
        raise Exception(f"REST API Error: {resp.status_code} - {resp.text}")
    items = resp.json().get("items", [])
    return [
        {
            "title": pr["title"],
            "url": pr["html_url"],
            "repository": {"nameWithOwner": "pytorch/pytorch"}
        }
        for pr in items
    ]


def fetch_repo_stars(repo_name):
    """
    Fetch star count for a given repository.
    """
    url = f"https://api.github.com/repos/{repo_name}"
    try:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            return resp.json().get("stargazers_count", 0)
        else:
            print(f"⚠️ Could not fetch stars for {repo_name}: {resp.status_code}")
            return 0
    except Exception as e:
        print(f"⚠️ Error fetching stars for {repo_name}: {e}")
        return 0


def calculate_star_stats(prs):
    """
    Calculate star statistics for contributed repositories.
    Returns dict with total_stars, avg_stars, median_stars, and repo_stars mapping.
    """
    unique_repos = set(pr["repository"]["nameWithOwner"] for pr in prs)
    repo_stars = {}
    
    print(f"⭐ Fetching star counts for {len(unique_repos)} repositories...")
    for repo in unique_repos:
        stars = fetch_repo_stars(repo)
        repo_stars[repo] = stars
        print(f"   {repo}: {stars:,} stars")
    
    star_counts = list(repo_stars.values())
    total_stars = sum(star_counts)
    avg_stars = total_stars / len(star_counts) if star_counts else 0
    median_stars = median(star_counts) if star_counts else 0
    
    return {
        "total_stars": total_stars,
        "avg_stars": avg_stars,
        "median_stars": median_stars,
        "repo_stars": repo_stars
    }


def write_markdown(prs, star_stats, filename="contributions.md"):
    """
    Writes contributions markdown file to the git repo root (or cwd if git root not found).
    """
    repo_root = get_repo_root()
    out_path = repo_root / filename

    # Calculate totals
    total_prs = len(prs)
    unique_repos = len(set(pr["repository"]["nameWithOwner"] for pr in prs))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# 💼 External Contributions\n\n")
        f.write("Below are the merged pull requests, contributed by [ParagEkbote](https://github.com/ParagEkbote) to open-source projects outside of his own repos.\n\n")
        
        f.write(f"**Total merged PRs:** {total_prs}\n\n")
        # Add star statistics
        f.write(f"**Combined repo stars:** {star_stats['total_stars']:,} ⭐\n\n")
        f.write(f"**Average per repo:** {star_stats['avg_stars']:,.0f} ⭐\n\n")
        f.write(f"**Unique repositories contributed to:** {unique_repos}\n\n")        
        
        f.write("![Open Source Contributions](./src/assets/oss_img.webp)\n\n")
        
        for idx, pr in enumerate(prs, start=1):
            repo = pr["repository"]["nameWithOwner"]
            f.write(f"{idx}. [{pr['title']}]({pr['url']}) — `{repo}`\n")

    print(f"📝 Wrote contributions file to: {out_path}")


if __name__ == "__main__":
    print("📥 Fetching merged external PRs...")
    merged_external = fetch_merged_external_prs()

    print("📥 Fetching PyTorch labeled PRs...")
    pytorch_prs = fetch_pytorch_labeled_prs()

    # Combine and deduplicate by URL
    all_prs = {pr["url"]: pr for pr in merged_external + pytorch_prs}
    combined = list(all_prs.values())

    # Print summary before writing
    total_prs = len(combined)
    unique_repos = len(set(pr["repository"]["nameWithOwner"] for pr in combined))
    print(f"📊 Total merged external PRs: {total_prs}")
    print(f"📁 Unique repositories contributed to: {unique_repos}")

    # Calculate star statistics
    star_stats = calculate_star_stats(combined)
    print(f"⭐ Total stars across projects: {star_stats['total_stars']:,}")
    print(f"⭐ Average stars per repo: {star_stats['avg_stars']:,.0f}")
    print(f"📝 Writing {total_prs} PRs to contributions.md at repo root...")
    write_markdown(combined, star_stats)
    print("✅ Done!")