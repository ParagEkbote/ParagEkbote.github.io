import os
import requests
import subprocess
import time
from pathlib import Path

# -------------------------------------------------------
# AUTH & HEADERS
# -------------------------------------------------------

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise RuntimeError("GITHUB_TOKEN is required (GraphQL does not work without it)")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
}

GRAPHQL_URL = "https://api.github.com/graphql"
REST_URL = "https://api.github.com"

# -------------------------------------------------------
# UTILS
# -------------------------------------------------------

def safe_json(resp: requests.Response):
    if resp.status_code != 200:
        raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text}")

    if not resp.text or not resp.text.strip():
        raise RuntimeError("Empty response from GitHub API")

    try:
        return resp.json()
    except ValueError:
        raise RuntimeError(f"Non-JSON response:\n{resp.text}")


def get_repo_root() -> Path:
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
        cwd = Path.cwd()
        print(f"⚠️ Could not determine git root. Falling back to: {cwd}")
        return cwd

# -------------------------------------------------------
# GRAPHQL: MERGED EXTERNAL PRs
# -------------------------------------------------------

def fetch_merged_external_prs(author="ParagEkbote"):
    all_prs = []
    cursor = None

    while True:
        query = f"""
        {{
          search(
            query: "author:{author} is:pr is:merged",
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

        resp = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query})
        data = safe_json(resp)

        if "errors" in data:
            raise RuntimeError(f"GraphQL query error: {data['errors']}")

        search = data.get("data", {}).get("search")
        if not search:
            raise RuntimeError(f"Malformed GraphQL response: {data}")

        all_prs.extend(search["nodes"])

        if not search["pageInfo"]["hasNextPage"]:
            break

        cursor = search["pageInfo"]["endCursor"]

    # Filter out personal repos
    return [
        pr for pr in all_prs
        if not pr["repository"]["nameWithOwner"].startswith(f"{author}/")
    ]

# -------------------------------------------------------
# REST: PYTORCH PRs
# -------------------------------------------------------

def fetch_pytorch_prs():
    url = "https://api.github.com/search/issues"
    params = {
        # DO NOT CHANGE — PyTorch uses a specific labeling workflow
        "q": "repo:pytorch/pytorch author:ParagEkbote is:pr is:closed label:Merged"
    }

    resp = requests.get(url, headers=HEADERS, params=params)

    if resp.status_code != 200:
        raise RuntimeError(
            f"REST API Error {resp.status_code}: {resp.text}"
        )

    if not resp.text or not resp.text.strip():
        raise RuntimeError("Empty response from GitHub REST search API")

    try:
        data = resp.json()
    except ValueError:
        raise RuntimeError(
            f"Non-JSON response from GitHub REST API:\n{resp.text}"
        )

    items = data.get("items", [])
    if not isinstance(items, list):
        raise RuntimeError(f"Malformed REST search payload: {data}")

    return [
        {
            "title": pr["title"],
            "url": pr["html_url"],
            "repository": {"nameWithOwner": "pytorch/pytorch"},
        }
        for pr in items
    ]

# -------------------------------------------------------
# STARS (RATE-LIMIT SAFE)
# -------------------------------------------------------

def fetch_repo_stars(repo_name):
    resp = requests.get(f"{REST_URL}/repos/{repo_name}", headers=HEADERS)

    if resp.status_code == 200:
        return safe_json(resp).get("stargazers_count", 0)

    print(f"⚠️ Could not fetch stars for {repo_name}: {resp.status_code}")
    return 0


def calculate_star_stats(prs):
    unique_repos = sorted({pr["repository"]["nameWithOwner"] for pr in prs})
    repo_stars = {}

    print(f"⭐ Fetching star counts for {len(unique_repos)} repositories...")
    for repo in unique_repos:
        stars = fetch_repo_stars(repo)
        repo_stars[repo] = stars
        print(f"   {repo}: {stars:,} stars")
        time.sleep(0.2)  # prevent secondary rate limit

    return {
        "total_stars": sum(repo_stars.values()),
        "repo_stars": repo_stars,
    }

# -------------------------------------------------------
# MARKDOWN OUTPUT
# -------------------------------------------------------

def write_markdown(prs, star_stats, filename="contributions.md"):
    repo_root = get_repo_root()
    out_path = repo_root / filename

    total_prs = len(prs)
    unique_repos = len({pr["repository"]["nameWithOwner"] for pr in prs})

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# 💼 External Open-Source Contributions\n\n")
        f.write(
            "Merged pull requests contributed by "
            "[ParagEkbote](https://github.com/ParagEkbote) "
            "to external open-source projects.\n\n"
        )

        f.write("---\n\n")
        f.write(f"**Total merged PRs:** {total_prs}\n\n")
        f.write(f"**Unique repositories:** {unique_repos}\n\n")
        f.write(f"**Combined repository stars:** {star_stats['total_stars']:,} ⭐\n\n")

        f.write("![Open Source Contributions](./src/assets/oss_hero_img.webp)\n\n")

        for idx, pr in enumerate(prs, start=1):
            repo = pr.get("repository", {}).get("nameWithOwner", "unknown")
            f.write(f"{idx}. [{pr['title']}]({pr['url']}) — `{repo}`\n")

    print(f"📝 Wrote contributions file to: {out_path}")

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

if __name__ == "__main__":
    print("📥 Fetching merged external PRs...")
    merged_external = fetch_merged_external_prs()

    print("📥 Fetching PyTorch PRs...")
    pytorch_prs = fetch_pytorch_prs()

    # Deduplicate by URL
    combined = {pr["url"]: pr for pr in merged_external + pytorch_prs}.values()
    combined = list(combined)

    print(f"📊 Total merged external PRs: {len(combined)}")

    star_stats = calculate_star_stats(combined)
    print(f"⭐ Total stars across projects: {star_stats['total_stars']:,}")

    write_markdown(combined, star_stats)
    print("✅ Done!")
