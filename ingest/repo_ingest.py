from langchain.document_loaders import GitLoader
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import os


def load_and_index_git_repository(repo_path, branch, faiss_index_path):
    """
    Loads documents from a Git repository and creates a FAISS index.

    Args:
        repo_path (str): The path to the Git repository.
        branch (str): The branch of the Git repository to load.
        faiss_index_path (str): The path to save the FAISS index.

    Returns:
        FAISS: The loaded FAISS vectorstore.
    """
    # Check if the FAISS index already exists
    if not os.path.exists(faiss_index_path):
        # Initialize the GitLoader with filtering options
        loader = GitLoader(repo_path=repo_path, branch=branch)

        # Load documents from the git repository
        documents = loader.load()

        # Initialize the embeddings model
        embeddings = OpenAIEmbeddings()

        # Create a FAISS vectorstore from the loaded documents
        vectorstore = FAISS.from_documents(documents, embeddings)

        # Save the vectorstore locally
        vectorstore.save_local("faiss_index")

    embeddings = OpenAIEmbeddings()

    # To load the vectorstore later
    new_vectorstore = FAISS.load_local("faiss_index", embeddings)

    return new_vectorstore


def similarity_search(vectorstore, query):
    """
    Performs a similarity search on the FAISS vectorstore.

    Args:
        vectorstore (FAISS): The FAISS vectorstore to search.
        query (str): The search query.

    Returns:
        list: The search results.
    """
    results = vectorstore.similarity_search(query)
    return results


if __name__ == "__main__":
    # Initialize Git repository
    repo_path = os.environ.get('REPO_PATH')
    branch = 'main'
    faiss_index_path = "faiss_index"

    # Load and index the Git repository
    vectorstore = load_and_index_git_repository(repo_path, branch,
                                                faiss_index_path)

    # Example similarity search
    query = "improve performance."
    results = similarity_search(vectorstore, query)

    for result in results:
        print(result.page_content)
