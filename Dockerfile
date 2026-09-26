FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x ./entrypoint.sh && \
    sed -i 's/\r$//' ./entrypoint.sh

# 5000 for FastAPI, 8000 for Streamlit
EXPOSE 5000 8000

ENTRYPOINT ["./entrypoint.sh"]
