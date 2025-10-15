
import json
import os
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Importing the core handler function
from taskhandler import handle_task 

# SETUP
load_dotenv()
app = Flask(__name__)
STUDENT_SECRET = os.getenv("STUDENT_SECRET")

# The API ENDPOINT
@app.route('/api-endpoint', methods=['POST'])
def receive_request():
    # Accepts the task request, verifies the secret, and returns HTTP 200 immediately. 
    try:
        data = request.get_json()
    except Exception as e:
        # Invalid JSON payload
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    # 1. Verifying Secret
    if data.get("secret") != STUDENT_SECRET:
        print(f"ERROR: Secret mismatch for email: {data.get('email')}")
        return jsonify({"status": "error", "message": "Unauthorized: Secret mismatch"}), 401

    # round 1
    task_id = data.get("task", "unknown")
    round_num = data.get("round", 0)
    print(f"SUCCESS: Received task {task_id}, Round {round_num}. Starting background process.")

    # 2. Starting Background Task (to avoid API timeout)
    thread = threading.Thread(target=handle_task, args=(data,))
    thread.start()

    # 3. HTTP 200 Response
    return jsonify({
        "status": "received",
        "message": "Task accepted and processing in background."
    }), 200

# Run Server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# Create a temporary file to hold the main logic for now
with open('task_handler.py', 'w') as f:
    f.write('def handle_task(data):\n    print(f"Handling task {data.get("task")}")\n    # The main logic will go here\n    pass')