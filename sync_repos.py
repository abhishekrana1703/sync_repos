import os
import subprocess
import concurrent.futures
import time

# GitLab and GitHub tokens for authentication
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')  # GitLab token should be passed as environment variable
GITHUB_TOKEN = os.getenv('GH_TOKEN')  # GitHub token should be passed as environment variable

# File containing GitLab and GitHub repository pairs
REPO_FILE = 'repos.txt'

# Max retries for failed syncs
MAX_RETRIES = 3

# Max workers for parallel execution (adjust based on your system’s resources)
MAX_WORKERS = 10

# Logging failed syncs
failed_repos = []

def sync_repo(gitlab_url, github_url, attempt=1):
    repo_name = gitlab_url.split('/')[-1].replace('.git', '')
    
    try:
        # Clone GitLab repository with token
        if os.path.exists(repo_name):
            subprocess.run(['rm', '-rf', repo_name])

        gitlab_url_with_token = gitlab_url.replace(
            'https://gitlab.com', f'https://oauth2:{GITLAB_TOKEN}@gitlab.com'
        )

        print(f"Cloning {repo_name} from GitLab (Attempt {attempt})...")
        subprocess.run(['git', 'clone', gitlab_url_with_token], check=True)

        os.chdir(repo_name)

        # Modify GitHub URL to include the GitHub token for authentication
        github_url_with_token = github_url.replace(
            'https://github.com', f'https://{GITHUB_TOKEN}:x-oauth-basic@github.com'
        )

        # Add GitHub remote with token for authentication
        subprocess.run(['git', 'remote', 'add', 'github', github_url_with_token], check=True)

        # Fetch and sync
        print(f"Fetching from GitLab and pushing to GitHub for {repo_name}...")
        subprocess.run(['git', 'fetch', 'origin'], check=True)
        subprocess.run(['git', 'push', '--mirror', 'github'], check=True)

        # Clean up
        os.chdir('..')
        subprocess.run(['rm', '-rf', repo_name])
        print(f"Synced {repo_name} successfully!\n")
    except subprocess.CalledProcessError as e:
        print(f"Error syncing {repo_name} (Attempt {attempt}): {str(e)}")
        
        if attempt < MAX_RETRIES:
            print(f"Retrying {repo_name}...")
            time.sleep(5)  # Add a short delay before retry
            sync_repo(gitlab_url, github_url, attempt + 1)
        else:
            print(f"Failed to sync {repo_name} after {MAX_RETRIES} attempts.")
            failed_repos.append(f"{gitlab_url},{github_url}")
    finally:
        if os.path.exists(repo_name):
            os.chdir('..')
            subprocess.run(['rm', '-rf', repo_name])


def main():
    # Read repo file
    with open(REPO_FILE, 'r') as f:
        repos = f.readlines()

    repo_pairs = [(repo.strip().split(',')[0], repo.strip().split(',')[1]) for repo in repos]

    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(sync_repo, gitlab_url, github_url) for gitlab_url, github_url in repo_pairs]

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # This will raise an exception if sync_repo raised one
            except Exception as exc:
                print(f"Generated an exception: {exc}")

    # Log failed repositories
    if failed_repos:
        with open('failed_repos.txt', 'w') as fail_log:
            fail_log.write("\n".join(failed_repos))
        print(f"{len(failed_repos)} repositories failed to sync. See 'failed_repos.txt' for details.")
    else:
        print("All repositories synced successfully!")


if __name__ == '__main__':
    main()
