from github import Github, GithubException
import time

class GitHubManager:
    def __init__(self, token, username):
        """Initialize GitHub manager with token and username"""
        self.github = Github(token)
        self.user = self.github.get_user()
        self.username = username
        
    def create_and_deploy_repo(self, repo_name, app_code, readme_content):
        """
        Create a new GitHub repository and deploy to GitHub Pages
        Returns: (repo_url, commit_sha, pages_url)
        """
        try:
            # Create repository
            print(f"Creating repository: {repo_name}")
            repo = self.user.create_repo(
                repo_name,
                description="Auto-generated application",
                private=False,
                auto_init=False
            )
            
            # Wait a moment for repo to be ready
            time.sleep(2)
            
            # Create MIT LICENSE
            mit_license = """MIT License

Copyright (c) 2025

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
            
            # Create files in the repository
            print("Creating LICENSE file...")
            repo.create_file("LICENSE", "Add MIT License", mit_license)
            
            print("Creating README.md...")
            repo.create_file("README.md", "Add README", readme_content)
            
            print("Creating index.html...")
            commit = repo.create_file("index.html", "Add application code", app_code)
            commit_sha = commit['commit'].sha
            
            # Enable GitHub Pages
            print("Enabling GitHub Pages...")
            self._enable_github_pages(repo)
            
            # Construct URLs
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
        Update an existing GitHub repository
        Returns: (repo_url, commit_sha, pages_url)
        """
        try:
            # Get existing repository
            print(f"Getting repository: {repo_name}")
            repo = self.user.get_repo(repo_name)
            
            # Update README.md
            print("Updating README.md...")
            readme_file = repo.get_contents("README.md")
            repo.update_file(
                "README.md",
                "Update README for Round 2",
                readme_content,
                readme_file.sha
            )
            
            # Update index.html
            print("Updating index.html...")
            index_file = repo.get_contents("index.html")
            commit = repo.update_file(
                "index.html",
                "Update application for Round 2",
                app_code,
                index_file.sha
            )
            commit_sha = commit['commit'].sha
            
            # Construct URLs
            repo_url = repo.html_url
            pages_url = f"https://{self.username}.github.io/{repo_name}/"
            
            print(f"Repository updated successfully: {repo_url}")
            print(f"Pages URL: {pages_url}")
            print("Note: GitHub Pages may take 1-2 minutes to redeploy")
            
            return repo_url, commit_sha, pages_url
            
        except GithubException as e:
            print(f"GitHub API error: {e.status} - {e.data}")
            raise Exception(f"Failed to update repository: {str(e)}")
        except Exception as e:
            print(f"Error updating repository: {str(e)}")
            raise
    
    def _enable_github_pages(self, repo):
        """Enable GitHub Pages for a repository"""
        try:
            # GitHub Pages API endpoint
            # We'll use the REST API directly since PyGithub doesn't have full Pages support
            import requests
            
            url = f"https://api.github.com/repos/{self.username}/{repo.name}/pages"
            headers = {
                "Authorization": f"token {self.github._Github__requester.auth.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "source": {
                    "branch": "main",
                    "path": "/"
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 201:
                print("GitHub Pages enabled successfully")
            elif response.status_code == 409:
                print("GitHub Pages already enabled")
            else:
                print(f"Warning: Could not enable GitHub Pages. Status: {response.status_code}")
                print(f"Response: {response.text}")
                # Try updating instead
                response = requests.put(url, json=data, headers=headers)
                if response.status_code == 200:
                    print("GitHub Pages updated successfully")
            
            # Wait for pages to be ready
            time.sleep(5)
            
        except Exception as e:
            print(f"Warning: Could not enable GitHub Pages: {str(e)}")
            print("You may need to enable it manually in the repository settings")
