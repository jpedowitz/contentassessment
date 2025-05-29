from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import fitz  # PyMuPDF
import docx2txt
import traceback

app = Flask(__name__)
CORS(app)

# Set your OpenAI API key securely
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(file_stream):
    text = ""
    with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_stream):
    with open("temp.docx", "wb") as f:
        f.write(file_stream.read())
    text = docx2txt.process("temp.docx")
    os.remove("temp.docx")
    return text

@app.route('/')
def health_check():
    return "Service is running."

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        file = request.files['file']
        persona = request.form.get('persona', 'General')
        stage = request.form.get('stage', 'Unaware')

        filename = file.filename.lower()
        if filename.endswith('.pdf'):
            content = extract_text_from_pdf(file.stream)
        elif filename.endswith('.docx'):
            content = extract_text_from_docx(file.stream)
        elif filename.endswith('.txt'):
            content = file.read().decode('utf-8', errors='ignore')
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        safe_content = content[:6000]  # Stay within token limits

        prompt = f"""
You are an expert B2B content evaluator. Analyze the following marketing content written for a {persona} in the "{stage}" stage of the buyer journey.

Content:
\"\"\"
{safe_content}
\"\"\"

Evaluate across 8 criteria:
1. Clarity & Structure
2. Audience Relevance
3. Value & Insight
4. Call to Action
5. Brand Voice & Tone
6. SEO & Discoverability
7. Visual/Design Integration
8. Performance Readiness

For each, provide:
- A numeric score from 1 to 5
- A brief reason for the score
- One actionable recommendation
"""

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a content assessment expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        result = response.choices[0].message.content
        return jsonify({'analysis': result})

    except Exception as e:
        error_trace = traceback.format_exc()
        print("🔥 ERROR:", error_trace)
        return jsonify({'error': 'Internal server error', 'details': error_trace}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)