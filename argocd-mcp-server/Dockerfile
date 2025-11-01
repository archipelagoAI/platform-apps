FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY argocd_mcp_server/ ./argocd_mcp_server/

# Run the server
CMD ["python", "-m", "argocd_mcp_server"]
