import os
from git_repo_loader import load_and_index_git_repository, similarity_search


def main():
    """
    This script loads a git repository, indexes it using Faiss, and performs a similarity search.

    It expects the environment variable 'REPO_PATH' to be set with the path to the git repository.

    The script prints the metadata and page content of the search results.
    """
    repo_path = os.environ.get('REPO_PATH')

    vectorstore = load_and_index_git_repository(repo_path)

    query = "custom git commit loader"
    results = similarity_search(query)

    for result in results:
        print(result.metadata)
        # print(result.page_content)


if __name__ == "__main__":
    main()
