import xml.etree.ElementTree as ET

# Parse downloaded XML
tree = ET.parse("sitemap.xml")
root = tree.getroot()

# Extract <loc> tags inside <url> entries
urls = []
for url in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
    loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
    urls.append(loc)

# Save to a file
with open("adgm_urls.txt", "w") as f:
    for u in urls:
        f.write(u + "\n")

print(f"{len(urls)} URLs saved to adgm_urls.txt")
