# Background Removal Service

Python-based background removal service using rembg library.

## Features

- High-quality background removal using ML models
- Multiple model options (u2net, u2netp, u2net_human_seg, etc.)
- Alpha matting support for better edge quality
- CORS enabled for cross-origin requests
- Deployed on Railway

## Deployment

### Railway

1. Create a new project on Railway
2. Connect this directory (python-functions) as the source
3. Railway will auto-detect Python and use the configurations
4. Set environment variables if needed
5. Deploy!

### Environment Variables

- `PORT` - Port to run the service (default: 8080, Railway sets this automatically)

## API Endpoints

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "rembg_available": true
}
```

### POST /remove-bg

Remove background from an image.

**Request Body:**
```json
{
  "image": "data:image/png;base64,iVBORw0KG...",
  "model": "u2net",
  "alpha_matting": false,
  "alpha_matting_foreground_threshold": 240,
  "alpha_matting_background_threshold": 10
}
```

**Response:**
Returns PNG image with transparent background.

## Available Models

- `u2net` - Universal model (recommended, best balance)
- `u2netp` - Lightweight and faster
- `u2net_human_seg` - Best for portraits and people
- `u2net_cloth_seg` - Best for clothing and fashion
- `isnet-general-use` - High quality general purpose (slower)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py

# Or with gunicorn
gunicorn main:app --bind 0.0.0.0:8080
```

## Testing

```bash
curl -X POST http://localhost:8080/remove-bg \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/png;base64,..."}'
```
