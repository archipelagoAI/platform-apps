FROM python:3.11-slim

WORKDIR /app

# Copy application code and dependencies files
COPY pyproject.toml README.md ./
COPY argocd_mcp_server/ ./argocd_mcp_server/

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Run the server
CMD ["python", "-m", "argocd_mcp_server"]
