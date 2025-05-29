import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import openai

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

# Limit content to ~6,000 tokens (~24,000 chars) to stay under 80K TPM
MAX_CONTENT_CHARS = 24000

@app.route('/')
def home():
    return "Content Assessment Backend is running."

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        persona = request.form.get('persona', '')
        stage = request.form.get('stage', '')

        filename = secure_filename(file.filename)
        content_bytes = file.read()

        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            content = content_bytes.decode('latin-1')  # fallback encoding

        if len(content) > MAX_CONTENT_CHARS:
            content = content[:MAX_CONTENT_CHARS]

        prompt = f"""
You are a B2B marketing strategist assessing a piece of content based on the following rubric:

1. Relevance to buyer stage: {stage}
2. Alignment with target persona: {persona}
3. Clarity, structure, and tone
4. Differentiation and value proposition
5. Call to action
6. Engagement and design quality (if applicable)

Evaluate the content and for each category:
- Give a score from 1 to 5
- Justify the score with a short rationale
- Suggest 1–2 steps for improvement

Content to assess:
\"\"\"
{content}
\"\"\"
"""

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )

        result = response.choices[0].message.content.strip()
        return jsonify({'analysis': result})

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)