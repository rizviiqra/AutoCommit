import google.generativeai as genai
from google.generativeai import types # FIXED: Changed from 'google.generativeai.types import Part'
import base64
import os
import json

def parse_attachment(attachment):
    """
    Parses a data URI attachment (e.g., data:image/png;base64,...)
    into a Gemini API Part object.
    """
    url = attachment.get('url', '')
    name = attachment.get('name', 'attachment')

    if not url.startswith("data:"):
        print(f"Warning: Attachment {name} is not a data URI. Skipping.")
        return None

    # Example: data:image/png;base64,iVBORw...
    try:
        mime_type, encoded_data = url.split(',', 1)
        mime_type = mime_type.split(':')[1].split(';')[0]
        
        # Decode the base64 data
        data_bytes = base64.b64decode(encoded_data)

        print(f"Parsed attachment: {name} ({mime_type}, {len(data_bytes)} bytes)")
        
        # FIX APPLIED HERE: Using types.Part instead of just Part
        return types.Part.from_bytes(data=data_bytes, mime_type=mime_type)

    except Exception as e:
        print(f"Error parsing attachment {name}: {str(e)}")
        return None


def generate_app_code(brief, checks, attachments, api_key, is_revision=False):
    """
    Generate app code using Google Gemini API based on the brief, requirements, and attachments.
    """
    MODEL_NAME = 'gemini-2.5-flash'
    genai.configure(api_key=api_key)
    
    # 1. Process attachments into multimodal parts
    image_parts = []
    attachment_descriptions = []
    for att in attachments:
        part = parse_attachment(att)
        if part:
            image_parts.append(part)
            attachment_descriptions.append(f"- {att['name']} (image, loaded successfully)")
    
    attachment_info = "\n\n" + "\n".join(attachment_descriptions) if attachment_descriptions else ""

    # 2. Build the text prompt
    checks_text = "\n".join(f"- {check}" for check in checks)
    action = "update" if is_revision else "create"
    
    prompt = f"""You are an expert web developer. {action.capitalize()} a complete, production-ready single-page web application based on these requirements:

BRIEF:
{brief}

REQUIREMENTS TO MEET:
{checks_text}
{attachment_info}

IMPORTANT INSTRUCTIONS:
1. Create a SINGLE HTML file with embedded CSS and JavaScript (index.html)
2. The app must be fully functional and meet ALL requirements.
3. Use the provided image attachment(s) directly in the HTML using data URIs or base64. Do NOT link to external image URLs.
4. Use modern, clean UI design with proper styling (e.g., Tailwind via CDN).
5. Make it mobile-responsive.
6. Return ONLY the complete HTML code. Do NOT include any explanations, external markdown blocks, or leading/trailing comments. The output must start with <!DOCTYPE html>."""

    # 3. Assemble all parts (text prompt must be the first element)
    contents = [prompt] + image_parts
    
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Generate content with multimodal parts
        response = model.generate_content(contents)
        
        # Extract and clean the generated code
        generated_code = response.text.strip()
        
        # Clean up if the model returns markdown code blocks
        if generated_code.startswith("```html"):
            generated_code = generated_code.replace("```html", "").replace("```", "").strip()
        elif generated_code.startswith("```"):
            generated_code = generated_code.replace("```", "").strip()
        
        # Ensure it starts with <!DOCTYPE html> or <html>
        if not (generated_code.lower().startswith("<!doctype") or generated_code.lower().startswith("<html")):
            generated_code = f"<!DOCTYPE html>\n{generated_code}"
        
        print(f"Generated {len(generated_code)} characters of code using {MODEL_NAME}")
        return generated_code
        
    except Exception as e:
        print(f"Error generating code with Gemini: {str(e)}")
        # Return a fallback simple HTML page
        return generate_fallback_html(brief, checks)

def generate_fallback_html(brief, checks):
    """
    Generate a simple fallback HTML page if LLM generation fails
    """
    checks_html = "\n".join(f"<li>{check}</li>" for check in checks)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Application Fallback</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #e0e0e0 0%, #cccccc 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            max-width: 600px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            border: 2px solid #ff5252;
        }}
        h1 {{
            color: #ff5252;
            margin-bottom: 20px;
        }}
        .brief {{
            background: #ffebee;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: #d32f2f;
        }}
        .requirements {{
            margin-top: 20px;
        }}
        .requirements h2 {{
            color: #3f51b5;
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .requirements ul {{
            list-style-position: inside;
            color: #555;
        }}
        .requirements li {{
            margin: 8px 0;
            padding-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>LLM Generation FAILED - Fallback Page</h1>
        <p>The core application logic failed to generate the required code. Displaying brief and requirements instead.</p>
        <div class="brief">
            <strong>Brief:</strong> {brief}
        </div>
        <div class="requirements">
            <h2>Requirements:</h2>
            <ul>
                {checks_html}
            </ul>
        </div>
    </div>
</body>
</html>"""
