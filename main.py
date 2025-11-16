"""
Background removal service using rembg
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import base64
from io import BytesIO
from PIL import Image
import os

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'service': 'background-removal',
        'rembg_available': REMBG_AVAILABLE
    })

@app.route('/remove-bg', methods=['POST', 'OPTIONS'])
def remove_background():
    if request.method == 'OPTIONS':
        return '', 200
    
    if not REMBG_AVAILABLE:
        return jsonify({
            'error': 'rembg not installed',
            'message': 'Please install: pip install rembg pillow'
        }), 500
    
    try:
        data = request.get_json()
        image_data = data.get('image')
        model_name = data.get('model', 'u2net')
        alpha_matting = data.get('alpha_matting', False)
        alpha_matting_foreground_threshold = data.get('alpha_matting_foreground_threshold', 240)
        alpha_matting_background_threshold = data.get('alpha_matting_background_threshold', 10)
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        if image_data.startswith('data:'):
            image_data = image_data.split(',', 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        input_image = Image.open(BytesIO(image_bytes))
        
        output_image = remove(
            input_image,
            model_name=model_name,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold,
        )
        
        output_buffer = BytesIO()
        output_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        
        return send_file(output_buffer, mimetype='image/png', as_attachment=False)
        
    except Exception as e:
        return jsonify({'error': 'Background removal failed', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
