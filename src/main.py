import os
import json
import logging
import aiohttp
from github import Github
from aiohttp import web
from options import Options
from utils import extract_function_code, find_changed_functions, get_file_content
from backend import Backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up GitHub token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Initialize GitHub client
github_client = Github(GITHUB_TOKEN)

# Initialize backend
backend = Backend()


# Define event handlers
async def handle_pull_request_event(event):
    """
    Handle pull request events from GitHub.

    Args:
        event (dict): GitHub event payload.
    """
    repo_name = event['repository']['full_name']
    pr_number = event['number']
    action = event['action']
    logger.info(
        f"Handling pull request event: {repo_name} #{pr_number}, action: {action}"
    )

    if action in ['opened', 'edited', 'synchronize']:
        await review_pull_request(repo_name, pr_number)


async def handle_pull_request_review_comment_event(event):
    """
    Handle pull request review comment events from GitHub.

    Args:
        event (dict): GitHub event payload.
    """
    repo_name = event['repository']['full_name']
    pr_number = event['pull_request']['number']
    comment_id = event['comment']['id']
    action = event['action']
    logger.info(
        f"Handling pull request review comment event: {repo_name} #{pr_number}, action: {action}, comment id: {comment_id}"
    )

    if action in ['created', 'edited']:
        await analyze_review_comment(repo_name, pr_number, comment_id)


async def handle_pull_request_review_event(event):
    """
    Handle pull request review events from GitHub.

    Args:
        event (dict): GitHub event payload.
    """
    repo_name = event['repository']['full_name']
    pr_number = event['pull_request']['number']
    review_id = event['review']['id']
    action = event['action']
    logger.info(
        f"Handling pull request review event: {repo_name} #{pr_number}, action: {action}, review id: {review_id}"
    )

    if action in ['submitted', 'edited']:
        await analyze_pull_request_review(repo_name, pr_number, review_id)


async def handle_pull_request_review_thread_event(event):
    """
    Handle pull request review thread events from GitHub.

    Args:
        event (dict): GitHub event payload.
    """
    repo_name = event['repository']['full_name']
    pr_number = event['pull_request']['number']
    thread_id = event['thread']['id']
    action = event['action']
    logger.info(
        f"Handling pull request review thread event: {repo_name} #{pr_number}, action: {action}, thread id: {thread_id}"
    )

    if action in ['resolved', 'unresolved']:
        await analyze_review_thread(repo_name, pr_number, thread_id)


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
    prompt = f"Analyze the following file change in {filename}:\n\nFile content:\n```python\n{file_content}\n```\n\nChanges:\n```diff\n{file_diff}\n```"

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
    prompt = f"Analyze the following function change in {filename}:\n\nOriginal function:\n```python\n{original_function_code}\n```\n\nChanges:\n```diff\n{function_diff}\n```"

    response = backend.generate(prompt)
    review_text = response['choices'][0]['text'].strip()
    logger.info(f"Analysis for {function_name} in {filename}:\n{review_text}")

    return {'function_name': function_name, 'review': review_text}


async def analyze_review_comment(repo_name, pr_number, comment_id):
    """
    Analyze a review comment.

    Args:
        repo_name (str): The full name of the repository.
        pr_number (int): The number of the pull request.
        comment_id (int): The ID of the review comment.
    """
    repo = github_client.get_repo(repo_name)
    comment = repo.get_pull(pr_number).get_review_comment(comment_id)
    comment_body = comment.body

    prompt = f"Analyze the following pull request review comment:\n\n{comment_body}\n"
    response = backend.generate(prompt)
    analysis = response['choices'][0]['text'].strip()
    logger.info(f"Analysis for review comment {comment_id}:\n{analysis}")

    # Post a reply to the comment with the analysis
    comment.create_reply(body=analysis)


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

    prompt = f"Analyze the following pull request review:\n\n{review_body}\n"
    response = backend.generate(prompt)
    analysis = response['choices'][0]['text'].strip()
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

    prompt = f"Analyze the following pull request review thread:\n\n" + "\n\n".join(
        thread_comments) + "\n"
    response = backend.generate(prompt)
    analysis = response['choices'][0]['text'].strip()
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


# Define the GitHub webhook handler
async def handle_github_event(request):
    """
    Handle incoming GitHub webhook events.

    Args:
        request (aiohttp.web.Request): The incoming HTTP request.

    Returns:
        aiohttp.web.Response: The HTTP response.
    """
    event = await request.json()
    event_type = request.headers.get('X-GitHub-Event', 'ping')

    if event_type == 'ping':
        return web.Response(text="Pong")

    if event_type == 'pull_request':
        await handle_pull_request_event(event)
        return web.Response(text="Pull request event handled")

    if event_type == 'pull_request_review_comment':
        await handle_pull_request_review_comment_event(event)
        return web.Response(text="Pull request review comment event handled")

    if event_type == 'pull_request_review':
        await handle_pull_request_review_event(event)
        return web.Response(text="Pull request review event handled")

    if event_type == 'pull_request_review_thread':
        await handle_pull_request_review_thread_event(event)
        return web.Response(text="Pull request review thread event handled")

    return web.Response(status=400, text="Unsupported event")


# Set up the web application
app = web.Application()
app.router.add_post('/github-webhook', handle_github_event)

# Define the entry point for the GitHub Action
if __name__ == '__main__':
    options = Options(github_token=os.getenv("GITHUB_TOKEN"),
                      openai_api_key=os.getenv("OPENAI_API_KEY"),
                      github_repository=os.getenv("GITHUB_REPOSITORY"),
                      github_event_path=os.getenv("GITHUB_EVENT_PATH"),
                      github_event_name=os.getenv("GITHUB_EVENT_NAME"),
                      watsonx_api_key=os.getenv("WATSONX_API_KEY"),
                      watsonx_project_id=os.getenv("WATSONX_PROJECT_ID"))

    if options.github_event_name in [
            'pull_request', 'pull_request_review_comment',
            'pull_request_review', 'pull_request_review_thread'
    ]:
        with open(options.github_event_path, 'r') as f:
            event = json.load(f)
        if options.github_event_name == 'pull_request':
            handle_pull_request_event(event)
        elif options.github_event_name == 'pull_request_review_comment':
            handle_pull_request_review_comment_event(event)
        elif options.github_event_name == 'pull_request_review':
            handle_pull_request_review_event(event)
        elif options.github_event_name == 'pull_request_review_thread':
            handle_pull_request_review_thread_event(event)

    web.run_app(app, port=8000)
