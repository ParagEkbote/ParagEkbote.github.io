import requests
import json
import csv
from datetime import datetime
from pathlib import Path

# List of paper titles to search
PAPER_TITLES = [
    "The Core of Modern AI Models:A Comprehensive Review on Encoder-Decoder Transformer"
]

CSV_FILE = Path("ieee_paper_search_results.csv")

def search_ieee(title):
    url = "https://ieeexplore.ieee.org/rest/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://ieeexplore.ieee.org",
        "Referer": "https://ieeexplore.ieee.org/search/searchresult.jsp",
        "Content-Type": "application/json",
        "DNT": "1",
        "Connection": "keep-alive",
    }

    payload = {
        "queryText": title,
        "highlight": True,
        "returnType": "SEARCH",
        "returnFacets": ["ALL"]
    }

    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        if r.status_code != 200:
            print(f"Error {r.status_code} for '{title}'")
            return {"title": title, "found": False}

        data = r.json()
        records = data.get("records", [])
        if not records:
            print(f"No results found for '{title}'")
            return {"title": title, "found": False}

        # Take the first match
        record = records[0]
        result = {
            "title": title,
            "found": True,
            "matched_title": record.get("articleTitle"),
            "doc_id": record.get("articleNumber"),
            "doi": record.get("doi"),
            "link": f"https://ieeexplore.ieee.org/document/{record.get('articleNumber')}"
        }
        print(f"Found '{title}': {result['link']}")
        return result

    except Exception as e:
        print(f"Exception for '{title}': {e}")
        return {"title": title, "found": False}

def save_results_to_csv(results):
    file_exists = CSV_FILE.exists()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "title", "found", "matched_title", "doc_id", "doi", "link"])
        if not file_exists:
            writer.writeheader()
        for res in results:
            row = {"date": datetime.now().isoformat(), **res}
            writer.writerow(row)

if __name__ == "__main__":
    results = [search_ieee(title) for title in PAPER_TITLES]
    save_results_to_csv(results)
