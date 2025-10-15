import os
import time
import requests
import json
import shutil
from githubapi import create_and_push_repo, enable_github_pages
from generator import generate_app_files

# Configuration
TEMP_DIR = "temp_repos"
MAX_RETRIES = 5 

def post_evaluation_ping(payload, url):
    
    # 1, 2, 4, 8, 16 seconds delay
    delays = [2**i for i in range(MAX_RETRIES)] 

    for delay in delays:
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"SUCCESS: Evaluation ping sent for task {payload['task']} (Round {payload['round']})")
                return True
            else:
                print(f"WARNING: Ping failed with status {response.status_code}. Retrying in {delay}s...")
        except requests.RequestException as e:
            print(f"ERROR: Failed to connect to evaluation URL. Retrying in {delay}s. Error: {e}")
        
        # Only sleep if it wasn't the last attempt
        if delay != delays[-1]:
            time.sleep(delay)
            
    print(f"FATAL: Evaluation ping failed after {MAX_RETRIES} attempts.")
    return False

def handle_task(data):

    # This runs in a background thread.
    
    # Parsing requested data
    email = data.get("email")
    task_id = data.get("task")
    round_num = data.get("round")
    nonce = data.get("nonce")
    brief = data.get("brief")
    attachments = data.get("attachments", [])
    evaluation_url = data.get("evaluation_url")
    
    repo_name = f"{task_id}"
    local_repo_path = os.path.join(TEMP_DIR, repo_name)
    
    # Clean up previous local instance if it exists
    if os.path.exists(local_repo_path):
        shutil.rmtree(local_repo_path)
    os.makedirs(local_repo_path, exist_ok=True)

    try:
        # 1. LLM Generation
        print("Generating app files with LLM...")
        # The generate_app_files function will create index.html, README.md, LICENSE
        # in the local_repo_path directory.
        generate_app_files(brief, attachments, round_num, local_repo_path)
        
        # 2. GitHub Build & Deploy
        print("Creating repo and pushing to GitHub...")
        # This function returns the metadata needed for the ping
        repo_metadata = create_and_push_repo(repo_name, local_repo_path, round_num)
        
        if not repo_metadata:
            print("FATAL: GitHub deployment failed.")
            return

        # 3. Enable GitHub Pages
        print("Enabling GitHub Pages and verifying reachability...")
        pages_url = enable_github_pages(repo_name, repo_metadata['repo_url'])
        
        if not pages_url:
             print("FATAL: GitHub Pages verification failed.")
             return
        
        # 4. Final Evaluation Ping
        final_payload = {
            "email": email,
            "task": task_id,
            "round": round_num,
            "nonce": nonce,
            "repo_url": repo_metadata['repo_url'],
            "commit_sha": repo_metadata['commit_sha'],
            "pages_url": pages_url
        }
        
        post_evaluation_ping(final_payload, evaluation_url)
        
    except Exception as e:
        print(f"FATAL ERROR in task handler for {task_id}: {e}")
    finally:
        # 5. Cleanup
        print(f"Cleaning up local directory: {local_repo_path}")
        shutil.rmtree(local_repo_path)