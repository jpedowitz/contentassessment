from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/')
def health_check():
    return "Service is running."

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        print("📥 Incoming request to /analyze")

        # Log incoming request data
        data = request.get_json()
        print("📄 Request JSON:", data)

        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise Exception("OpenAI API key missing.")

        content = data.get('content')
        persona = data.get('persona', 'CMO')
        stage = data.get('stage', 'adoption')

        if not content:
            raise ValueError("Missing 'content' in request.")

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

        print("🧠 Sending prompt to OpenAI...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        result = response.choices[0].message['content']
        print("✅ OpenAI response received")
        return jsonify({'analysis': result})

    except Exception as e:
        error_trace = traceback.format_exc()
        print("🔥 ERROR:", error_trace)
        return jsonify({'error': 'Internal server error', 'details': error_trace}), 500