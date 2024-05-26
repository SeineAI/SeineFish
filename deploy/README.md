# GitHub Webhook Setup

This Python script automates the process of setting up a GitHub webhook for a repository using ngrok. It configures the webhook to receive notifications for various events such as issues, issue comments, pull requests, pull request comments, pushes, releases, forks, and watches.

## Prerequisites

Before running the script, make sure you have the following:

- Python installed on your machine
- `requests` library installed (`pip install requests`)
- ngrok installed and running on your machine

## Environment Variables

To run the script, you need to set the following environment variables:

- `REPO_OWNER`: The owner or organization of the GitHub repository.
- `REPO_NAME`: The name of the GitHub repository.
- `WEBHOOK_PORT`: The port number on which the webhook will be running.
- `WEBHOOK_ENDPOINT`: The endpoint path for the webhook. In this case, it is set to `/github-webhook`.
- `GITHUB_TOKEN`: Your personal access token with the necessary permissions to manage webhooks.
- `NGROK_WEB_ADDR`: The address of the ngrok web interface. Default is `http://localhost:4040/api/tunnels`.

### Setting Environment Variables

You can set the environment variables in your terminal or command prompt before running the script. Here's an example of how to set the environment variables using mock values:

```bash
export REPO_OWNER=YourGitHubUsername
export REPO_NAME=YourRepositoryName
export WEBHOOK_PORT=8000
export WEBHOOK_ENDPOINT=/github-webhook
export GITHUB_TOKEN=your_personal_access_token
export NGROK_WEB_ADDR=http://localhost:4040/api/tunnels
```

Replace `YourGitHubUsername` with your actual GitHub username or organization name, `YourRepositoryName` with the name of your repository, `8000` with the desired port number for the webhook, `your_personal_access_token` with your actual GitHub personal access token, and `http://localhost:4040/api/tunnels` with the address of your ngrok web interface if different.

## Running the Script

Once you have set the environment variables, you can run the script using the following command:

```bash
python webhook_setup.py
```

The script will perform the following steps:

1. Check if there is an existing ngrok tunnel. If found, it will use the existing tunnel's public URL.
2. If no existing tunnel is found, it will create a new ngrok tunnel using the specified port number.
3. Remove any existing webhooks from the repository.
4. Set up a new GitHub webhook for the repository using the ngrok tunnel's public URL and the specified webhook endpoint.

The script will provide informative messages throughout the process, indicating the status of each step.

## Webhook Events

The webhook is configured to receive notifications for the following events:

- Issues
- Issue comments
- Pull requests
- Pull request review comments
- Pushes
- Releases
- Forks
- Watches

Whenever any of these events occur in the specified repository, GitHub will send a notification to the webhook URL.

## Troubleshooting

If you encounter any issues while running the script, make sure:

- You have correctly set the environment variables with valid values.
- ngrok is installed and running on your machine.
- You have the necessary permissions to manage webhooks for the specified repository.
- Your GitHub personal access token has the required scopes to create and delete webhooks.

If the script fails to create the webhook, it will display an error message along with the status code and response content for debugging purposes.
