FROM python:3.11-slim

# Install Node.js and npm
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install MCP Gmail server globally
RUN npm install -g @peakmojo/mcp-server-headless-gmail

# Copy application code
COPY . .

# Create data directory for memory storage
RUN mkdir -p data/memory

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Start the application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]