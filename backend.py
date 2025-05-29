from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import fitz  # PyMuPDF
import docx

app = Flask(__name__)
CORS(app)

# Use environment variable for key security
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files["file"]
        persona = request.form["persona"]
        stage = request.form["stage"]
        filename = file.filename.lower()

        if filename.endswith(".txt"):
            content = file.read().decode("utf-8", errors="ignore")
        elif filename.endswith(".pdf"):
            doc = fitz.open(stream=file.read(), filetype="pdf")
            content = "\n".join([page.get_text() for page in doc])
        elif filename.endswith(".docx"):
            doc = docx.Document(file)
            content = "\n".join([para.text for para in doc.paragraphs])
        else:
            return jsonify({"error": "Unsupported file type", "details": filename}), 400

        prompt = f"""You are a content marketing expert. Assess the uploaded content for how well it aligns with the persona '{persona}' and the buying journey stage '{stage}'.

Score the content (1–10) based on:
1. Relevance to persona
2. Stage alignment
3. Clarity
4. Persuasiveness
5. Actionability

Then, explain the reasoning behind each score and offer 3 concrete suggestions for improvement.

Content to assess:
\"\"\"
{content[:3000]}  # capped to avoid token limits
\"\"\"
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )

        analysis = response.choices[0].message.content.strip()

        return jsonify({"analysis": analysis})

    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# 🔌 Ensure Flask runs on the correct port in Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)