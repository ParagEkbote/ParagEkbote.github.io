import requests
from bs4 import BeautifulSoup
import time
import schedule

# Paper title(s) to track
PAPER_TITLES = [
    "The Core of Modern AI Models:A Comprehensive Review on Encoder-Decoder Transformer"
]

# IEEE Xplore search URL template
SEARCH_URL = "https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText={}"

def check_papers():
    print(f"\nChecking IEEE Xplore at {time.ctime()}...\n")

    for title in PAPER_TITLES:
        query = title.replace(" ", "+")
        url = SEARCH_URL.format(query)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to fetch results for: {title}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # IEEE Xplore search results are rendered with JS, but titles appear in <title> and meta
        # For basic presence check, use the <title> tag
        page_title = soup.find("title").text.strip()

        if "Search Results" in page_title:
            print(f"🔍 '{title}' not yet found.")
        else:
            print(f"✅ '{title}' might be available! Check manually: {url}")

# Schedule the job daily at 9 AM
schedule.every().day.at("09:00").do(check_papers)

if __name__ == "__main__":
    check_papers()  # Run immediately once
    while True:
        schedule.run_pending()
        time.sleep(60)
