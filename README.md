# Rembg Background Removal API Server

A Flask API for removing backgrounds from images using rembg with BiRefNet model.
Designed for deployment on Oracle Cloud.

## Quick Start (Local Testing)

```bash
# Install dependencies
pip install -r requirements-cpu.txt

# Run the server
python app.py
```

The server will be available at `http://localhost:5000`

## API Endpoints

### POST /remove-bg
Remove background from an image.

**Request body (JSON):**
```json
{
  "imageData": "data:image/jpeg;base64,...",  // OR
  "imageUrl": "https://example.com/image.jpg",
  "alpha_matting": true,
  "return_format": "base64"  // or "binary"
}
```

**Response:**
```json
{
  "success": true,
  "dataUrl": "data:image/png;base64,...",
  "originalSize": [1920, 1080],
  "processedSize": [1920, 1080],
  "processingTime": 2.45
}
```

### GET /health
Health check endpoint.

### GET /models
List available models.

## Oracle Cloud Deployment

### Option 1: GPU Instance (Recommended)

Oracle Cloud offers free tier GPU instances that work great for this:

1. **Create a GPU compute instance:**
   - Shape: VM.GPU.A10.1 or similar
   - Image: Oracle Linux 8 with CUDA

2. **SSH into your instance and install Docker:**
   ```bash
   sudo dnf install -y docker
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker $USER
   ```

3. **Install NVIDIA Container Toolkit:**
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo | \
     sudo tee /etc/yum.repos.d/nvidia-docker.repo
   sudo dnf install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

4. **Copy files and build:**
   ```bash
   scp -r rembg-server/ ubuntu@your-oracle-ip:~/
   ssh ubuntu@your-oracle-ip
   cd rembg-server
   docker build -t rembg-api .
   ```

5. **Run the container:**
   ```bash
   docker run -d \
     --gpus all \
     -p 5000:5000 \
     --restart unless-stopped \
     --name rembg-api \
     rembg-api
   ```

### Option 2: CPU Instance

For CPU-only instances (slower but still works):

```bash
# Build with CPU Dockerfile
docker build -f Dockerfile.cpu -t rembg-api-cpu .

# Run
docker run -d \
  -p 5000:5000 \
  --restart unless-stopped \
  --name rembg-api \
  rembg-api-cpu
```

### Option 3: Direct Installation (No Docker)

```bash
# Install Python 3.11
sudo dnf install python3.11 python3.11-pip

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-cpu.txt  # or requirements.txt for GPU

# Run with gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 300 app:app
```

### Firewall Configuration

Open port 5000 in Oracle Cloud:

1. Go to your instance's VCN
2. Add an ingress rule:
   - Source: 0.0.0.0/0
   - Protocol: TCP
   - Destination Port: 5000

Also open the port on the instance:
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### Set Up Nginx Reverse Proxy (Optional)

For HTTPS support:

```bash
sudo dnf install nginx certbot python3-certbot-nginx

# Configure nginx
sudo cat > /etc/nginx/conf.d/rembg.conf << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
        client_max_body_size 50M;
    }
}
EOF

sudo systemctl start nginx
sudo systemctl enable nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Server port |
| `REMBG_MODEL` | birefnet-general | Model to use |
| `MAX_IMAGE_SIZE` | 4096 | Max image dimension |
| `DEBUG` | false | Enable debug mode |
| `ALLOWED_ORIGINS` | * | CORS allowed origins |

## Performance Notes

- **GPU (A10/T4):** ~1-2 seconds per image
- **CPU (4 cores):** ~15-30 seconds per image
- First request may be slower due to model warm-up

## Testing

```bash
# Test with curl
curl -X POST http://localhost:5000/remove-bg \
  -H "Content-Type: application/json" \
  -d '{"imageUrl": "https://example.com/photo.jpg"}' \
  -o response.json

# Health check
curl http://localhost:5000/health
```
