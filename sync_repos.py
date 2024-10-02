import os  # Import the os module for operating system-related functionality
import subprocess  # Import the subprocess module to execute shell commands
import sys  # Import the sys module for system-specific parameters and functions

# Set GitLab and GitHub tokens
GITLAB_TOKEN = "glpat-o2rV5ywVfSLMcvSSqEsx"  # Token for GitLab authentication
GH_TOKEN = "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"  # Token for GitHub authentication

# Working directory to clone the repositories
WORK_DIR = "/tmp/sync_repos"  # Directory where repositories will be cloned

def run_command(command):
    """Run a shell command and return the output."""
    print(f"Running command: {' '.join(command)}")  # Print the command being run
    try:
        # Execute the command, capturing standard output and errors
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout  # Return the standard output from the command
    except subprocess.CalledProcessError as e:
        # Handle errors in command execution
        print(f"Command failed: {e.cmd}")  # Print the command that failed
        print(f"Error: {e.stderr}")  # Print the error message
        sys.exit(1)  # Exit the program with a non-zero status

def cleanup(repo_name):
    """Clean up any previous directories."""
    print(f"Cleaning up previous directory for {repo_name}...")  # Indicate cleanup process
    if os.path.exists(f"{WORK_DIR}/{repo_name}"):  # Check if the directory exists
        subprocess.run(["rm", "-rf", f"{WORK_DIR}/{repo_name}"])  # Remove the directory and its contents

def sync_repo(gitlab_repo, github_repo):
    """Clone from GitLab and push to GitHub."""
    repo_name = gitlab_repo.split('/')[-1].replace('.git', '')  # Extract repository name from the URL
    cleanup(repo_name)  # Clean up previous directory for the repository

    # Step 1: Clone from GitLab
    print(f"Cloning {gitlab_repo} from GitLab...")  # Indicate the cloning process
    run_command([
        "git", "clone", f"https://oauth2:{GITLAB_TOKEN}@{gitlab_repo}",  # Clone the repository using the GitLab token
        f"{WORK_DIR}/{repo_name}"  # Specify the target directory for the clone
    ])

    # Step 2: Navigate to the repository directory
    os.chdir(f"{WORK_DIR}/{repo_name}")  # Change the working directory to the cloned repository

    # Step 3: Add GitHub as a remote
    print(f"Adding GitHub as a remote for {repo_name}...")  # Indicate adding GitHub as a remote
    run_command([
        "git", "remote", "add", "github", f"https://oauth2:{GH_TOKEN}@{github_repo}"  # Add the GitHub remote using the token
    ])

    # Step 4: Force push to GitHub
    print(f"Forcing push to GitHub for {repo_name}...")  # Indicate the force push operation
    run_command(["git", "push", "--force", "github", "main"])  # Force push the main branch to GitHub

    print(f"Synchronization complete for {repo_name}!")  # Indicate completion of synchronization

def main():
    # Create the working directory if it doesn't exist
    os.makedirs(WORK_DIR, exist_ok=True)  # Create the working directory if it does not already exist

    # Read the list of repositories from the file
    with open('repos.txt', 'r') as f:  # Open the file containing the repository URLs
        repos = f.readlines()  # Read all lines from the file

    # Iterate through each line in the file
    for line in repos:
        gitlab_repo, github_repo = line.strip().split(',')  # Split the line into GitLab and GitHub repo URLs
        sync_repo(gitlab_repo, github_repo)  # Sync the repositories

if __name__ == "__main__":
    main()  # Run the main function if the script is executed directly
