import logging
from utils import (
    review_pull_request,
    analyze_review_comment,
    analyze_pull_request_review,
    analyze_review_thread,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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