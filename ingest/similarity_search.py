def similarity_search(vectorstore, query):
    """
    Performs a similarity search on the provided vector store using the given query.

    Args:
        vectorstore: The vector store to search within. This should be an instance that supports similarity search.
        query: The query used to perform the similarity search. This could be a text string or a vector, depending on the implementation of the vector store.

    Returns:
        results: The search results returned by the vector store. The format of the results will depend on the implementation of the vector store.
    """
    results = vectorstore.similarity_search(query)
    return results
