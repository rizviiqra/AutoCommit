
import os
import time
import requests
from github import Github, GithubException
from dotenv import load_dotenv

# Configuration
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
PAGES_BASE_URL = f"https://{GITHUB_USERNAME}.github.io/"

# Initialize PyGithub client
try:
    g = Github(GITHUB_TOKEN)
except Exception as e:
    print(f"FATAL: Could not initialize GitHub client. Check GITHUB_TOKEN. Error: {e}")
    g = None

def create_and_push_repo(repo_name, local_repo_path, round_num):

    # Creates a new public repo, commits files, and pushes to GitHub.
    # Returns repo metadata on success.

    if not g: return None

    repo_url = f"https://github.com/{GITHUB_USERNAME}/{repo_name}"
    print(f"Attempting to create and push to: {repo_url}")

    try:
        # 1. Create Repository (Public)
        repo = g.get_user().create_repo(
            repo_name,
            description=f"LLM-generated app for task {repo_name} (Round {round_num})",
            private=False,
            auto_init=False
        )
        print(f"Repository '{repo_name}' created successfully.")

        # using shell commands
        os.system(f"git init {local_repo_path}")
        os.system(f"cd {local_repo_path} && git add .")
        os.system(f"cd {local_repo_path} && git commit -m 'Initial LLM-generated commit (Round {round_num})'")
        os.system(f"cd {local_repo_path} && git branch -M main")
        os.system(f"cd {local_repo_path} && git remote add origin {repo_url}.git")
        os.system(f"cd {local_repo_path} && git push -u origin main")
        
        # 2. Get Commit SHA
        # Fetch the latest commit SHA after the push
        latest_commit = repo.get_branch("main").commit.sha
        
        return {
            'repo_url': repo.html_url,
            'commit_sha': latest_commit
        }

    except GithubException as e:
        print(f"GitHub API Error during creation/push: {e}")
        return None
    except Exception as e:
        print(f"Local Git CLI Error: {e}")
        return None

def enable_github_pages(repo_name, repo_url):
    # Enables GitHub Pages for the repository and checks for 200 OK status.
    # Returns the pages URL on success.

    if not g: return None
    
    pages_url = f"{PAGES_BASE_URL}{repo_name}/"
    
    try:
        repo = g.get_repo(f"{GITHUB_USERNAME}/{repo_name}")
        
        # 1. Enable Pages (serving from the 'main' branch)
        repo.enable_pages(
            source={"branch": "main", "path": "/"}, 
            cname=None
        )
        print("GitHub Pages enabled. Waiting for deployment...")

        # 2. Verify Pages reachability (can take a few seconds)
        max_attempts = 10
        for attempt in range(max_attempts):
            time.sleep(5) # Wait 5 seconds between checks
            try:
                # Check the site directly
                response = requests.get(pages_url)
                if response.status_code == 200:
                    print(f"Pages is reachable (200 OK) at: {pages_url}")
                    return pages_url
                else:
                    print(f"Attempt {attempt+1}/{max_attempts}: Pages status {response.status_code}. Retrying...")
            except requests.RequestException:
                print(f"Attempt {attempt+1}/{max_attempts}: Connection error. Retrying...")
        
        print(f"FATAL: Pages did not become reachable after {max_attempts} attempts.")
        return None
        
    except GithubException as e:
        print(f"GitHub API Error during Pages setup: {e}")
        return None
    except Exception as e:
        print(f"General error during Pages setup: {e}")
        return None