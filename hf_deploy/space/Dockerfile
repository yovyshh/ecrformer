FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HF_HOME=/home/user/app/.cache/huggingface \
    TORCH_THREADS=2 \
    PORT=7860

# Install minimal OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create user with UID 1000 for Hugging Face Spaces compatibility
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY --chown=user:user . /home/user/app

# Set up cache directory permissions
RUN mkdir -p /home/user/app/.cache/huggingface && \
    chown -R user:user /home/user/app

USER user

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]

