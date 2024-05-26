import os
import requests
import subprocess
import time


def get_ngrok_url(url):
    """
    Retrieves the public URL of the existing ngrok tunnel.

    Returns:
        str: The public URL of the ngrok tunnel if found, None otherwise.
    """
    # Send a GET request to the ngrok API to retrieve the public URL
    response = requests.get(url)

    # Check the response status code
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Extract the public URL from the response
        ngrok_url = data["tunnels"][0]["public_url"]

        return ngrok_url
    else:
        return None


def create_ngrok_tunnel(port):
    """
    Creates a new ngrok tunnel using the specified port number.

    Args:
        port (int): The port number on which the webhook will be running.

    Returns:
        str: The public URL of the newly created ngrok tunnel if successful, None otherwise.
    """
    try:
        # Start ngrok and create a new tunnel
        subprocess.Popen(["ngrok", "http", str(port)])

        # Wait for a few seconds to allow ngrok to start
        time.sleep(5)

        # Retrieve the ngrok public URL
        ngrok_url = get_ngrok_url()

        if ngrok_url:
            print(
                f"ngrok tunnel created successfully. Public URL: {ngrok_url}")
            return ngrok_url
        else:
            print("Failed to create ngrok tunnel.")
            return None
    except:
        print("An error occurred while creating ngrok tunnel.")
        return None


def remove_existing_webhooks(repo_owner, repo_name, github_token):
    """
    Removes any existing webhooks from the specified repository.

    Args:
        repo_owner (str): The owner or organization of the GitHub repository.
        repo_name (str): The name of the GitHub repository.
        github_token (str): The personal access token with the necessary permissions to manage webhooks.
    """
    # GitHub API endpoint for listing webhooks
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/hooks"

    # Set the headers for the API request
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Send a GET request to retrieve the list of webhooks
    response = requests.get(api_url, headers=headers)

    # Check the response status code
    if response.status_code == 200:
        webhooks = response.json()

        # Iterate over each webhook and delete it
        for webhook in webhooks:
            webhook_id = webhook["id"]
            delete_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/hooks/{webhook_id}"
            delete_response = requests.delete(delete_url, headers=headers)

            if delete_response.status_code == 204:
                print(f"Webhook with ID {webhook_id} deleted successfully.")
            else:
                print(
                    f"Failed to delete webhook with ID {webhook_id}. Status code: {delete_response.status_code}"
                )
    else:
        print(
            f"Failed to retrieve webhooks. Status code: {response.status_code}"
        )


def set_github_webhook(repo_owner, repo_name, webhook_url, github_token):
    """
    Sets up a GitHub webhook for the specified repository using the provided webhook URL and GitHub token.

    Args:
        repo_owner (str): The owner or organization of the GitHub repository.
        repo_name (str): The name of the GitHub repository.
        webhook_url (str): The URL of the webhook endpoint.
        github_token (str): The personal access token with the necessary permissions to create webhooks.
    """
    # GitHub API endpoint for creating webhooks
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/hooks"

    # Set the headers for the API request
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Set the payload for creating the webhook
    payload = {
        "name":
        "web",
        "active":
        True,
        "events": [
            "issues", "issue_comment", "pull_request",
            "pull_request_review_comment", "push", "release", "fork", "watch"
        ],
        "config": {
            "url": webhook_url,
            "content_type": "json"
        }
    }

    # Send a POST request to create the webhook
    response = requests.post(api_url, json=payload, headers=headers)

    # Check the response status code
    if response.status_code == 201:
        print("Webhook created successfully!")
    else:
        print(f"Failed to create webhook. Status code: {response.status_code}")
        print(f"Response content: {response.text}")


if __name__ == "__main__":
    """
    Main entry point of the script.
    Reads the required parameters from environment variables and sets up a GitHub webhook.
    """
    # Read the required parameters from environment variables
    repo_owner = os.environ.get("REPO_OWNER")
    repo_name = os.environ.get("REPO_NAME")
    webhook_port = os.environ.get("WEBHOOK_PORT")
    webhook_endpoint = os.environ.get("WEBHOOK_ENDPOINT")
    github_token = os.environ.get("GITHUB_TOKEN")
    ngrok_web_addr = os.environ.get(
        "NGROK_WEB_ADDR")  # e.g. http://localhost:4041/api/tunnels

    # Check if all the required environment variables are set
    if repo_owner and repo_name and webhook_port and github_token:
        # Check if there is an existing ngrok tunnel
        ngrok_url = get_ngrok_url(ngrok_web_addr)

        if ngrok_url:
            print(f"Existing ngrok tunnel found. Public URL: {ngrok_url}")
        else:
            print("No existing ngrok tunnel found. Creating a new one...")
            ngrok_url = create_ngrok_tunnel(int(webhook_port))

        if ngrok_url:
            # Remove any existing webhooks
            remove_existing_webhooks(repo_owner, repo_name, github_token)

            # Call the function to set the GitHub webhook
            set_github_webhook(repo_owner, repo_name,
                               ngrok_url + webhook_endpoint, github_token)
    else:
        print("Missing required environment variables.")
