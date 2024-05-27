import base64
import aiohttp
import logging
from typing import Dict
from github.Repository import Repository
from github.PullRequest import PullRequest

logger = logging.getLogger(__name__)


async def get_file_content(repo: Repository, pull_request: PullRequest,
                           file_path: str) -> str:
    """
    Get the full content of a file at the specified path in the pull request.

    Args:
        repo (Repository): The GitHub repository.
        pull_request (PullRequest): The pull request.
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    file_content_url = f"https://api.github.com/repos/{repo.full_name}/contents/{file_path}?ref={pull_request.head.sha}"
    logger.debug(f"Getting file content from {file_content_url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(file_content_url) as response:
            file_data = await response.json()
            file_content = base64.b64decode(
                file_data["content"]).decode("utf-8")
    return file_content


def find_changed_functions(file_diff: str) -> Dict[str, str]:
    """
    Find the functions that are changed in the file diff.

    Args:
        file_diff (str): The file diff.

    Returns:
        Dict[str, str]: A dictionary of function names and their diffs.
    """
    changed_functions = {}
    function_name = None
    function_diff = ""
    for line in file_diff.split("\n"):
        if line.startswith("def "):
            if function_name is not None:
                changed_functions[function_name] = function_diff
            function_name = line.split("def ")[1].split("(")[0]
            function_diff = line + "\n"
        elif function_name is not None:
            function_diff += line + "\n"
    if function_name is not None:
        changed_functions[function_name] = function_diff
    return changed_functions


def extract_function_code(file_content: str, function_name: str) -> str:
    """
    Extract the full code of a function from the file content.

    Args:
        file_content (str): The content of the file.
        function_name (str): The name of the function.

    Returns:
        str: The full code of the function.
    """
    function_code = ""
    inside_function = False
    for line in file_content.split("\n"):
        if line.startswith(f"def {function_name}("):
            inside_function = True
        if inside_function:
            function_code += line + "\n"
            if line.startswith("    return") or line.startswith(
                    "    raise") or line == "":
                inside_function = False
    return function_code

def similarity_search(vectorstore, query):
    """
    Performs a similarity search on the FAISS vectorstore.

    Args:
        vectorstore (FAISS): The FAISS vectorstore to search.
        query (str): The search query.

    Returns:
        list: The search results.
    """
    
    # Load and index the Git repository
    vectorstore = load_and_index_git_repository(repo_path, faiss_index_path)

    
    results = similarity_search(vectorstore, query)
    results = vectorstore.similarity_search(query)
    return results

