import chromadb
import uuid

def embed_information(content: str, category: str) -> str:
    """
    Embeds a single piece of information (document) into a ChromaDB collection
    named after the category, and stores the category as metadata.

    Args:
        content (str): The text content to embed.
        category (str): The category of the content. This will be used as the
                        collection name and stored as metadata.

    Returns:
        str: The auto-generated unique ID for the embedded document.
    """
    # Initialize the ChromaDB client (in-memory client)
    # For a persistent client, use: client = chromadb.PersistentClient(path="/path/to/your/db")
    client = chromadb.Client()

    collection_name = category  # Use category as collection name
    # Get or create the collection
    collection = client.get_or_create_collection(name=collection_name)

    if not content:
        print("Content cannot be empty. No document added.")
        return None # Or raise an error

    doc_id = str(uuid.uuid4()) # Generate a unique ID

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
    """
    Queries a ChromaDB collection for information related to the query_text.
    Returns up to 5 results.

    Args:
        query_text (str): The text to search for.
        category (str): The category (collection name) to search within.

    Returns:
        dict: The query results from ChromaDB.
    """
    client = chromadb.Client()
    collection_name = category

    try:
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        # Handle cases where the collection might not exist,
        # though get_collection usually raises a ValueError if it doesn't.
        # ChromaDB's behavior for non-existent collections with get_collection
        # might vary or be configured. For robustness, explicit error handling or
        # a check like `client.list_collections()` could be added if needed.
        print(f"Error getting collection '{collection_name}': {e}")
        print(f"Please ensure the collection '{collection_name}' exists and has data.")
        return {"error": str(e), "documents": [[]], "distances": [[]], "metadatas": [[]], "ids": [[]]}


    if not query_text:
        print("Query text cannot be empty.")
        return {"error": "Query text cannot be empty", "documents": [[]], "distances": [[]], "metadatas": [[]], "ids": [[]]}

    results = collection.query(
        query_texts=[query_text],
        n_results=5, # Hardcoded to 5 results
        include=['documents', 'distances', 'metadatas'] # Adjust as needed
    )
    
    print(f"Query results from '{collection_name}' for '{query_text}': {results}")
    return results
"""
if __name__ == '__main__':
    # Example usage:

    # Embed documents and store their IDs
    doc_id1 = embed_information(
        content="This is the first document about ChromaDB.",
        category="tech"
    )
    doc_id2 = embed_information(
        content="ChromaDB is a vector database.",
        category="tech"
    )
    doc_id3 = embed_information(
        content="It can be used for semantic search.",
        category="search_engines" # Using a different category for this one
    )

    # Example with a different category
    doc_id4 = embed_information(
        content="Another document here, related to general topics.",
        category="general"
    )
    doc_id5 = embed_information(
        content="This one is also general.",
        category="general"
    )

    # Example query
    if doc_id1: # Ensure at least one document was added to 'tech'
        query_results_tech = query_information(
            query_text="What is ChromaDB?",
            category="tech"
        )
        print(f"\nQuery results for 'What is ChromaDB?' in 'tech': {query_results_tech}")

    if doc_id3: # Ensure at least one document was added to 'search_engines'
        query_results_search = query_information(
            query_text="semantic search",
            category="search_engines"
        )
        print(f"\nQuery results for 'semantic search' in 'search_engines': {query_results_search}")

    # Querying a non-existent or empty collection (or one where query yields no close results)
    # Note: The behavior of query on an empty or non-matching collection is to return empty lists for documents, etc.
    # The error handling in query_information is more for issues like the collection not existing at all.
    query_results_empty = query_information(
        query_text="non_existent_topic",
        category="general" # Assuming 'general' exists but might not match this query well
    )
    print(f"\nQuery results for 'non_existent_topic' in 'general': {query_results_empty}")


    # Verify (optional, for demonstration)
    client = chromadb.Client()
    
    if doc_id1 and doc_id2:
        tech_collection = client.get_collection("tech")
        print(f"\nTech Collection count: {tech_collection.count()}")
        # Note: doc_id3 is in 'search_engines', not 'tech'
        retrieved_tech_items = tech_collection.get(ids=[doc_id1, doc_id2])
        print(f"Tech Collection items (first two): {retrieved_tech_items}")

    if doc_id3:
        search_collection = client.get_collection("search_engines")
        print(f"\nSearch Engines Collection count: {search_collection.count()}")
        retrieved_search_items = search_collection.get(ids=[doc_id3])
        print(f"Search Engines Collection items: {retrieved_search_items}")


    if doc_id4 and doc_id5:
        general_collection = client.get_collection("general")
        print(f"\nGeneral Collection count: {general_collection.count()}")
        retrieved_general_items = general_collection.get(ids=[doc_id4, doc_id5])
        print(f"General Collection items: {retrieved_general_items}")
        """