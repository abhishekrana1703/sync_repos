import os
import subprocess
import requests
import logging
from datetime import datetime

# Constants
GITLAB_TOKEN = "glpat-o2rV5ywVfSLMcvSSqEsx"
GITHUB_TOKEN = "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"
REPOS_FILE = "repos.txt"
LOG_DIR = "sync_logs"

# Set up logging
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(filename=os.path.join(LOG_DIR, f"sync_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def validate_token(token, service):
    """Check if the token is valid for the given service."""
    if service == 'gitlab':
        url = "https://gitlab.com/api/v4/user"
        headers = {'Private-Token': token}
    elif service == 'github':
        url = "https://api.github.com/user"
        headers = {'Authorization': f'token {token}'}
    else:
        logging.error("Unsupported service for token validation.")
        return False

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.info(f"{service.capitalize()} token is valid.")
        return True
    else:
        logging.error(f"{service.capitalize()} token is invalid: {response.text}")
        return False

def get_repo_list(file_path):
    """Read the repository pairs from the repos.txt file."""
    with open(file_path, 'r') as file:
        return [line.strip().split(',') for line in file.readlines()]

def get_gitlab_project_id(gitlab_repo):
    """Retrieve the project ID from the GitLab repository."""
    project_name = gitlab_repo.split('/')[-1].replace('.git', '')
    url = f"https://gitlab.com/api/v4/projects/{gitlab_repo.replace('/', '%2F')}"  # URL-encode the path
    headers = {'Private-Token': GITLAB_TOKEN}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()['id']  # Return the project ID
    else:
        logging.error(f"Failed to fetch project ID from GitLab repo {gitlab_repo}, status code: {response.status_code}, response: {response.text}")
        return None

def has_new_commits(gitlab_repo):
    """Check for new commits in the GitLab repository."""
    project_id = get_gitlab_project_id(gitlab_repo)
    
    if project_id is None:
        return False, None  # Project ID retrieval failed

    url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/commits"
    headers = {'Private-Token': GITLAB_TOKEN}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commits = response.json()
        return len(commits) > 0, commits[0]['id'] if commits else None
    else:
        logging.error(f"Error checking commits for {gitlab_repo}: {response.text}")
        return False, None

def sync_commit(gitlab_repo, github_repo):
    """Sync the latest commit from GitLab to GitHub."""
    # Clone the GitLab repository
    subprocess.run(["git", "clone", f"https://{GITLAB_TOKEN}:x-oauth-basic@gitlab.com/{gitlab_repo}.git"], check=True)

    # Change directory to the cloned repository
    repo_name = gitlab_repo.split('/')[-1]
    os.chdir(repo_name)

    # Push to GitHub
    subprocess.run(["git", "push", f"https://{GITHUB_TOKEN}:x-oauth-basic@{github_repo}"], check=True)

    # Change back to the previous directory
    os.chdir('..')

    # Remove the cloned repository
    subprocess.run(["rm", "-rf", repo_name])

def main():
    # Validate tokens
    if not validate_token(GITLAB_TOKEN, 'gitlab') or not validate_token(GITHUB_TOKEN, 'github'):
        return

    # Get the list of repositories
    repo_pairs = get_repo_list(REPOS_FILE)
    logging.info(f"Found {len(repo_pairs)} repositories to sync.")

    for gitlab_repo, github_repo in repo_pairs:
        logging.info(f"Checking for new commits in {gitlab_repo}...")

        new_commits, latest_commit_id = has_new_commits(gitlab_repo)

        if new_commits:
            logging.info(f"New commits found in {gitlab_repo}. Syncing to {github_repo}...")
            sync_commit(gitlab_repo, github_repo)
            logging.info(f"Successfully synced {gitlab_repo} to {github_repo}.")
        else:
            logging.info(f"No new commits in {gitlab_repo}.")

if __name__ == "__main__":
    main()
