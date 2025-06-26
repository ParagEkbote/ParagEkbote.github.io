import os
import requests

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
  search(query: "author:ParagEkbote is:pr is:merged", type: ISSUE, first: 100) {
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

def fetch_merged_external_prs():
    url = "https://api.github.com/graphql"
    resp = requests.post(url, headers=HEADERS, json={"query": GRAPHQL_QUERY})
    if resp.status_code != 200:
        raise Exception(f"GraphQL API Error: {resp.status_code} - {resp.text}")
    data = resp.json()
    all_prs = data["data"]["search"]["nodes"]
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
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 💼 External Contributions\n\n")
        f.write("These are merged pull requests by [ParagEkbote](https://github.com/ParagEkbote) to projects **outside** of his own repositories.\n\n")
        for pr in prs:
            repo = pr["repository"]["nameWithOwner"]
            f.write(f"- [{pr['title']}]({pr['url']}) — `{repo}`\n")

if __name__ == "__main__":
    print("📥 Fetching merged external PRs...")
    merged_external = fetch_merged_external_prs()

    print("📥 Fetching PyTorch labeled PRs...")
    pytorch_prs = fetch_pytorch_labeled_prs()

    # Combine and deduplicate by URL
    all_prs = {pr["url"]: pr for pr in merged_external + pytorch_prs}
    combined = list(all_prs.values())

    print(f"📝 Writing {len(combined)} PRs to contributions.md...")
    write_markdown(combined)
    print("✅ Done!")
