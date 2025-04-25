FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Install system dependencies (for pyppeteer/chromium)
RUN apt-get update && \
    apt-get install -y wget gnupg2 curl unzip fonts-liberation libnss3 libatk-bridge2.0-0 libgtk-3-0 libxss1 libasound2 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libpangocairo-1.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

ENV PYTHONPATH=/app

EXPOSE 1102

CMD ["python", "src/main.py"]