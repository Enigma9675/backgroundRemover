# Rembg Background Removal API - Render Free Tier
# Optimized for memory constraints (512MB RAM on free tier)

FROM python:3.11-slim

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements-render.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the u2net model (smaller, works on free tier)
# BiRefNet is too large for 512MB RAM
RUN python -c "from rembg import new_session; new_session('u2net')"

# Copy application code
COPY app.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Render uses PORT env variable
ENV PORT=10000
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run with gunicorn - single worker to save memory
CMD gunicorn --bind 0.0.0.0:${PORT} --workers 1 --timeout 300 --keep-alive 5 app:app
