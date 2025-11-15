"""
Python-based background removal using rembg
This provides better quality than JavaScript libraries and is FREE!

Requirements:
    pip install rembg pillow

Models available:
    - u2net: Universal (default, best balance)
    - u2netp: Lightweight and faster
    - u2net_human_seg: Best for portraits/people
    - u2net_cloth_seg: Best for clothing/fashion
    - silueta: Good for general use
    - isnet-general-use: High quality general purpose
"""

from http.server import BaseHTTPRequestHandler
import json
import base64
from io import BytesIO
from PIL import Image

# Try to import rembg
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    print("WARNING: rembg not installed. Run: pip install rembg pillow")


class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set CORS headers for cross-origin requests"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        """Handle POST requests for background removal"""
        try:
            # Check if rembg is available
            if not REMBG_AVAILABLE:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                error = {
                    'error': 'rembg not installed',
                    'message': 'Please install: pip install rembg pillow'
                }
                self.wfile.write(json.dumps(error).encode())
                return

            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Get parameters
            image_data = data.get('image')  # Base64 encoded image
            model_name = data.get('model', 'u2net')  # Default model
            alpha_matting = data.get('alpha_matting', False)
            alpha_matting_foreground_threshold = data.get('alpha_matting_foreground_threshold', 240)
            alpha_matting_background_threshold = data.get('alpha_matting_background_threshold', 10)

            if not image_data:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self._set_cors_headers()
                self.end_headers()
                error = {'error': 'No image data provided'}
                self.wfile.write(json.dumps(error).encode())
                return

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
            output_bytes = output_buffer.getvalue()

            # Return PNG image
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(output_bytes)))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(output_bytes)

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._set_cors_headers()
            self.end_headers()
            error = {
                'error': 'Background removal failed',
                'message': str(e)
            }
            self.wfile.write(json.dumps(error).encode())
