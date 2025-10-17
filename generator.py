import google.generativeai as genai
import base64
import json

def generate_app_code(brief, checks, attachments, api_key, is_revision=False):
    """
    Generate app code using Google Gemini API based on the brief and requirements
    """
    genai.configure(api_key=api_key)
    
    # Process attachments to include in prompt
    attachment_info = ""
    if attachments:
        attachment_info = "\n\nAttachments provided:\n"
        for att in attachments:
            attachment_info += f"- {att['name']}: {att['url'][:100]}...\n"
    
    # Build the prompt
    checks_text = "\n".join(f"- {check}" for check in checks)
    
    action = "update" if is_revision else "create"
    
    prompt = f"""You are an expert web developer. {action.capitalize()} a complete, production-ready single-page web application based on these requirements:

BRIEF:
{brief}

REQUIREMENTS TO MEET:
{checks_text}
{attachment_info}

IMPORTANT INSTRUCTIONS:
1. Create a SINGLE HTML file with embedded CSS and JavaScript
2. The app must be fully functional and meet ALL requirements
3. Use modern, clean UI design with proper styling
4. Handle edge cases and errors gracefully
5. Include clear instructions in the UI if needed
6. Make it mobile-responsive
7. If attachments are provided, use them appropriately in the app
8. Add helpful comments in the code
9. The app should work immediately when opened in a browser
10. Do NOT use any external dependencies that require npm/build steps
11. You can use CDN links for libraries if absolutely necessary

Return ONLY the complete HTML code. No explanations, no markdown code blocks, just the raw HTML file content starting with <!DOCTYPE html>."""

    try:
        # Use Gemini Pro model
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Extract the generated code
        generated_code = response.text.strip()
        
        # Clean up if the model returns markdown code blocks
        if generated_code.startswith("```html"):
            generated_code = generated_code.replace("```html", "").replace("```", "").strip()
        elif generated_code.startswith("```"):
            generated_code = generated_code.replace("```", "").strip()
        
        # Ensure it starts with <!DOCTYPE html> or <html>
        if not (generated_code.lower().startswith("<!doctype") or generated_code.lower().startswith("<html")):
            generated_code = f"<!DOCTYPE html>\n{generated_code}"
        
        print(f"Generated {len(generated_code)} characters of code")
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
    <title>Application</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .brief {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: #666;
        }}
        .requirements {{
            margin-top: 20px;
        }}
        .requirements h2 {{
            color: #667eea;
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
        <h1>Application</h1>
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