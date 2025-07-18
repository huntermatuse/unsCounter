FROM python:3.11-slim

WORKDIR /app

RUN pip install paho-mqtt flask

COPY counter.py .
COPY app.py .

CMD ["python", "app.py"]