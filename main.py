"""
Background removal service using rembg
Deployed on Railway for better size limits
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import base64
from io import BytesIO
from PIL import Image
import os

# Try to import rembg
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    print("WARNING: rembg not installed. Run: pip install rembg pillow")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'background-removal',
        'rembg_available': REMBG_AVAILABLE
    })

@app.route('/remove-bg', methods=['POST', 'OPTIONS'])
def remove_background():
    """Remove background from image"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    # Check if rembg is available
    if not REMBG_AVAILABLE:
        return jsonify({
            'error': 'rembg not installed',
            'message': 'Please install: pip install rembg pillow'
        }), 500
    
    try:
        # Get JSON data
        data = request.get_json()
        
        # Get parameters
        image_data = data.get('image')  # Base64 encoded image
        model_name = data.get('model', 'u2net')  # Default model
        alpha_matting = data.get('alpha_matting', False)
        alpha_matting_foreground_threshold = data.get('alpha_matting_foreground_threshold', 240)
        alpha_matting_background_threshold = data.get('alpha_matting_background_threshold', 10)
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64 image
        # Handle data URLs (data:image/png;base64,...)
        if image_data.startswith('data:'):
            image_data = image_data.split(',', 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        input_image = Image.open(BytesIO(image_bytes))
        
        # Remove background
        output_image = remove(
            input_image,
            model_name=model_name,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold,
        )
        
        # Convert to PNG bytes
        output_buffer = BytesIO()
        output_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        
        # Return PNG image
        return send_file(
            output_buffer,
            mimetype='image/png',
            as_attachment=False
        )
        
    except Exception as e:
        return jsonify({
            'error': 'Background removal failed',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
