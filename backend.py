from flask import Flask, request, jsonify, send_from_directory

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')