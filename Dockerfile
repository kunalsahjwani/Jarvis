# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# TODO: You might want to add these environment variables if needed
# ENV PYTHONPATH=/app
# ENV PYTHONUNBUFFERED=1

# Expose the port that FastAPI will run on
EXPOSE 8000

# TODO: Change this command if you want different startup behavior
# Default command (can be overridden in docker-compose.yml)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]