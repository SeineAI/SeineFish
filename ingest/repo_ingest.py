from langchain_core.document_loaders import BaseLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import os
import git
from typing import Iterator, AsyncIterator
import asyncio
import json


class GitRepoCommitsLoader(BaseLoader):
    """A document loader that reads git repository commits."""

    def __init__(self, repo_path: str) -> None:
        """Initialize the loader with the path to the git repository.

        Args:
            repo_path: The path to the git repository.
        """
        self.repo_path = repo_path

    def lazy_load(self) -> Iterator[Document]:
        """A lazy loader that reads git repository commits.

        Yields documents one by one for each commit in the repository.
        """
        repo = git.Repo(self.repo_path)
        commits = list(repo.iter_commits())

        for commit in commits:
            commit_message = commit.message
            commit_diff = commit.diff(create_patch=True)

            diff_texts = []
            for diff in commit_diff:
                diff_texts.append(diff.diff.decode('utf-8'))

            commit_diff_text = '\n'.join(diff_texts)
            content = f"Commit Message:\n{commit_message}\n\nCommit Diff:\n{commit_diff_text}"

            yield Document(page_content=content,
                           metadata={
                               "commit_hash": commit.hexsha,
                               "author": commit.author.name,
                               "date": commit.committed_datetime.isoformat()
                           })

    async def alazy_load(self) -> AsyncIterator[Document]:
        """An async lazy loader that reads git repository commits."""

        # Simulating async functionality (since gitpython does not support async)
        def get_commits():
            repo = git.Repo(self.repo_path)
            return list(repo.iter_commits())

        commits = await asyncio.to_thread(get_commits)

        for commit in commits:
            commit_message = commit.message
            commit_diff = commit.diff(create_patch=True)

            diff_texts = []
            for diff in commit_diff:
                diff_texts.append(diff.diff.decode('utf-8'))

            commit_diff_text = '\n'.join(diff_texts)
            content = f"Commit Message:\n{commit_message}\n\nCommit Diff:\n{commit_diff_text}"

            yield Document(page_content=content,
                           metadata={
                               "commit_hash": commit.hexsha,
                               "author": commit.author.name,
                               "date": commit.committed_datetime.isoformat()
                           })


def save_latest_commit(repo_path, commit_hash):
    """Saves the latest commit hash to a file."""
    with open(f"latest_commit.json", "w") as f:
        json.dump({"latest_commit": commit_hash}, f)


def load_latest_commit(repo_path):
    """Loads the latest commit hash from a file."""
    try:
        with open(f"latest_commit.json", "r") as f:
            data = json.load(f)
            return data.get("latest_commit")
    except FileNotFoundError:
        return None


def load_and_index_git_repository(repo_path, faiss_index_path):
    """
    Loads documents from a Git repository and creates a FAISS index.

    Args:
        repo_path (str): The path to the Git repository.
        faiss_index_path (str): The path to save the FAISS index.

    Returns:
        FAISS: The loaded FAISS vectorstore.
    """
    # Fetch latest commits from remote
    repo = git.Repo(repo_path)
    origin = repo.remote(name='origin')
    origin.fetch()

    # Initialize the embeddings model
    embeddings = OpenAIEmbeddings()

    # Check if the FAISS index already exists
    if not os.path.exists(faiss_index_path):
        # Initialize the GitRepoCommitsLoader
        loader = GitRepoCommitsLoader(repo_path=repo_path)

        # Load documents from the git repository
        documents = list(loader.lazy_load())

        # Create a FAISS vectorstore from the loaded documents
        vectorstore = FAISS.from_documents(documents, embeddings)

        # Save the vectorstore locally
        vectorstore.save_local(faiss_index_path)

        # Save the latest commit hash
        if documents:
            latest_commit = documents[0].metadata['commit_hash']
            save_latest_commit(repo_path, latest_commit)
    else:
        # Load the existing FAISS index
        vectorstore = FAISS.load_local(faiss_index_path, embeddings)

        # Load the latest indexed commit
        latest_commit = load_latest_commit(repo_path)

        # Load new commits from the git repository
        new_documents = []
        for commit in repo.iter_commits():
            if commit.hexsha == latest_commit:
                break
            commit_message = commit.message
            commit_diff = commit.diff(create_patch=True)

            diff_texts = []
            for diff in commit_diff:
                diff_texts.append(diff.diff.decode('utf-8'))

            commit_diff_text = '\n'.join(diff_texts)
            content = f"Commit Message:\n{commit_message}\n\nCommit Diff:\n{commit_diff_text}"

            new_documents.append(
                Document(page_content=content,
                         metadata={
                             "commit_hash": commit.hexsha,
                             "author": commit.author.name,
                             "date": commit.committed_datetime.isoformat()
                         }))

        # Add new documents to the vectorstore
        if new_documents:
            vectorstore.add_documents(new_documents)
            vectorstore.save_local(faiss_index_path)

            # Save the latest commit hash
            save_latest_commit(repo_path,
                               new_documents[0].metadata['commit_hash'])

    return vectorstore


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
    faiss_index_path = "faiss_index"

    # Load and index the Git repository
    vectorstore = load_and_index_git_repository(repo_path, faiss_index_path)

    # Example similarity search
    query = "custom git commit loader"
    results = similarity_search(vectorstore, query)

    for result in results:
        print(result.metadata)
        print(result.page_content)
