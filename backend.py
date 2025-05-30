import os
import io
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from PyPDF2 import PdfReader
import docx
import openai

# Set OpenAI API key (legacy style)
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

def extract_text_from_pdf(file_stream):
    try:
        reader = PdfReader(file_stream)
        return "\n".join([page.extract_text() or '' for page in reader.pages])
    except Exception as e:
        print(f"PDF extraction error: {e}", flush=True)
        return ""

def extract_text_from_docx(file_stream):
    try:
        doc = docx.Document(file_stream)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"DOCX extraction error: {e}", flush=True)
        return ""

def summarize_insights(text, persona, stage):
    prompt = f"""
You are an expert B2B marketing strategist evaluating content designed to influence a {persona} in the {stage} stage of the buying journey.

Analyze the content across the following 8 categories:
	1.	Clarity & Structure
	2.	Audience Relevance
	3.	Value & Insight
	4.	Call to Action
	5.	Brand Voice & Tone
	6.	SEO & Discoverability
	7.	Visual/Design Integration
	8.	Performance Readiness

For each category, return:
	•	A score (1–5)
	•	A short explanation of the rationale (why it earned that score)
	•	A specific recommendation to improve performance in that area

Important: Be concise but insightful. Avoid generic feedback. Tailor each suggestion to the content and persona. Use a structured JSON format as shown:

[
  {{
    "label": "Clarity & Structure",
    "score": 4,
    "reason": "The content is logically organized but has a few repetitive elements.",
    "recommendation": "Remove duplicate headings and improve transitions between sections."
  }},
  ...
]

Now evaluate this content:

{text[:5000]}
"""

    try:
        # Use legacy OpenAI API style
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"OpenAI API error: {e}", flush=True)
        return f"Error: {str(e)}"

def parse_response(feedback):
    """Parse the OpenAI response into structured data"""
    try:
        import json
        
        # First, try to parse as JSON directly
        try:
            scores = json.loads(feedback)
            if isinstance(scores, list) and all('label' in item and 'score' in item for item in scores):
                # Calculate total score
                total_score = sum(item.get('score', 0) for item in scores)
                print(f"Parsed {len(scores)} criteria with total score: {total_score}", flush=True)
                return scores, total_score
        except json.JSONDecodeError:
            print("Response is not valid JSON, trying text parsing...", flush=True)
        
        # Fallback to original text parsing method
        scores = []
        lines = feedback.split('\n')
        
        current_item = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for criterion lines (number. Name - Score: X)
            if ' - Score:' in line and any(char.isdigit() for char in line):
                # Save previous item if exists
                if current_item and 'label' in current_item:
                    scores.append(current_item)
                
                # Parse new item
                parts = line.split(' - Score:')
                if len(parts) == 2:
                    label = parts[0].strip()
                    # Remove number prefix (1. 2. etc.)
                    label = label.split('. ', 1)[-1] if '. ' in label else label
                    
                    try:
                        score = int(parts[1].strip())
                        current_item = {
                            'label': label,
                            'score': score,
                            'reason': '',
                            'recommendation': ''
                        }
                    except ValueError:
                        continue
            
            elif line.startswith('Reason:') and current_item:
                current_item['reason'] = line.replace('Reason:', '').strip()
            
            elif line.startswith('Recommendation:') and current_item:
                current_item['recommendation'] = line.replace('Recommendation:', '').strip()
        
        # Add the last item
        if current_item and 'label' in current_item:
            scores.append(current_item)
        
        # Calculate total score
        total_score = sum(item.get('score', 0) for item in scores)
        
        print(f"Parsed {len(scores)} criteria with total score: {total_score}", flush=True)
        
        return scores, total_score
    
    except Exception as e:
        print(f"Parsing error: {e}", flush=True)
        return [], 0

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        file = request.files.get('file')
        persona = request.form.get('persona', 'General')
        stage = request.form.get('stage', 'Unaware')

        print(f"=== ANALYSIS START: {persona} in {stage} stage ===", flush=True)

        if not file:
            return jsonify({'error': 'No file uploaded'}), 400

        filename = file.filename.lower()
        content = ""
        
        print(f"Processing file: {filename}", flush=True)
        
        if filename.endswith('.pdf'):
            content = extract_text_from_pdf(file)
        elif filename.endswith('.docx'):
            content = extract_text_from_docx(file)
        elif filename.endswith('.txt'):
            content = file.read().decode('utf-8', errors='ignore')
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        if not content.strip():
            return jsonify({'error': 'Could not extract text from file'}), 400

        print(f"Extracted {len(content)} characters from {filename}", flush=True)
        print(f"First 200 chars: {content[:200]}...", flush=True)

        # Get AI feedback
        print("=== CALLING OPENAI API ===", flush=True)
        feedback = summarize_insights(content, persona, stage)
        
        if feedback.startswith("Error:"):
            print(f"OpenAI Error: {feedback}", flush=True)
            return jsonify({'error': feedback}), 500
        
        print("=== RECEIVED AI RESPONSE ===", flush=True)
        print("Raw AI Response (first 500 chars):", flush=True)
        print(feedback[:500] + "..." if len(feedback) > 500 else feedback, flush=True)
        
        # Parse the response
        scores, total_score = parse_response(feedback)
        
        print(f"=== PARSED RESPONSE: {len(scores)} scores, total: {total_score} ===", flush=True)
        
        if not scores:
            # Return raw response for debugging
            print("No scores parsed, returning raw response", flush=True)
            return jsonify({
                'error': 'Could not parse AI response',
                'raw_response': feedback,
                'scores': [],
                'overall_score': 0
            })

        print("=== RETURNING SUCCESS ===", flush=True)
        return jsonify({
            "scores": scores,
            "overall_score": total_score
        })

    except Exception as e:
        print(f"=== ANALYSIS ERROR: {e} ===", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error', 
            'details': str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Content Assessment API is running', 'status': 'healthy'})

@app.route('/test', methods=['GET', 'POST'])
def test():
    """Test endpoint for debugging"""
    return jsonify({
        'message': 'Test endpoint working',
        'openai_key_set': bool(openai.api_key),
        'environment': os.environ.get('ENVIRONMENT', 'unknown')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting server on port {port}", flush=True)
    print(f"OpenAI API key set: {bool(openai.api_key)}", flush=True)
    app.run(host='0.0.0.0', port=port, debug=True)