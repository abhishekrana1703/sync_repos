import os
import subprocess
import concurrent.futures
import time
import logging
from datetime import datetime

# GitLab and GitHub tokens for authentication
GITLAB_TOKEN = 'your_gitlab_token'
GITHUB_TOKEN = os.getenv('GH_TOKEN')

# File containing GitLab and GitHub repository pairs
REPO_FILE = 'repos.txt'  # The file should have lines of GitLab and GitHub repository URLs separated by commas

# Max retries for failed syncs
MAX_RETRIES = 3  # Number of retry attempts for each repo in case of failure

# Max workers for parallel execution (adjust based on your system's resources)
MAX_WORKERS = 10  # Adjust the number of concurrent threads based on system performance

# Logging failed syncs
failed_repos = []  # To store any repositories that fail to sync

# Set up logging
def setup_logging():
    """Sets up logging for the script."""
    log_filename = f"repo_sync_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(filename=log_filename,
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting repository sync job...")

def sync_repo(gitlab_url, github_url, attempt=1):
    """
    Syncs a GitLab repository to GitHub.
    
    :param gitlab_url: URL of the GitLab repository
    :param github_url: URL of the GitHub repository
    :param attempt: Current retry attempt (default: 1)
    """
    # Extract repo name from GitLab URL
    repo_name = gitlab_url.split('/')[-1].replace('.git', '') 
    
    try:
        # If repo exists locally, delete it to start fresh
        if os.path.exists(repo_name):
            subprocess.run(['rm', '-rf', repo_name])  # Remove the directory if it exists
        
        logging.info(f"Cloning {repo_name} from GitLab (Attempt {attempt})...")  # Log cloning attempt
        
        # Clone GitLab repository
        subprocess.run(['git', 'clone', gitlab_url], check=True)
        
        os.chdir(repo_name)  # Change to the cloned repo directory
        
        # Add GitHub as a remote repository
        subprocess.run(['git', 'remote', 'add', 'github', github_url], check=True)
        
        # Fetch from GitLab and push to GitHub
        logging.info(f"Fetching from GitLab and pushing to GitHub for {repo_name}...")
        subprocess.run(['git', 'fetch', 'origin'], check=True)  # Fetch the latest changes from GitLab
        subprocess.run(['git', 'push', '--mirror', 'github'], check=True)  # Push all branches and tags to GitHub
        
        # Clean up: Return to the parent directory and remove the cloned repo
        os.chdir('..')
        subprocess.run(['rm', '-rf', repo_name])
        logging.info(f"Synced {repo_name} successfully!\n")  # Log successful sync
        
    except subprocess.CalledProcessError as e:
        # Log the error and retry if applicable
        logging.error(f"Error syncing {repo_name} (Attempt {attempt}): {str(e)}")
        
        # Retry if the current attempt is less than the maximum retries
        if attempt < MAX_RETRIES:
            logging.info(f"Retrying {repo_name}...")  # Log retry attempt
            time.sleep(5)  # Delay before retrying
            sync_repo(gitlab_url, github_url, attempt + 1)  # Recursive retry
        else:
            # Log failure after reaching maximum retries
            logging.error(f"Failed to sync {repo_name} after {MAX_RETRIES} attempts.")
            failed_repos.append(f"{gitlab_url},{github_url}")  # Add to the failed_repos list
    
    finally:
        # Ensure the repo is deleted if it still exists
        if os.path.exists(repo_name):
            os.chdir('..')
            subprocess.run(['rm', '-rf', repo_name])  # Clean up the cloned repo if not already done

def main():
    """
    Main function to initiate syncing of repositories.
    """
    setup_logging()  # Initialize logging for the current run

    # Read the repo file and create a list of repo pairs (GitLab and GitHub URLs)
    with open(REPO_FILE, 'r') as f:
        repos = f.readlines()  # Read all lines from the repo file
    
    # Split each line into GitLab and GitHub URL pairs
    repo_pairs = [(repo.strip().split(',')[0], repo.strip().split(',')[1]) for repo in repos]
    
    # Use ThreadPoolExecutor to sync repos in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(sync_repo, gitlab_url, github_url) for gitlab_url, github_url in repo_pairs]
        
        # Wait for all threads to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # Raises exception if any occurred during sync_repo execution
            except Exception as exc:
                logging.error(f"Generated an exception: {exc}")  # Log any exception raised
    
    # Log failed repositories
    if failed_repos:
        with open('failed_repos.txt', 'w') as fail_log:
            fail_log.write("\n".join(failed_repos))  # Write failed repos to a log file
        logging.info(f"{len(failed_repos)} repositories failed to sync. See 'failed_repos.txt' for details.")
    else:
        logging.info("All repositories synced successfully!")  # Log if all repos synced successfully

if __name__ == '__main__':
    main()  # Execute the main function
