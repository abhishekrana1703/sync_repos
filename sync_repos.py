import os
import subprocess
import time

# Hardcoded tokens
GITLAB_TOKEN = "glpat-o2rV5ywVfSLMcvSSqEsx"  # Your GitLab token
GITHUB_TOKEN = "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"  # Your GitHub token

# File containing repository URLs
REPO_FILE = 'repos.txt'
FAILED_REPOS_FILE = 'failed_repos.txt'


def sync_repository(gitlab_url, github_url):
    """Sync a single repository from GitLab to GitHub."""
    repo_name = github_url.split('/')[-1]
    print(f'Cloning {repo_name} from GitLab...')

    # Construct GitLab and GitHub URLs with tokens for authentication
    gitlab_clone_url = f'https://oauth2:{GITLAB_TOKEN}@{gitlab_url.split("https://")[1]}'
    github_clone_url = f'https://{GITHUB_TOKEN}:x-oauth-basic@{github_url}'

    # Clone the repository from GitLab
    try:
        subprocess.run(['git', 'clone', gitlab_clone_url, repo_name], check=True)
        print(f'Fetching from GitLab and pushing to GitHub for {repo_name}...')

        # Push the repository to GitHub
        subprocess.run(['git', 'remote', 'add', 'github', github_clone_url], check=True)
        subprocess.run(['git', 'push', '--mirror', 'github'], check=True)
        print(f'Successfully synced {repo_name} to GitHub.')
    except subprocess.CalledProcessError:
        print(f'Error syncing {repo_name}. Retrying...')
        return False  # Indicate failure
    finally:
        # Clean up local repo
        subprocess.run(['rm', '-rf', repo_name])


def main():
    """Main function to read repository URLs and sync them."""
    with open(REPO_FILE, 'r') as file:
        repos = [line.strip().split(',') for line in file.readlines()]

    failed_repos = []

    for gitlab_url, github_url in repos:
        success = False
        for attempt in range(3):  # Retry up to 3 times
            if sync_repository(gitlab_url.strip(), github_url.strip()):
                success = True
                break  # Exit retry loop if successful
            time.sleep(2)  # Wait before retrying

        if not success:
            failed_repos.append(github_url.strip())

    # Log failed repositories
    if failed_repos:
        with open(FAILED_REPOS_FILE, 'w') as file:
            for repo in failed_repos:
                file.write(f'{repo}\n')
        print(f'Failed to sync {len(failed_repos)} repositories. See {FAILED_REPOS_FILE} for details.')


if __name__ == "__main__":
    main()
