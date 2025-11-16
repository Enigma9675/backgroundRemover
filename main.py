# main.py (replace your file with this whole version)
import os
import sys
import io
import base64
import tempfile
import traceback
import platform
from importlib import import_module

from flask import Flask, request, jsonify
from flask_cors import CORS

# --------- Cache location & model selection ----------
# Match the path used during build so the model is already present
os.environ.setdefault("U2NET_HOME", "/app/.u2net")

# Choose model via env: REMBG_MODEL=u2net or u2netp (default: u2netp for speed)
REMBG_MODEL = os.environ.get("REMBG_MODEL", "u2netp").strip()

# --------- Try to import rembg and create a session upfront ----------
REMBG_AVAILABLE = False
REMBG_SESSION = None

try:
    from rembg import remove, new_session
    REMBG_SESSION = new_session(REMBG_MODEL)
    REMBG_AVAILABLE = True
except Exception as _e:
    REMBG_AVAILABLE = False
    REMBG_SESSION = None

# Third-party libs used by endpoints
import requests
from PIL import Image

# Flask app
app = Flask(__name__)
CORS(app)

# Diagnostics helpers
def check_imports(pkgs):
    out = {}
    for name in pkgs:
        try:
            m = import_module(name)
            ver = getattr(m, '__version__', 'unknown')
            out[name] = {'ok': True, 'version': ver}
        except Exception as e:
            out[name] = {'ok': False, 'error': str(e)}
    return out

def disk_writable():
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
            f.write('ok')
        return True
    except Exception:
        return False

# Optional: warm up rembg (loads model into memory)
def _warmup():
    if REMBG_SESSION is None:
        return False
    try:
        # 1x1 transparent PNG to trigger the pipeline without payload
        tiny_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAnsB4hU1F1kAAAAASUVORK5CYII=")
        _ = remove(tiny_png, session=REMBG_SESSION)
        return True
    except Exception:
        return False

WARMED_UP = _warmup()

# Root health (simple)
@app.route('/', methods=['GET'])
def root_health():
    return jsonify({
        'service': 'background-removal',
        'status': 'ok',
        'rembg_available': REMBG_AVAILABLE
    })

# Detailed health
@app.route('/health', methods=['GET'])
def health():
    imports = check_imports(['flask', 'flask_cors', 'PIL', 'rembg', 'onnxruntime', 'numpy', 'gunicorn', 'requests'])
    info = {
        'service': 'background-removal',
        'status': 'healthy' if REMBG_AVAILABLE else 'degraded',
        'rembg_available': REMBG_AVAILABLE,
        'rembg_model': REMBG_MODEL,
        'warmed_up': WARMED_UP,
        'runtime': {
            'python': sys.version.split()[0],
            'platform': platform.platform(),
        },
        'imports': imports,
        'disk_writable': disk_writable(),
        'env': {
            'PORT': os.environ.get('PORT'),
            'U2NET_HOME': os.environ.get('U2NET_HOME'),
            'XDG_CACHE_HOME': os.environ.get('XDG_CACHE_HOME'),
            'PYTHONHASHSEED': os.environ.get('PYTHONHASHSEED'),
        }
    }
    return jsonify(info), (200 if REMBG_AVAILABLE else 206)

# Quick imports endpoint
@app.route('/debug/imports', methods=['GET'])
def debug_imports():
    return jsonify(check_imports(['flask', 'flask_cors', 'PIL', 'rembg', 'onnxruntime', 'numpy', 'gunicorn', 'requests']))

# Utilities for image loading
MAX_BYTES = 8 * 1024 * 1024  # 8MB safety

def _load_image_from_url(url: str) -> Image.Image:
    r = requests.get(url, timeout=15, stream=True)
    r.raise_for_status()
    content = r.content
    if len(content) > MAX_BYTES:
        raise ValueError(f"image too large ({len(content)} bytes > {MAX_BYTES})")
    return Image.open(io.BytesIO(content)).convert("RGBA")

def _load_image_from_data_url(data_url: str) -> Image.Image:
    try:
        header, b64 = data_url.split(',', 1)
        raw = base64.b64decode(b64)
    except Exception:
        raise ValueError("invalid data URL")
    if len(raw) > MAX_BYTES:
        raise ValueError(f"image too large ({len(raw)} bytes > {MAX_BYTES})")
    return Image.open(io.BytesIO(raw)).convert("RGBA")

# Main API
@app.route('/remove-bg', methods=['POST'])
def remove_bg():
    if REMBG_SESSION is None:
        return jsonify({
            'ok': False,
            'error': 'rembg_not_available',
            'message': 'rembg/onnxruntime failed to initialize on server'
        }), 500

    data = request.get_json(silent=True) or {}
    image_url = data.get('imageUrl')
    image_data = data.get('imageData')

    if not image_url and not image_data:
        return jsonify({'ok': False, 'error': 'bad_request', 'message': 'Provide imageUrl or imageData'}), 400

    try:
        if image_url:
            img = _load_image_from_url(image_url)
        else:
            img = _load_image_from_data_url(image_data)

        buf_in = io.BytesIO()
        img.save(buf_in, format='PNG')
        buf_in.seek(0)

        out_bytes = remove(buf_in.getvalue(), session=REMBG_SESSION)

        return jsonify({
            'ok': True,
            'contentType': 'image/png',
            'data': base64.b64encode(out_bytes).decode('ascii')
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'ok': False, 'error': 'fetch_failed', 'message': str(e)}), 400
    except ValueError as e:
        return jsonify({'ok': False, 'error': 'validation', 'message': str(e)}), 400
    except Exception as e:
        print('remove-bg error:', traceback.format_exc(), flush=True)
        return jsonify({'ok': False, 'error': 'processing_failed', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    app.run(host='0.0.0.0', port=port)
