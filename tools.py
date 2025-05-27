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