FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies required by OpenCV, Ultralytics, and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch first to avoid multi-GB CUDA downloads on Render
RUN pip install --upgrade pip && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt

COPY . .

RUN sed -i 's/\r$//' /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh && \
    python manage.py collectstatic --noinput

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
