import requests

url = "https://www.adgm.com/sitemap.xml"  # ✅ Correct XML sitemap
response = requests.get(url)

if response.status_code == 200:
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("sitemap.xml downloaded successfully")
else:
    print("Failed to download sitemap:", response.status_code)
