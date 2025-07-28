import requests
from bs4 import BeautifulSoup
import tiktoken
import openai
import json
import time
import streamlit as st

# Load URLs from file
with open("adgm_urls.txt", "r") as f:
    urls = [line.strip() for line in f.readlines()]

def fetch_clean_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

# Initialize tokenizer (GPT-4 tokenizer)
tokenizer = tiktoken.get_encoding("cl100k_base")

def chunk_text(text, max_tokens=500):
    words = text.split()
    chunks = []
    chunk = []

    for word in words:
        chunk.append(word)
        # Check token length, if exceeded max_tokens, finalize current chunk without last word
        if len(tokenizer.encode(" ".join(chunk))) >= max_tokens:
            chunk.pop()  # Remove last word that caused overflow
            chunks.append(" ".join(chunk))
            chunk = [word]  # Start new chunk with the last word
    if chunk:
        chunks.append(" ".join(chunk))
    return chunks

# Set Azure OpenAI credentials from Streamlit secrets
openai.api_type = "azure"
openai.api_base = st.secrets["azure_endpoint1"] # Base URL only, no path
openai.api_version = st.secrets["api_version1"] 
openai.api_key = st.secrets["subscription_key1"]

# Embedding deployment/model name (make sure this matches your Azure deployment name)
EMBEDDING_MODEL = st.secrets["deployment1"]

vector_store = []

for url in urls:
    print(f"🔍 Processing {url}")
    content = fetch_clean_text(url)
    if not content:
        print(f"⚠️ No content fetched for {url}, skipping...")
        continue
    
    chunks = chunk_text(content)
    
    for chunk in chunks:
        if not chunk.strip():
            continue
        
        for attempt in range(3):
            try:
                response = openai.Embedding.create(
                    input=chunk,
                    engine=EMBEDDING_MODEL  # Deployment name here
                )
                embedding = response.data[0].embedding
                print(f"Embedding length: {len(embedding)}")
                
                vector_store.append({
                    "url": url,
                    "text": chunk,
                    "embedding": embedding
                })
                break  # Success, stop retrying
                
            except Exception as e:
                print(f"⚠️ Embedding error on {url} (attempt {attempt+1}): {e}")
                time.sleep(2)
        else:
            print(f"❌ Failed to embed chunk after 3 attempts, skipping this chunk.")

# Save embeddings to JSON file
print("Saving vectors to adgm_vectors.json")
with open("adgm_vectors.json", "w") as f:
    json.dump(vector_store, f)

print(f"\n✅ Embedded and saved {len(vector_store)} chunks to adgm_vectors.json")
