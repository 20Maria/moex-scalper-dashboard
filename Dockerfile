FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY scalper-dashboard.html .
COPY shared.css .
COPY demo.html .
COPY test-api.html .

EXPOSE 8081

CMD ["python", "server.py"]
