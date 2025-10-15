# generator.py
import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initializing OpenAI Client
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    print(f"FATAL: Could not initialize OpenAI client. Error: {e}")
    client = None

def decode_attachment(data_uri):

    # Decodes a Base64 Data URI into its content.
    try:
        # Find the Base64 part after the last comma
        _, encoded_data = data_uri.rsplit(',', 1)
        decoded_bytes = base64.b64decode(encoded_data)
        # Try decoding as UTF-8, but return bytes if it fails (e.g., image)
        try:
            return decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return decoded_bytes
    except Exception as e:
        print(f"Error decoding attachment: {e}")
        return ""

def format_attachments_for_prompt(attachments):

    # Converts attachments into a human-readable format for the LLM.
    # For large files, only provide the name and type.

    if not attachments:
        return "None"

    formatted_list = []
    for att in attachments:
        name = att.get('name', 'file')
        url = att.get('url', '')
        
        # Decode and truncate content to fit within prompt limits
        content = decode_attachment(url)
        content_preview = ""

        if isinstance(content, str):
            # For text content (CSV, JSON, MD), show a snippet
            content_preview = content[:200] + ("..." if len(content) > 200 else "")
            formatted_list.append(f"File Name: {name}\nContent Type: TEXT\nContent Preview:\n---\n{content_preview}\n---")
        else:
            # For binary content (PNG), just note the type
            content_preview = f"(Binary content: {len(content)} bytes)"
            formatted_list.append(f"File Name: {name}\nContent Type: BINARY\nContent Preview:\n---\n{content_preview}\n---")
            
    return "\n\n".join(formatted_list)


SYSTEM_PROMPT = """
You are an expert full-stack developer specializing in generating minimal, single-page web applications.
Your response MUST be a single JSON object containing three keys: 'index.html', 'README.md', and 'LICENSE'.

**CONSTRAINTS & REQUIREMENTS:**
1.  **Format:** Output ONLY a single JSON object. Do not include markdown formatting outside the JSON block.
2.  **App:** The application must be a single 'index.html' file using plain JavaScript/HTML/CSS, or Bootstrap/CDN libraries if required by the brief.
3.  **Attachments:** If attachments are provided, they are Base64 Data URIs. Embed them directly into the JavaScript code using the full Data URI string where needed (e.g., for `fetch` or image sources).
4.  **License:** The 'LICENSE' file MUST contain the standard MIT License text.
5.  **README:** The 'README.md' must be professional, complete, and include a **Summary**, **Setup (None required)**, **Usage**, and **Code Explanation**.
6.  **Code Quality:** The code must be minimal, clean, and avoid embedding secrets.
"""

def generate_app_files(brief, attachments, round_num, output_path):
    """
    Generates application files using the LLM and writes them to the output path.
    """
    if not client:
        # If client failed to initialize, create dummy files to at least test deployment
        print("LLM client not initialized. Creating dummy files.")
        create_dummy_files(brief, output_path)
        return

    # 1. Prepare Prompt
    formatted_attachments = format_attachments_for_prompt(attachments)
    
    USER_PROMPT = f"""
    TASK BRIEF (Round {round_num}):
    {brief}

    ATTACHMENTS:
    {formatted_attachments}

    Based on the brief and attachments, generate the three files required. 
    """
    
    # 2. Call LLM
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Use a capable model
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT},
            ],
            response_format={"type": "json_object"}
        )
        
        # 3. Parse JSON Output
        generated_json_text = response.choices[0].message.content
        file_contents = json.loads(generated_json_text)

        # 4. Write Files to Disk
        for filename, content in file_contents.items():
            file_path = os.path.join(output_path, filename)
            
            # Ensure index.html and README.md are strings
            if isinstance(content, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Wrote file: {filename}")
            else:
                # Handle potential non-string output if LLM messes up
                print(f"ERROR: Content for {filename} was not a string.")


    except Exception as e:
        print(f"FATAL LLM GENERATION ERROR: {e}")
        # Fallback if LLM fails
        create_dummy_files(brief, output_path)


# Fallback/Bootstrap function for testing or failure
def create_dummy_files(brief, output_path):
    """Creates minimal files when LLM generation fails or is skipped."""
    with open(os.path.join(output_path, 'index.html'), 'w') as f:
        f.write(f"<!DOCTYPE html><html><head><title>Fallback App</title></head><body><h1>Task Failed/Skipped: {brief[:50]}...</h1></body></html>")
    
    with open(os.path.join(output_path, 'README.md'), 'w') as f:
        f.write("# Fallback App\n\nThis is a placeholder README due to a generation failure.")
        
    with open(os.path.join(output_path, 'LICENSE'), 'w') as f:
        f.write("The MIT License (MIT)\n...") # Minimal MIT