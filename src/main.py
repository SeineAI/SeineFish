import os
import json
from aiohttp import web
from options import Options
from handlers import (
    handle_pull_request_event,
    handle_pull_request_review_comment_event,
    handle_pull_request_review_event,
    handle_pull_request_review_thread_event,
)


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
