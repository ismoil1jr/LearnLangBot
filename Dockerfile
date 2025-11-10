FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# git va boshqa kerakli paketlar
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["python", "main.py"]
