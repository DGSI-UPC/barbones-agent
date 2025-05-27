import chromadb
import uuid
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

def embed_information(content: str, category: str) -> str:
    client = chromadb.Client()
    collection_name = category
    collection = client.get_or_create_collection(name=collection_name)

    if not content:
        print("Content cannot be empty. No document added.")
        return None

    doc_id = str(uuid.uuid4())
    documents_to_add = [content]
    ids_to_add = [doc_id]
    metadatas_to_add = [{"category": category}]

    collection.add(
        documents=documents_to_add,
        metadatas=metadatas_to_add,
        ids=ids_to_add
    )
    
    print(f"Successfully added 1 document with id '{doc_id}' to the '{collection_name}' collection.")
    return doc_id

def query_information(query_text: str, category: str) -> dict:
    client = chromadb.Client()
    collection_name = category

    try:
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        print(f"Error getting collection '{collection_name}': {e}")
        print(f"Please ensure the collection '{collection_name}' exists and has data.")
        return {"error": str(e), "documents": [[]], "distances": [[]], "metadatas": [[]], "ids": [[]]}

    if not query_text:
        print("Query text cannot be empty.")
        return {"error": "Query text cannot be empty", "documents": [[]], "distances": [[]], "metadatas": [[]], "ids": [[]]}

    results = collection.query(
        query_texts=[query_text],
        n_results=5,
        include=['documents', 'distances', 'metadatas']
    )
    
    print(f"Query results from '{collection_name}' for '{query_text}': {results}")
    return results

def scrape_and_embed_website(url: str) -> list[str]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    chunks = [p for p in paragraphs if p]

    if not chunks:
        print(f"No text content found or extracted from paragraphs at {url}.")
        return []

    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    original_hostname_for_meta = hostname if hostname else "unknown_host"

    if not hostname:
        category_name_base = "unknown_website_host"
    else:
        if hostname.startswith("www."):
            hostname = hostname[len("www."):]
        
        name_parts = hostname.split('.')
        if len(name_parts) > 1:
            category_name_base = ".".join(name_parts[:-1])
        else:
            category_name_base = name_parts[0]
    
    category = re.sub(r'[^a-zA-Z0-9_-]+', '_', category_name_base)
    category = category.strip('_')

    if len(category) > 60:
        category = category[:60]
    if len(category) < 3:
        category = f"{category}_web" if category else "scraped_data"
        while len(category) < 3:
            category += "_"
    category = category[:63]

    if not category:
        category = "default_scraped_content"

    client = chromadb.Client()
    collection = client.get_or_create_collection(name=category)

    documents_to_add = []
    ids_to_add = []
    metadatas_to_add = []

    for i, chunk_content in enumerate(chunks):
        doc_id = str(uuid.uuid4())
        documents_to_add.append(chunk_content)
        ids_to_add.append(doc_id)
        metadatas_to_add.append({
            "source_url": url,
            "chunk_index": i,
            "original_hostname": original_hostname_for_meta
        })

    if not documents_to_add:
        print(f"No valid chunks to embed from {url}.")
        return []

    collection.add(
        documents=documents_to_add,
        metadatas=metadatas_to_add,
        ids=ids_to_add
    )

    print(f"Successfully embedded {len(documents_to_add)} chunks from {url} into category '{category}'.")
    return ids_to_add

if __name__ == '__main__':
    target_url = "https://bernatbc.tk" 
    print(f"Attempting to scrape and embed content from: {target_url}")
    
    embedded_doc_ids = scrape_and_embed_website(target_url)
    
    if embedded_doc_ids:
        print(f"\nSuccessfully scraped and embedded {len(embedded_doc_ids)} chunks from {target_url}.")
        print(f"Document IDs: {embedded_doc_ids}")

        parsed_url = urlparse(target_url)
        hostname = parsed_url.hostname
        if hostname.startswith("www."):
            hostname = hostname[len("www."):]
        name_parts = hostname.split('.')
        if len(name_parts) > 1:
            category_name_base = ".".join(name_parts[:-1])
        else:
            category_name_base = name_parts[0]
        
        category = re.sub(r'[^a-zA-Z0-9_-]+', '_', category_name_base)
        category = category.strip('_')
        if len(category) > 60: category = category[:60]
        if len(category) < 3:
            category = f"{category}_web" if category else "scraped_data"
            while len(category) < 3: category += "_"
        category = category[:63]
        if not category: category = "default_scraped_content"

        print(f"\nTo query this information, use category: '{category}'")
    else:
        print(f"\nFailed to scrape or embed content from {target_url}.")