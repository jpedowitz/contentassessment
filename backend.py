from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import traceback
from docx import Document
import fitz  # PyMuPDF
import docx2txt

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text(file):
    filename = file.filename
    if filename.endswith(".pdf"):
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            return " ".join(page.get_text() for page in doc)
    elif filename.endswith(".docx"):
        return docx2txt.process(file)
    elif filename.endswith(".txt"):
        return file.read().decode("utf-8")
    elif filename.endswith(".html"):
        return file.read().decode("utf-8")
    else:
        return ""

@app.route('/')
def health_check():
    return "Service is running."

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        file = request.files['file']
        persona = request.form['persona']
        stage = request.form['stage']
        content = extract_text(file)

        if not content:
            return jsonify({'error': 'No content extracted from file.'}), 400

        prompt = f"""
You are an expert B2B content evaluator. Analyze the following content using the eight criteria below. For each category, provide:
1. A numeric score from 1 to 5
2. A brief reason for the score
3. One actionable recommendation to improve it

Persona: {persona}
Buyer Journey Stage: {stage}

Criteria:
- Clarity & Structure
- Audience Relevance
- Value & Insight
- Call to Action
- Brand Voice & Tone
- SEO & Discoverability
- Visual/Design Integration
- Performance Readiness

Content:
\"\"\"
{content}
\"\"\"
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        result = response.choices[0].message.content.strip()
        return jsonify({'analysis': result})

    except Exception as e:
        error_trace = traceback.format_exc()
        print("🔥 ERROR:", error_trace)
        return jsonify({'error': 'Internal server error', 'details': error_trace}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)