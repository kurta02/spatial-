#!/usr/bin/env python3
"""
Simple Flask test to verify basic Flask functionality
"""

import sys
import os

# Add paths
sys.path.insert(0, '/home/kurt/spatial-ai')

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({"status": "working", "message": "Simple Flask test"})

if __name__ == "__main__":
    print("Starting simple Flask test on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=True)