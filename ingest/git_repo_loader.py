import os
import json
import git
import pinecone
from typing import Iterator, AsyncIterator
from langchain_core.document_loaders import BaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import asyncio
from langchain_community.vectorstores import FAISS

# Set the storage path
storage_path = os.getenv("STORAGE_PATH", "/tmp")
faiss_index_path = storage_path + "/faiss_index"
latest_commit_path = storage_path + "/latest_commit.json"
vector_store_choice = os.getenv("VECTOR_STORE", "faiss").lower()

# Initialize Pinecone if chosen
if vector_store_choice == "pinecone":
    pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"),
                           environment=os.getenv("PINECONE_ENVIRONMENT"))
    index_name = "git-commits"
    list_indexes = pc.list_indexes()
    index_names = [index.name for index in list_indexes]
    print(
        f"Checking if index '{index_name}' exists in list of indexes: {index_names}"
    )

    if index_name not in index_names:
        pc.create_index(index_name,
                        dimension=1536,
                        spec=pinecone.ServerlessSpec(cloud="aws",
                                                     region="us-east-1"))
    pinecone_index = pc.Index(index_name)


class GitRepoCommitsLoader(BaseLoader):
    """
    A custom loader for git repository commits that extracts commit messages and diffs as documents.

    Attributes:
        repo_path (str): The path to the git repository.
    """

    def __init__(self, repo_path: str) -> None:
        """
        Initializes the GitRepoCommitsLoader with the specified repository path.

        Args:
            repo_path (str): The path to the git repository.
        """
        self.repo_path = repo_path

    def lazy_load(self) -> Iterator[Document]:
        """
        Lazily loads the commit messages and diffs from the git repository.

        Yields:
            Iterator[Document]: An iterator of Document objects containing commit messages and diffs.
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
        """
        Asynchronously lazily loads the commit messages and diffs from the git repository.

        Yields:
            AsyncIterator[Document]: An async iterator of Document objects containing commit messages and diffs.
        """

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
    """
    Saves the latest commit hash to a JSON file.

    Args:
        repo_path (str): The path to the git repository.
        commit_hash (str): The hash of the latest commit.
    """
    with open(latest_commit_path, "w") as f:
        json.dump({"latest_commit": commit_hash}, f)


def load_latest_commit(repo_path):
    """
    Loads the latest commit hash from a JSON file.

    Args:
        repo_path (str): The path to the git repository.

    Returns:
        str: The hash of the latest commit, or None if the file is not found.
    """
    try:
        with open(latest_commit_path, "r") as f:
            data = json.load(f)
            return data.get("latest_commit")
    except FileNotFoundError:
        return None


def load_and_index_git_repository(repo_path: str):
    """
    Loads and indexes the git repository commits into the chosen vector store.

    Args:
        repo_path (str): The path to the git repository.
    """
    repo = git.Repo(repo_path)
    origin = repo.remote(name='origin')
    origin.fetch()

    embeddings = OpenAIEmbeddings()

    loader = GitRepoCommitsLoader(repo_path=repo_path)
    documents = list(loader.lazy_load())

    if vector_store_choice == "faiss":
        if not os.path.exists(faiss_index_path):
            vectorstore = FAISS.from_documents(documents, embeddings)
            vectorstore.save_local(faiss_index_path)

            if documents:
                latest_commit = documents[0].metadata['commit_hash']
                save_latest_commit(repo_path, latest_commit)
        else:
            vectorstore = FAISS.load_local(faiss_index_path, embeddings)
            latest_commit = load_latest_commit(repo_path)

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

            if new_documents:
                vectorstore.add_documents(new_documents)
                vectorstore.save_local(faiss_index_path)
                save_latest_commit(repo_path,
                                   new_documents[0].metadata['commit_hash'])

        return vectorstore

    elif vector_store_choice == "pinecone":
        if documents:
            vectors = []
            for doc in documents:
                vector = embeddings.embed_query(doc.page_content)
                vectors.append((doc.metadata['commit_hash'], vector))

            pinecone_index.upsert(vectors)
            latest_commit = documents[0].metadata['commit_hash']
            save_latest_commit(repo_path, latest_commit)
        else:
            latest_commit = load_latest_commit(repo_path)
            if latest_commit:
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
                                     "date":
                                     commit.committed_datetime.isoformat()
                                 }))

                if new_documents:
                    vectors = []
                    for doc in new_documents:
                        vector = embeddings.embed_query(doc.page_content)
                        vectors.append((doc.metadata['commit_hash'], vector))

                    pinecone_index.upsert(vectors)
                    save_latest_commit(
                        repo_path, new_documents[0].metadata['commit_hash'])

        return pinecone_index


def similarity_search(query, score=0.8):
    """
    Performs a similarity search on the chosen vector store using the given query.

    Args:
        query: The query vector used to perform the similarity search. This should be a list or numpy array representing the query vector.

    Returns:
        results: The search results returned by the vector store. This will be a list of dictionaries containing the matched items and their similarity scores.
    """
    embeddings = OpenAIEmbeddings()

    if vector_store_choice == "faiss":
        vectorstore = FAISS.load_local(faiss_index_path, embeddings)
        results = vectorstore.similarity_search_with_relevance_scores(query)
        ret = []
        for i in results:
            doc = i[0]
            relevance_score = i[1]
            print('relevance_score:', relevance_score)
            if relevance_score > score:
                ret.append(doc)
        return ret
    elif vector_store_choice == "pinecone":
        query_vector = embeddings.embed_query(query)
        results = pinecone_index.query(queries=[query_vector],
                                       top_k=3)  # Perform a similarity search

        return results['matches']
    return None
