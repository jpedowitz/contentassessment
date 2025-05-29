from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def health_check():
    return "Service is running."

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        content = data.get("content")
        persona = data.get("persona", "CMO")
        stage = data.get("stage", "adoption")

        if not content:
            return jsonify({"error": "No content provided"}), 400

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

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        analysis = response.choices[0].message["content"]
        return jsonify({"analysis": analysis})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)