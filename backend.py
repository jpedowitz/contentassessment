import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Route to test if service is live
@app.route('/')
def home():
    return "Content Assessment API is live."

# Analyze uploaded file
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        filename = secure_filename(file.filename)
        content_bytes = file.read()

        # Try decoding with UTF-8 first, fallback to Latin-1
        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            content = content_bytes.decode('latin-1')

        persona = request.form.get('persona', 'Default Persona')
        stage = request.form.get('stage', 'Awareness')

        prompt = f"""
You are an expert marketing evaluator. Assess the following content based on its clarity, engagement, effectiveness, and alignment to the buyer's journey stage ({stage}) and intended persona ({persona}). 
Grade it across the following dimensions: Message Clarity, Relevance, Persuasiveness, CTA Effectiveness, Emotional Appeal, and Visual/Format Quality. 
Provide:
1. A score from 1 to 10 for each dimension.
2. Specific reasoning for each score.
3. Three tactical recommendations to improve the content.

Here is the content:

{content}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )

        analysis = response.choices[0].message.content.strip()

        return jsonify({'analysis': analysis})

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)