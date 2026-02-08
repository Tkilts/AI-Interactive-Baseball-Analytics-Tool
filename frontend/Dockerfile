# frontend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend source code
COPY . .

CMD ["streamlit", "run", "app.py", "--server.enableCORS", "false", "--server.port", "8501"]