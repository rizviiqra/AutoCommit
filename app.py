from flask import Flask, request, jsonify
import os
import time
import requests
import threading # CRITICAL FIX: For non-blocking operations
from dotenv import load_dotenv

# Assuming 'generator' and 'githubcode' are in the same directory
from generator import generate_app_code
from githubcode import GitHubManager

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load configuration from environment
STUDENT_EMAIL = os.getenv('STUDENT_EMAIL')
STUDENT_SECRET = os.getenv('STUDENT_SECRET')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize GitHub manager (assuming environment variables are set)
githubcode = GitHubManager(GITHUB_TOKEN, GITHUB_USERNAME)

def verify_secret(secret):
    """Verify if the provided secret matches"""
    return secret == STUDENT_SECRET

def send_to_evaluation_url_sync(evaluation_url, payload, max_retries=5):
    """
    Synchronous function with exponential backoff designed to run in a
    separate thread, preventing the main Flask process from blocking.
    """
    delay = 1
    for attempt in range(max_retries):
        try:
            # Note: We use a longer timeout here as the evaluation server might be slow
            response = requests.post(
                evaluation_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60 # Increased timeout for slow external API
            )
            if response.status_code == 200:
                print(f"[Evaluation Thread] Success: Sent to evaluation URL: {evaluation_url}")
                return True
            else:
                print(f"[Evaluation Thread] Warning: Evaluation URL returned {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[Evaluation Thread] Error sending to evaluation URL (attempt {attempt + 1}): {str(e)}")
        
        if attempt < max_retries - 1:
            print(f"[Evaluation Thread] Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
    
    print(f"[Evaluation Thread] FAILED to send to evaluation URL after {max_retries} attempts.")
    return False

def start_evaluation_thread(evaluation_url, payload):
    """Starts the evaluation call in a non-blocking thread."""
    thread = threading.Thread(target=send_to_evaluation_url_sync, args=(evaluation_url, payload))
    thread.daemon = True # Allows the thread to exit when the main program exits
    thread.start()
    print("Evaluation POST dispatched to a separate, non-blocking thread.")

@app.route('/api-endpoint', methods=['POST'])
def handle_request():
    """Main endpoint to handle build and revision requests"""
    try:
        data = request.json
        if not data:
             return jsonify({'error': 'No JSON payload provided'}), 400

        # --- Robust Input Validation ---
        required_fields = ['secret', 'email', 'task', 'brief', 'evaluation_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

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
        print(f"Brief: {brief[:50]}...")
        print(f"{'='*50}\n")
        
        # Generate unique repo name based on task (sanitized)
        repo_name = task.replace('/', '-').replace(' ', '-').lower() 
        
        is_revision = round_num > 1
        
        # --- 1. Generate App Code ---
        print(f"Generating {'updated' if is_revision else 'initial'} app code with LLM (including any attachments)...")
        app_code = generate_app_code(
            brief=brief, 
            checks=checks, 
            attachments=attachments, 
            api_key=GEMINI_API_KEY, 
            is_revision=is_revision
        )
        
        # --- 2. Prepare README Content ---
        readme_sections = [
            f"# {task}",
            f"## Description\n{brief}",
            f"## Requirements\n{chr(10).join(f'- {check}' for check in checks)}",
            f"## Usage\nOpen the deployed GitHub Pages URL in your browser.",
            f"## Code Explanation\nThis application was generated and {'updated' if is_revision else 'created'} to fulfill the requirements specified in the brief.",
            f"## License\nMIT License - See LICENSE file for details"
        ]
        
        if is_revision:
            readme_sections.insert(4, "## Recent Updates\nThis application has been updated to meet additional requirements in Round 2.")
            
        readme_content = '\n\n'.join(readme_sections)

        # --- 3. Deploy/Update GitHub ---
        if not is_revision:
            # Round 1: Build and Deploy
            repo_url, commit_sha, pages_url = githubcode.create_and_deploy_repo(
                repo_name=repo_name,
                app_code=app_code,
                readme_content=readme_content
            )
        else:
            # Round 2: Revise and Update
            repo_url, commit_sha, pages_url = githubcode.update_repo(
                repo_name=repo_name,
                app_code=app_code,
                readme_content=readme_content
            )
            
        print(f"Deployment complete. Pages URL: {pages_url}")
        
        # --- 4. Prepare and Send Evaluation Payload (Asynchronously) ---
        eval_payload = {
            'email': email,
            'task': task,
            'round': round_num,
            'nonce': nonce,
            'repo_url': repo_url,
            'commit_sha': commit_sha,
            'pages_url': pages_url
        }
        
        # Start the non-blocking thread for the evaluation call
        start_evaluation_thread(evaluation_url, eval_payload)
        
        # Return success response immediately (HTTP 200 required by project spec)
        return jsonify({
            'status': 'success',
            'message': f'Round {round_num} completed and evaluation initiated.',
            'repo_url': repo_url,
            'commit_sha': commit_sha,
            'pages_url': pages_url
        }), 200
        
    except Exception as e:
        print(f"FATAL ERROR processing request: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # Verify environment variables are set before starting the server
    required_vars = ['STUDENT_EMAIL', 'STUDENT_SECRET', 'GITHUB_TOKEN', 
                     'GITHUB_USERNAME', 'GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        exit(1)
    
    print(f"Starting Flask app for student: {STUDENT_EMAIL}")
    app.run(host='0.0.0.0', port=5000, debug=True)
