import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

BASE_URL = "https://www.adgm.com"
visited = set()
data = []

def crawl(url, depth=1):
    if url in visited or not url.startswith(BASE_URL) or depth > 2:
        return
    visited.add(url)
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=' ', strip=True)
        data.append({"url": url, "title": soup.title.string if soup.title else "", "content": text[:3000]})
        for link in soup.find_all("a", href=True):
            crawl(urljoin(BASE_URL, link["href"]), depth + 1)
    except:
        pass

crawl(BASE_URL)

# Save to a JSON file
with open("adgm_pages.json", "w", encoding="utf-8") as f:
    for i, d in enumerate(data):
        d["id"] = str(i + 1)
    json.dump(data, f, indent=2)
