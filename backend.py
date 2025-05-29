from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import traceback

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def health_check():
    return "Service is running."

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        file = request.files['file']
        persona = request.form.get("persona")
        stage = request.form.get("stage")

        content = file.read().decode('utf-8')

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
{content}
"""

        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        analysis = completion.choices[0].message.content
        return jsonify({"analysis": analysis})

    except Exception as e:
        error_trace = traceback.format_exc()
        print("🔥 ERROR:", error_trace)
        return jsonify({'error': 'Internal server error', 'details': error_trace}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)