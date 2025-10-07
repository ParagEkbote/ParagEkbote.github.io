import os
import requests
import subprocess
from pathlib import Path

# 🔐 Read token from environment variable
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# 🔍 GraphQL query for merged PRs authored by you
GRAPHQL_QUERY = """
{
  search(query: "author:ParagEkbote is:pr is:merged", type: ISSUE, first: 120) {
    nodes {
      ... on PullRequest {
        title
        url
        repository {
          nameWithOwner
        }
      }
    }
  }
}
"""

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


def write_markdown(prs, filename="contributions.md"):
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
        f.write("These are merged pull requests by [ParagEkbote](https://github.com/ParagEkbote) to projects **outside** of his own repositories.\n\n")
        f.write(f"**Total merged PRs:** {total_prs}\n\n")
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

    print(f"📝 Writing {total_prs} PRs to contributions.md at repo root...")
    write_markdown(combined)
    print("✅ Done!")
