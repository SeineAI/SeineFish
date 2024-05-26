import os
import logging
from github import Github
from backend import Backend
from prompts import (
    ANALYZE_FILE_CHANGE_PROMPT,
    ANALYZE_FUNCTION_CHANGE_PROMPT,
    ANALYZE_REVIEW_COMMENT_PROMPT,
    ANALYZE_PULL_REQUEST_REVIEW_PROMPT,
    ANALYZE_REVIEW_THREAD_PROMPT,
)
from helpers import get_file_content, find_changed_functions, extract_function_code

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up GitHub token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Initialize GitHub client
github_client = Github(GITHUB_TOKEN)

# Initialize backend
backend = Backend()


async def review_pull_request(repo_name, pr_number):
    """
    Review the pull request using the backend and provide feedback.

    Args:
        repo_name (str): The full name of the repository.
        pr_number (int): The number of the pull request.
    """
    repo = github_client.get_repo(repo_name)
    pull_request = repo.get_pull(pr_number)
    logger.info(
        f"Reviewing pull request: {repo_name} #{pr_number} ({pull_request.title})"
    )

    # Collect metadata
    metadata = {
        'title': pull_request.title,
        'author': pull_request.user.login,
        'description': pull_request.body,
        'url': pull_request.html_url
    }

    # Get changed files and their diffs
    changed_files = []
    for file in pull_request.get_files():
        file_diff = file.patch
        logger.debug(
            f"Processing file: {file.filename} with diff:\n{file_diff}")
        changed_files.append({
            'filename': file.filename,
            'status': file.status,
            'changes': file.changes,
            'additions': file.additions,
            'deletions': file.deletions,
            'diff': file_diff
        })

    # Process each changed file and collect reviews
    file_reviews = []
    for file in changed_files:
        file_review = await review_file(repo, pull_request, file)
        file_reviews.append(file_review)

    logger.info(f"File reviews: {file_reviews}")
    # Summarize file reviews and rate the pull request
    review_summary, rating = summarize_reviews(file_reviews)

    # Post a summary review on the pull request
    review_body = generate_review_body(metadata, file_reviews, review_summary,
                                       rating)
    logger.debug(f"Review body:\n{review_body}")
    pull_request.create_review(body=review_body, event='COMMENT')


async def review_file(repo, pull_request, file):
    """
    Review the entire file content.

    Args:
        repo (Repository): The GitHub repository.
        pull_request (PullRequest): The pull request.
        file (dict): Information about the changed file.

    Returns:
        dict: Review results for the file.
    """
    file_content = await get_file_content(repo, pull_request, file['filename'])

    # Generate a review for the entire file content
    review = await analyze_file_change(file['filename'], file_content,
                                       file['diff'])

    return {
        'filename': file['filename'],
        'status': file['status'],
        'changes': file['changes'],
        'additions': file['additions'],
        'deletions': file['deletions'],
        'review': review
    }


async def analyze_file_change(filename, file_content, file_diff):
    """
    Analyze the file changes using the backend.

    Args:
        filename (str): The name of the file.
        file_content (str): The content of the file.
        file_diff (str): The diff of the file changes.

    Returns:
        str: Review results for the file.
    """
    prompt = ANALYZE_FILE_CHANGE_PROMPT.format(filename=filename,
                                               file_content=file_content,
                                               file_diff=file_diff)

    response = backend.generate(prompt)
    review_text = response.strip()
    logger.info(f"Analysis for {filename}:\n{review_text}")

    return review_text


async def review_file_function(repo, pull_request, file):
    """
    Review functions in a changed file.

    Args:
        repo (Repository): The GitHub repository.
        pull_request (PullRequest): The pull request.
        file (dict): Information about the changed file.

    Returns:
        dict: Review results for the file.
    """
    file_content = await get_file_content(repo, pull_request, file['filename'])
    functions = find_changed_functions(file['diff'])

    function_reviews = []
    for function_name, function_diff in functions.items():
        original_function_code = extract_function_code(file_content,
                                                       function_name)
        review = await analyze_function_change(file['filename'], function_name,
                                               original_function_code,
                                               function_diff)
        function_reviews.append(review)

    return {
        'filename': file['filename'],
        'status': file['status'],
        'changes': file['changes'],
        'additions': file['additions'],
        'deletions': file['deletions'],
        'reviews': function_reviews
    }


async def analyze_function_change(filename, function_name,
                                  original_function_code, function_diff):
    """
    Analyze the function changes using the backend.

    Args:
        filename (str): The name of the file.
        function_name (str): The name of the function.
        original_function_code (str): The original code of the function.
        function_diff (str): The diff of the function changes.

    Returns:
        dict: Review results for the function.
    """
    prompt = ANALYZE_FUNCTION_CHANGE_PROMPT.format(
        filename=filename,
        function_name=function_name,
        original_function_code=original_function_code,
        function_diff=function_diff)

    response = backend.generate(prompt)
    review_text = response.strip()
    logger.info(f"Analysis for {function_name} in {filename}:\n{review_text}")

    return {'function_name': function_name, 'review': review_text}


async def analyze_review_comment(repo_name, pr_number, comment_id, path,
                                 position, commit_id):
    """
    Analyze a review comment.

    Args:
        repo_name (str): The full name of the repository.
        pr_number (int): The number of the pull request.
        comment_id (int): The ID of the review comment.
    """
    repo = github_client.get_repo(repo_name)
    pull_request = repo.get_pull(pr_number)
    comment = pull_request.get_review_comment(comment_id)
    comment_body = comment.body
    # remove @mentions from the comment body
    comment_body = " ".join(
        filter(lambda x: not x.startswith('@'), comment_body.split()))
    logger.info(
        f"Analyzing review comment {comment_id} in {repo_name} #{pr_number}:\n{comment_body}"
    )

    commit = repo.get_commit(commit_id)

    prompt = ANALYZE_REVIEW_COMMENT_PROMPT.format(comment_body=comment_body)
    response = backend.generate(prompt)
    analysis = response.strip()
    logger.info(f"Analysis for review comment {comment_id}:\n{analysis}")

    # Post a reply to the comment with the analysis
    pull_request.create_comment(body=analysis,
                                commit_id=commit,
                                path=path,
                                position=position)


async def analyze_pull_request_review(repo_name, pr_number, review_id):
    """
    Analyze a pull request review.

    Args:
        repo_name (str): The full name of the repository.
        pr_number (int): The number of the pull request.
        review_id (int): The ID of the pull request review.
    """
    repo = github_client.get_repo(repo_name)
    review = repo.get_pull(pr_number).get_review(review_id)
    review_body = review.body

    prompt = ANALYZE_PULL_REQUEST_REVIEW_PROMPT.format(review_body=review_body)
    response = backend.generate(prompt)
    analysis = response.strip()
    logger.info(f"Analysis for review {review_id}:\n{analysis}")

    # Post a reply to the review with the analysis
    review.create_reply(body=analysis)


async def analyze_review_thread(repo_name, pr_number, thread_id):
    """
    Analyze a review thread.

    Args:
        repo_name (str): The full name of the repository.
        pr_number (int): The number of the pull request.
        thread_id (int): The ID of the review thread.
    """
    repo = github_client.get_repo(repo_name)
    thread = repo.get_pull(pr_number).get_review_thread(thread_id)
    thread_comments = [comment.body for comment in thread.comments]

    prompt = ANALYZE_REVIEW_THREAD_PROMPT.format(
        thread_comments="\n\n".join(thread_comments))
    response = backend.generate(prompt)
    analysis = response.strip()
    logger.info(f"Analysis for review thread {thread_id}:\n{analysis}")

    # Post a reply to the thread with the analysis
    thread.comments[-1].create_reply(body=analysis)


def summarize_reviews(file_reviews):
    """
    Summarize the reviews of all changed files and rate the pull request.

    Args:
        file_reviews (list): List of file reviews.

    Returns:
        tuple: Summary of reviews and rating.
    """
    summary = []
    issues_count = 0

    for file_review in file_reviews:
        summary.append(
            f"### {file_review['filename']} ({file_review['status']}):")
        summary.append(f"- **Review:** {file_review['review']}")
        if 'issue' in file_review['review'].lower():
            issues_count += 1

    if issues_count == 0:
        rating = "GOOD"
    elif issues_count < 3:
        rating = "NEEDS FURTHER TRIAGE"
    else:
        rating = "BAD"
    logger.debug(f"Rating for the pull request: {rating}, summary: {summary}")
    return "\n".join(summary), rating


def summarize_function_reviews(file_reviews):
    """
    Summarize the reviews of all functions in changed files and rate the pull request.

    Args:
        file_reviews (list): List of file reviews.

    Returns:
        tuple: Summary of reviews and rating.
    """
    summary = []
    issues_count = 0

    for file_review in file_reviews:
        summary.append(
            f"### {file_review['filename']} ({file_review['status']}):")
        for review in file_review['review']:
            summary.append(
                f"- **Function `{review['function_name']}`:** {review['review']}"
            )
            if 'issue' in review['review'].lower():
                issues_count += 1

    if issues_count == 0:
        rating = "GOOD"
    elif issues_count < 3:
        rating = "NEEDS FURTHER TRIAGE"
    else:
        rating = "BAD"

    return "\n".join(summary), rating


def generate_review_body(metadata, file_reviews, review_summary, rating):
    """
    Generate the review body to be posted on the pull request.

    Args:
        metadata (dict): Metadata of the pull request.
        file_reviews (list): List of file reviews.
        review_summary (str): Summary of the reviews.
        rating (str): Rating of the pull request.

    Returns:
        str: The review body.
    """
    review_body = f"### Pull Request Review for [{metadata['title']}]({metadata['url']})\n"
    review_body += f"**Author:** {metadata['author']}\n\n"
    review_body += f"**Description:**\n{metadata['description']}\n\n"
    review_body += f"#### Changed Files:\n"

    for file in file_reviews:
        review_body += f"- **{file['filename']}** ({file['status']}): {file['changes']} changes\n"
        review_body += f"  - Additions: {file['additions']}, Deletions: {file['deletions']}\n"

    review_body += f"\n### Review Summary:\n{review_summary}\n"
    review_body += f"\n### Rating: {rating}\n"

    return review_body
