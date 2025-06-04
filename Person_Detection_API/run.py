import torch
from transformers import AutoModelForObjectDetection, AutoImageProcessor
from ultralytics import YOLO
from PIL import Image as PILImage
import numpy as np
import json
from flask import Flask, request, jsonify
import tempfile
import os
import sys
import logging
from detect_persons import *

# Suppress Flask development server warning
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *args, **kwargs: None

app = Flask(__name__)

# ==== קבועים לסף ====
IOU_THRESHOLD = 0.5
CONFIDENCE_THRESHOLD = 0.5

@app.route('/detect_persons', methods=['POST'])
def handle_request():
    try:
        print("Request received")
        print(f"Files in request: {list(request.files.keys())}")
        
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400

        file = request.files['image']
        filename = file.filename
        print(f"Filename: {filename}")
        
        if not filename:
            return jsonify({"error": "Empty filename"}), 400
            
        ext = os.path.splitext(filename)[1].lower()
        print(f"File extension: {ext}")
        
        if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']:
            return jsonify({"error": f"Unsupported file extension: {ext}"}), 400

        # שמירה זמנית של הקובץ עם סיומת
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
            file.save(temp.name)
            temp_path = temp.name
            print(f"Saved to temporary file: {temp_path}")

        # בדיקה האם הקובץ הוא תמונה תקינה
        try:
            img = PILImage.open(temp_path)
            img.verify()  # יוודא שזה קובץ תמונה תקין
            print(f"Image verified: {img.format}, {img.size}")
        except Exception as e:
            os.unlink(temp_path)
            return jsonify({"error": f"Invalid image file: {e}"}), 400

        # הרצת הלוגיקה
        print("Running detection...")
        result = get_persons_bounding_box(temp_path)
        print(f"Detection result: {result}")

        os.unlink(temp_path)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
