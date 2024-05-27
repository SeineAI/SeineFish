# SeineFish

A GitHub Webhook that Reviews GitHub Pull Requests

## Overview

SeineFish is a GitHub webhook designed to automatically review pull requests in your GitHub repositories. It uses AI to analyze code changes, provide feedback, and summarize the review results.

## Features

- Handles `pull_request`, `pull_request_review_comment`, `pull_request_review`, and `pull_request_review_thread` events.
- Uses LangChain to select between OpenAI and WatsonX for language model backend.
- Reviews entire file content in pull requests.
- Summarizes reviews and rates pull requests as "GOOD", "NEEDS FURTHER TRIAGE", or "BAD".

## Requirements

- Python 3.8 or higher
- GitHub personal access token with appropriate permissions
- OpenAI API key or WatsonX API key

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SeineAI/SeineFish.git
   cd SeineFish
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Create a `.env` file in the project root directory.
   - Add the following environment variables to the `.env` file:
   | Environment Variable    | Value                           |
   |-------------------------|---------------------------------|
   | GITHUB_TOKEN            | <your_github_token>             |
   | OPENAI_API_KEY          | <your_openai_api_key>           |
   | WATSONX_API_KEY         | <your_watsonx_api_key>          |
   | WATSONX_PROJECT_ID      | <your_watsonx_project_id>       |
   | REPO_OWNER              | <your_github_repo_owner>        |
   | REPO_NAME               | <your_github_repo_name>         |
   | REPO_PATH               | <your_git_repo_path>            |
   | NGROK_WEB_ADDR          | http://localhost:4041/api/tunnels |
   | WEBHOOK_ENDPOINT        | /github-webhook                 |
   | WEBHOOK_PORT            | 8000                            |

5. **Run the webhook server locally for testing:**
   ```bash
   cd src; python main.py
   ```

## Usage

1. **Create the GitHub Webhook:**
   - Use the `create_webhook.sh` script in the `deploy` directory to create the webhook in your GitHub repository.
   - Run the script and follow the prompts:
     ```bash
     ./deploy/create_webhook.sh
     ```

2. **Test the webhook locally:**
   - Use the scripts in the `test` directory to send test payloads to the webhook endpoint.
   - Test pull request events:
     ```bash
     ./test/test_webhook.sh
     ```
   - Test pull request review comment events:
     ```bash
     ./test/test_pull_review.sh
     ```

For more detailed information, visit the [repository](https://github.com/SeineAI/SeineFish).