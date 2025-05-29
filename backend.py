import os
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
from PyPDF2 import PdfReader
import docx
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(file_stream):
    try:
        reader = PdfReader(file_stream)
        return "\n".join([page.extract_text() or '' for page in reader.pages])
    except:
        return ""

def extract_text_from_docx(file_stream):
    try:
        doc = docx.Document(file_stream)
        return "\n".join([para.text for para in doc.paragraphs])
    except:
        return ""

def summarize_insights(text, persona, stage):
    rubric = [
        "Clarity & Structure",
        "Audience Relevance",
        "Value & Insight",
        "Call to Action",
        "Brand Voice & Tone",
        "SEO & Discoverability",
        "Visual/Design Integration",
        "Performance Readiness"
    ]

    prompt = f"""
You are a marketing content evaluator. Assess the following content based on 8 criteria. 
For each criterion, provide a score from 1 to 5, a brief reason, and a recommendation for improvement. 
End with a total score. The content is targeted at a {persona} in the {stage} stage of their buying journey.

Criteria:
1. Clarity & Structure
2. Audience Relevance
3. Value & Insight
4. Call to Action
5. Brand Voice & Tone
6. SEO & Discoverability
7. Visual/Design Integration
8. Performance Readiness

Content:
{text[:5000]}  # Truncate to stay under token limits
"""

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    return response.choices[0].message.content.strip()

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    persona = request.form.get('persona', 'General')
    stage = request.form.get('stage', 'Unaware')

    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    filename = file.filename.lower()
    if filename.endswith('.pdf'):
        content = extract_text_from_pdf(file)
    elif filename.endswith('.docx'):
        content = extract_text_from_docx(file)
    elif filename.endswith('.txt'):
        content = file.read().decode('utf-8', errors='ignore')
    else:
        return jsonify({'error': 'Unsupported file format'}), 400

    try:
        feedback = summarize_insights(content, persona, stage)

        scores = []
        total = 0
        for section in feedback.split("\n\n"):
            lines = section.strip().split("\n")
            if len(lines) >= 3 and "Score:" in lines[0]:
                label = lines[0].split("Score:")[0].strip("12345678. ").strip()
                score = int(lines[0].split("Score:")[1].strip())
                reason = lines[1].replace("Reason:", "").strip()
                recommendation = lines[2].replace("Recommendation:", "").strip()
                scores.append({
                    "label": label,
                    "score": score,
                    "reason": reason,
                    "recommendation": recommendation
                })
                total += score

        return jsonify({"scores": scores, "overall_score": total})

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)