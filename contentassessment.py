# backend.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import fitz  # PyMuPDF for PDFs
import docx2txt  # For DOCX files
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("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")  # Add your API key in .env or environment

def extract_text(file):
    filename = file.filename
    if filename.endswith('.pdf'):
        doc = fitz.open(stream=file.read(), filetype='pdf')
        return "\n".join([page.get_text() for page in doc])
    elif filename.endswith('.docx'):
        return docx2txt.process(file)
    elif filename.endswith('.txt'):
        return file.read().decode('utf-8')
    else:
        return ""

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files['file']
    persona = request.form['persona']
    stage = request.form['stage']
    content = extract_text(file)

    prompt = f"""You are an expert B2B content evaluator. Analyze the following content using the eight criteria below. For each category, provide:
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
{content[:7000]}"""  # truncate to fit token limits

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        temperature=0.3
    )

    return jsonify({
        "prompt": prompt,
        "result": response['choices'][0]['message']['content']
    })

if __name__ == '__main__':
    app.run(debug=True)