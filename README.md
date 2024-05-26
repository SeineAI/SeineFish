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
     ```plaintext
     GITHUB_TOKEN=<your_github_token>
     OPENAI_API_KEY=<your_openai_api_key>  # Optional, if using OpenAI
     WATSONX_API_KEY=<your_watsonx_api_key>  # Optional, if using WatsonX
     ```

5. **Run the webhook server locally for testing:**
   ```bash
   python review_bot.py
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