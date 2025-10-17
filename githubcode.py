from github import Github, GithubException
import time
import requests # Need to import requests here for the Pages API call

class GitHubManager:
    def __init__(self, token, username):
        """Initialize GitHub manager with token and username"""
        self.github = Github(token)
        self.user = self.github.get_user()
        self.username = username
        self.default_branch = "main" # Standard branch name

    def create_and_deploy_repo(self, repo_name, app_code, readme_content):
        """
        Create a new GitHub repository and deploy to GitHub Pages.
        Returns: (repo_url, commit_sha, pages_url)
        """
        try:
            # 1. Create repository
            print(f"Creating public repository: {repo_name}")
            repo = self.user.create_repo(
                repo_name,
                description="Auto-generated application",
                private=False, # Required to be public
                auto_init=False
            )
            
            # 2. Add files
            time.sleep(1) # Wait a moment for repo to be ready
            
            # MIT LICENSE content
            mit_license = f"""MIT License

Copyright (c) 2025 {self.username}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
            
            # Create files directly on the default branch (main)
            print("Creating LICENSE file...")
            repo.create_file("LICENSE", "Add MIT License", mit_license, branch=self.default_branch)
            
            print("Creating README.md...")
            repo.create_file("README.md", "Add README", readme_content, branch=self.default_branch)
            
            print("Creating index.html...")
            commit = repo.create_file("index.html", "Initial application code", app_code, branch=self.default_branch)
            commit_sha = commit['commit'].sha
            
            # 3. Enable GitHub Pages
            print(f"Enabling GitHub Pages from the '{self.default_branch}' branch...")
            self._enable_github_pages(repo, self.default_branch)
            
            # 4. Construct URLs
            repo_url = repo.html_url
            pages_url = f"https://{self.username}.github.io/{repo_name}/"
            
            print(f"Repository created successfully: {repo_url}")
            print(f"Pages will be available at: {pages_url}")
            print("Note: GitHub Pages may take 1-2 minutes to deploy")
            
            return repo_url, commit_sha, pages_url
            
        except GithubException as e:
            print(f"GitHub API error: {e.status} - {e.data}")
            raise Exception(f"Failed to create repository: {str(e)}")
        except Exception as e:
            print(f"Error creating repository: {str(e)}")
            raise

    
    def update_repo(self, repo_name, app_code, readme_content):
        """
        Update an existing GitHub repository for the revision round.
        Returns: (repo_url, commit_sha, pages_url)
        """
        try:
            # 1. Get existing repository
            print(f"Getting repository: {repo_name}")
            repo = self.user.get_repo(repo_name)

            # 2. Define the list of files to update/create
            files_to_update = {
                "README.md": ("Update README for Round 2", readme_content),
                "index.html": ("Update application for Round 2", app_code)
            }
            
            latest_commit = None
            
            # 3. Iterate through files and update/create as necessary (Robustness fix)
            for path, (message, content) in files_to_update.items():
                print(f"Processing {path}...")
                try:
                    # Try to get contents (file exists)
                    file_content = repo.get_contents(path, ref=self.default_branch)
                    
                    # Update existing file
                    commit = repo.update_file(
                        path,
                        message,
                        content,
                        file_content.sha,
                        branch=self.default_branch
                    )
                    latest_commit = commit
                    print(f"  -> Successfully updated {path}")
                    
                except GithubException as e:
                    # If file not found (404), create it
                    if e.status == 404:
                        print(f"  -> File {path} not found, creating it...")
                        commit = repo.create_file(
                            path,
                            message,
                            content,
                            branch=self.default_branch
                        )
                        latest_commit = commit
                        print(f"  -> Successfully created {path}")
                    else:
                        raise # Re-raise other GitHub errors

            if latest_commit is None:
                raise Exception("No changes were committed to the repository. Update failed.")

            commit_sha = latest_commit['commit'].sha
            
            # 4. Construct URLs (Pages URL should be the same, but confirm commit)
            repo_url = repo.html_url
            pages_url = f"https://{self.username}.github.io/{repo_name}/"
            
            print(f"Repository updated successfully. New Commit SHA: {commit_sha}")
            print("Note: GitHub Pages may take 1-2 minutes to redeploy")
            
            return repo_url, commit_sha, pages_url
            
        except GithubException as e:
            print(f"GitHub API error: {e.status} - {e.data}")
            raise Exception(f"Failed to update repository: {str(e)}")
        except Exception as e:
            print(f"Error updating repository: {str(e)}")
            raise
    
    def _enable_github_pages(self, repo, branch_name):
        """Enable or update GitHub Pages for a repository using the REST API."""
        
        # NOTE: We use the REST API as PyGithub Pages integration is often incomplete.
        url = f"https://api.github.com/repos/{self.username}/{repo.name}/pages"
        
        # Token format for PyGithub internal authentication is a private attribute,
        # but the token used for the PyGithub object is the one passed to the constructor.
        # We ensure 'requests' is imported at the top of the file for this to work.
        headers = {
            "Authorization": f"token {self.github._Github__requester.auth.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "source": {
                "branch": branch_name,
                "path": "/"
            }
        }
        
        # Attempt 1: POST (Create Pages configuration)
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 201:
            print("GitHub Pages enabled successfully (POST 201)")
            
        elif response.status_code == 409:
            # Conflict (Pages already exists)
            print("GitHub Pages already exists (409 Conflict). Attempting to update configuration.")
            
            # Attempt 2: PUT (Update Pages configuration)
            response = requests.put(url, json=data, headers=headers)
            
            if response.status_code == 200:
                print("GitHub Pages configuration updated successfully (PUT 200)")
            else:
                print(f"Warning: Failed to update GitHub Pages configuration. Status: {response.status_code}")
                print(f"Response: {response.text}")
                
        else:
            print(f"Warning: Could not enable GitHub Pages (initial POST failed). Status: {response.status_code}")
            print(f"Response: {response.text}")

        # Adding a short delay to allow GitHub internal processes to start
        time.sleep(3)

