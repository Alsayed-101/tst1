import os
import json
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Read Azure Search details from environment variables
endpoint = os.getenv("SEARCH_ENDPOINT")
key = os.getenv("SEARCH_KEY")
index_name = os.getenv("SEARCH_INDEX")

# Initialize Azure Search client
client = SearchClient(
    endpoint=endpoint,
    index_name=index_name,
    credential=AzureKeyCredential(key)
)

# Load the ADGM page content
with open("adgm_pages.json", "r", encoding="utf-8") as f:
    documents = json.load(f)

# Upload to Azure Search
result = client.upload_documents(documents=documents)
print(f"✅ Uploaded {len(documents)} documents to index '{index_name}'")
