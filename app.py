#!/usr/bin/env python3
"""
Rembg Background Removal API Server

A Flask API for removing backgrounds from images using rembg with BiRefNet model.
Designed for deployment on Oracle Cloud with GPU support.

Usage:
    POST /remove-bg
    Body: JSON with base64 image data or image URL
    Returns: PNG image with transparent background
"""

import os
import io
import base64
import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
from rembg import remove, new_session
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
# Default to u2net for Render free tier (512MB RAM limit)
# Use birefnet-general for better quality if you have more RAM
MODEL_NAME = os.environ.get('REMBG_MODEL', 'u2net')
MAX_IMAGE_SIZE = int(os.environ.get('MAX_IMAGE_SIZE', 2048))  # Max dimension in pixels
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')

# Pre-load the model at startup for faster inference
print(f"Loading {MODEL_NAME} model...")
session = new_session(MODEL_NAME)
print(f"Model {MODEL_NAME} loaded successfully!")


def decode_base64_image(data_url_or_base64):
    """Decode a base64 string or data URL to PIL Image."""
    if data_url_or_base64.startswith('data:'):
        # Extract base64 from data URL
        header, encoded = data_url_or_base64.split(',', 1)
    else:
        encoded = data_url_or_base64

    image_data = base64.b64decode(encoded)
    return Image.open(io.BytesIO(image_data))


def fetch_image_from_url(url):
    """Fetch an image from a URL."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))


def resize_if_needed(image, max_size=MAX_IMAGE_SIZE):
    """Resize image if it exceeds max dimensions."""
    width, height = image.size
    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int((height / width) * max_size)
        else:
            new_height = max_size
            new_width = int((width / height) * max_size)
        image = image.resize((new_width, new_height), Image.LANCZOS)
    return image


def image_to_base64(image, format='PNG'):
    """Convert PIL Image to base64 data URL."""
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/{format.lower()};base64,{b64}"


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'model': MODEL_NAME,
        'max_image_size': MAX_IMAGE_SIZE
    })


@app.route('/remove-bg', methods=['POST'])
def remove_background():
    """
    Remove background from an image.

    Accepts JSON body with:
    - imageData: base64 encoded image or data URL
    - imageUrl: URL to fetch image from
    - alpha_matting: boolean (optional, default True)
    - return_format: 'base64' or 'binary' (optional, default 'base64')

    Returns:
    - JSON with dataUrl (base64) or binary PNG
    """
    start_time = time.time()

    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Get image from request
        image = None
        if 'imageData' in data:
            image = decode_base64_image(data['imageData'])
        elif 'imageUrl' in data:
            image = fetch_image_from_url(data['imageUrl'])
        else:
            return jsonify({'error': 'No image provided. Use imageData or imageUrl'}), 400

        # Ensure image is in RGB or RGBA mode
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA')

        # Resize if too large
        original_size = image.size
        image = resize_if_needed(image)

        # Get options
        alpha_matting = data.get('alpha_matting', True)
        return_format = data.get('return_format', 'base64')

        # Remove background
        output_image = remove(
            image,
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
        )

        elapsed = time.time() - start_time

        # Return result
        if return_format == 'binary':
            buffer = io.BytesIO()
            output_image.save(buffer, format='PNG')
            buffer.seek(0)
            return send_file(
                buffer,
                mimetype='image/png',
                as_attachment=False
            )
        else:
            # Return as base64 data URL
            data_url = image_to_base64(output_image)
            return jsonify({
                'success': True,
                'dataUrl': data_url,
                'originalSize': original_size,
                'processedSize': image.size,
                'processingTime': round(elapsed, 2)
            })

    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch image: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/models', methods=['GET'])
def list_models():
    """List available models."""
    return jsonify({
        'current': MODEL_NAME,
        'available': [
            {'name': 'u2net', 'description': 'Fast, good quality'},
            {'name': 'birefnet-general', 'description': 'Best quality, slower'},
            {'name': 'isnet-general-use', 'description': 'Good for general images'},
            {'name': 'u2net_human_seg', 'description': 'Optimized for humans'},
        ]
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    print(f"Starting Rembg API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
