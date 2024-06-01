from flask import Flask, request, redirect, session, jsonify
import requests
import os
import json
from options import Options
from handlers import (
    handle_pull_request_event,
    handle_pull_request_review_comment_event,
    handle_pull_request_review_event,
    handle_pull_request_review_thread_event,
)
import prompts

import sys

sys.path.append('..')
from deploy.create_webhook import get_ngrok_url

GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
#WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
ngrok_web_addr = os.environ.get(
    "NGROK_WEB_ADDR")  # e.g. http://localhost:4040/api/tunnels
ngrok_url = get_ngrok_url(ngrok_web_addr)
print(f"ngrok_url: {ngrok_url}")
# Set up the web application
app = Flask(__name__)
app.secret_key = os.urandom(24)


# Define the GitHub webhook handler
@app.route('/github-webhook', methods=['POST'])
async def handle_github_event():
    """
    Handle incoming GitHub webhook events.

    Args:
        request (aiohttp.web.Request): The incoming HTTP request.

    Returns:
        aiohttp.web.Response: The HTTP response.
    """
    event = request.json
    event_type = request.headers.get('X-GitHub-Event', 'ping')

    if event_type == 'ping':
        return "Pong", 200

    if event_type == 'pull_request':
        await handle_pull_request_event(event)
        msg = "Pull request event handled"
        return msg, 200

    if event_type == 'pull_request_review_comment':
        await handle_pull_request_review_comment_event(event)
        msg = "Pull request review comment event handled"
        return msg, 200

    if event_type == 'pull_request_review':
        await handle_pull_request_review_event(event)
        msg = "Pull request review event handled"
        return msg, 200

    if event_type == 'pull_request_review_thread':
        await handle_pull_request_review_thread_event(event)
        msg = "Pull request review thread event handled"
        return msg, 200

    return "Unsupported event", 400


@app.route('/update-prompt', methods=['POST'])
def handle_prompt_update():
    """
    Handle prompt update requests.

    Args:
        request (aiohttp.web.Request): The incoming HTTP request.

    Returns:
        aiohttp.web.Response: The HTTP response.
    """
    try:
        data = request.json()
        prompt_name = data.get('prompt_name')
        new_prompt = data.get('new_prompt')

        if prompt_name and new_prompt:
            if prompt_name in prompts.__dict__:
                setattr(prompts, prompt_name, new_prompt)
                return f"Prompt '{prompt_name}' updated successfully.", 200
            else:
                return f"Prompt '{prompt_name}' not found.", 404
        else:
            return "Missing 'prompt_name' or 'new_prompt' in request body.", 400
    except json.JSONDecodeError:
        return "Invalid JSON in request body.", 400


@app.route('/callback')
def handle_callback():
    code = request.args.get('code')
    access_token = get_github_access_token(code)
    session['github_token'] = access_token
    return 'GitHub authentication successful! You can now set this URL as your GitHub webhook.'


@app.route('/')
def handle_home():
    return 'Welcome to the GitHub Webhook Service. <a href="/login">Login with GitHub</a>'


@app.route('/login')
def handle_login():
    github_authorize_url = (
        f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={ngrok_url}/callback&scope=repo"
    )
    return redirect(github_authorize_url)


def get_github_access_token(code):
    url = 'https://github.com/login/oauth/access_token'
    headers = {'Accept': 'application/json'}
    data = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code,
        'redirect_uri': f"{ngrok_url}/callback",
    }
    response = requests.post(url, headers=headers, data=data)
    response_data = response.json()
    return response_data.get('access_token')


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

    app.run(debug=True, port=8000)
