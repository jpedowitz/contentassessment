from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import fitz  # PyMuPDF
import docx2txt
import traceback

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

RUBRIC_CATEGORIES = [
    "Clarity & Structure",
    "Audience Relevance",
    "Value & Insight",
    "Call to Action",
    "Brand Voice & Tone",
    "SEO & Discoverability",
    "Visual/Design Integration",
    "Performance Readiness"
]

@app.route('/')
def health_check():
    return "Service is running."

def extract_text(file):
    filename = file.filename
    if filename.endswith(".pdf"):
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in pdf])
    elif filename.endswith(".docx"):
        return docx2txt.process(file)
    elif filename.endswith(".txt"):
        return file.read().decode("utf-8")
    else:
        return ""

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        file = request.files['file']
        persona = request.form['persona']
        stage = request.form['stage']

        content = extract_text(file)
        if not content.strip():
            return jsonify({'error': 'No readable content extracted.'}), 400

        system_prompt = f"""
You are an expert B2B content evaluator. Analyze the following content using the eight criteria below.
For each category, provide:
1. A numeric score from 1 to 5
2. A brief reason for the score
3. One actionable recommendation to improve it

End your response with a JSON block like this:
"overall_score": average score from all 8 categories
"scores": {{"Category Name": score, ...}}

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
{content[:6000]}
        """

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
            ]
        )

        result_text = response.choices[0].message.content
        return jsonify({'analysis': result_text})

    except Exception as e:
        error_trace = traceback.format_exc()
        print("🔥 ERROR:", error_trace)
        return jsonify({'error': 'Internal server error', 'details': error_trace}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
