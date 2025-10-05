FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create directory for SSH keys and logs
RUN mkdir -p /app/logs /app/.ssh

# Set permissions
RUN chmod 700 /app/.ssh

# Expose the port the MCP server will listen on
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app/src
ENV LOG_DIR=/app/logs

# Run the MCP server
CMD ["python", "src/mongodb_mcp_server.py"]