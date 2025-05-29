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
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        text = ""
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif filename.endswith(".docx"):
        path = f"/tmp/{file.filename}"
        file.save(path)
        return docx2txt.process(path)
    elif filename.endswith(".txt"):
        return file.read().decode("utf-8")
    else:
        raise ValueError("Unsupported file type")

def build_prompt(content, persona, stage):
    categories = "\n".join([f"{i+1}. {cat}" for i, cat in enumerate(RUBRIC_CATEGORIES)])
    return f"""
You are an expert B2B content evaluator. Analyze the following content using the eight criteria below. For each category, provide:
1. A numeric score from 1 to 5
2. A brief reason for the score
3. One actionable recommendation to improve it

Persona: {persona}
Buyer Journey Stage: {stage}

Criteria:
{categories}

Content:
""" + content.strip()

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        file = request.files['file']
        persona = request.form['persona']
        stage = request.form['stage']

        content = extract_text(file)
        prompt = build_prompt(content, persona, stage)

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert B2B content evaluator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        reply = response.choices[0].message.content.strip()

        # Try to parse scores and structure
        result = []
        lines = reply.splitlines()
        current = {}
        overall_score = 0
        count = 0

        for line in lines:
            if any(cat in line for cat in RUBRIC_CATEGORIES):
                if current:
                    result.append(current)
                current = {"category": line.split("**")[1] if "**" in line else line.strip()}
            elif "Score:" in line:
                score = int(line.split(":")[1].strip())
                current['score'] = score
                overall_score += score
                count += 1
            elif "Reason:" in line:
                current['reason'] = line.split(":", 1)[1].strip()
            elif "Recommendation:" in line:
                current['recommendation'] = line.split(":", 1)[1].strip()
        if current:
            result.append(current)

        avg_score = round(overall_score / count, 2) if count else 0

        return jsonify({"overall_score": avg_score, "categories": result})

    except Exception as e:
        error_trace = traceback.format_exc()
        print("\U0001F525 ERROR:", error_trace)
        return jsonify({'error': 'Internal server error', 'details': error_trace}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)