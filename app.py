from flask import Flask, request, jsonify
import os
import time
import requests
from dotenv import load_dotenv
from generator import generate_app_code
from githubcode import GitHubManager

load_dotenv()

app = Flask(__name__)

# Load configuration from environment
STUDENT_EMAIL = os.getenv('STUDENT_EMAIL')
STUDENT_SECRET = os.getenv('STUDENT_SECRET')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize GitHub manager
githubcode = GitHubManager(GITHUB_TOKEN, GITHUB_USERNAME)

def verify_secret(secret):
    """Verify if the provided secret matches"""
    return secret == STUDENT_SECRET

def send_to_evaluation_url(evaluation_url, payload, max_retries=5):
    """Send POST request to evaluation URL with exponential backoff"""
    delay = 1
    for attempt in range(max_retries):
        try:
            response = requests.post(
                evaluation_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            if response.status_code == 200:
                print(f"Successfully sent to evaluation URL: {evaluation_url}")
                return True
            else:
                print(f"Evaluation URL returned {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Error sending to evaluation URL (attempt {attempt + 1}): {str(e)}")
        
        if attempt < max_retries - 1:
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff: 1, 2, 4, 8, 16 seconds
    
    return False

@app.route('/api-endpoint', methods=['POST'])
def handle_request():
    """Main endpoint to handle build and revision requests"""
    try:
        # Parse incoming request
        data = request.json
        
        # Verify secret
        if not verify_secret(data.get('secret')):
            return jsonify({'error': 'Invalid secret'}), 403
        
        # Extract request data
        email = data.get('email')
        task = data.get('task')
        round_num = data.get('round', 1)
        nonce = data.get('nonce')
        brief = data.get('brief')
        checks = data.get('checks', [])
        evaluation_url = data.get('evaluation_url')
        attachments = data.get('attachments', [])
        
        print(f"\n{'='*50}")
        print(f"Received request for Round {round_num}")
        print(f"Task: {task}")
        print(f"Brief: {brief}")
        print(f"{'='*50}\n")
        
        # Generate unique repo name based on task
        repo_name = task.replace('/', '-').replace(' ', '-')
        
        if round_num == 1:
            # Round 1: Build and Deploy
            print("Starting Round 1: Build and Deploy")
            
            # Generate app code using LLM
            print("Generating app code with LLM...")
            app_code = generate_app_code(brief, checks, attachments, GEMINI_API_KEY)
            
            # Create README content
            readme_content = f"""# {task}

## Description
{brief}

## Requirements
{chr(10).join(f'- {check}' for check in checks)}

## Usage
Open the deployed GitHub Pages URL in your browser.

## Code Explanation
This application was generated to fulfill the requirements specified in the brief. The code implements the requested functionality with clean, maintainable structure.

## License
MIT License - See LICENSE file for details
"""
            
            # Create GitHub repo and deploy
            print(f"Creating GitHub repo: {repo_name}")
            repo_url, commit_sha, pages_url = githubcode.create_and_deploy_repo(
                repo_name=repo_name,
                app_code=app_code,
                readme_content=readme_content
            )
            
            print(f"Repo created: {repo_url}")
            print(f"Commit SHA: {commit_sha}")
            print(f"Pages URL: {pages_url}")
            
        else:
            # Round 2: Revise and Update
            print("Starting Round 2: Revise and Update")
            
            # Generate updated app code using LLM
            print("Generating updated app code with LLM...")
            app_code = generate_app_code(brief, checks, attachments, GEMINI_API_KEY, is_revision=True)
            
            # Update README content
            readme_content = f"""# {task}

## Description
{brief}

## Requirements
{chr(10).join(f'- {check}' for check in checks)}

## Recent Updates
This application has been updated to meet additional requirements in Round 2.

## Usage
Open the deployed GitHub Pages URL in your browser.

## Code Explanation
This application was generated and updated to fulfill the requirements specified in the brief. The code implements the requested functionality with clean, maintainable structure.

## License
MIT License - See LICENSE file for details
"""
            
            # Update existing repo
            print(f"Updating GitHub repo: {repo_name}")
            repo_url, commit_sha, pages_url = githubcode.update_repo(
                repo_name=repo_name,
                app_code=app_code,
                readme_content=readme_content
            )
            
            print(f"Repo updated: {repo_url}")
            print(f"Commit SHA: {commit_sha}")
            print(f"Pages URL: {pages_url}")
        
        # Prepare payload for evaluation URL
        eval_payload = {
            'email': email,
            'task': task,
            'round': round_num,
            'nonce': nonce,
            'repo_url': repo_url,
            'commit_sha': commit_sha,
            'pages_url': pages_url
        }
        
        # Send to evaluation URL (in background to not block response)
        print(f"Sending results to evaluation URL: {evaluation_url}")
        send_to_evaluation_url(evaluation_url, eval_payload)
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': f'Round {round_num} completed successfully',
            'repo_url': repo_url,
            'commit_sha': commit_sha,
            'pages_url': pages_url
        }), 200
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # Verify environment variables are set
    required_vars = ['STUDENT_EMAIL', 'STUDENT_SECRET', 'GITHUB_TOKEN', 
                     'GITHUB_USERNAME', 'GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        exit(1)
    
    print(f"Starting Flask app for student: {STUDENT_EMAIL}")
    print(f"GitHub username: {GITHUB_USERNAME}")
    app.run(host='0.0.0.0', port=5000, debug=True)