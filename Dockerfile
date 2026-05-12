FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir grpcio grpcio-tools

EXPOSE 8000

CMD ["python", "server.py"]