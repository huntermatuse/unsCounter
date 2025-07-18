FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    paho-mqtt \
    flask \
    requests

COPY . .

RUN mkdir -p templates

RUN if [ ! -f config.json ]; then \
    echo '{"broker": "mosquitto", "port": 1883, "client_id": "multi_line_sim", "random_seed": 42, "lines": {"1": 1, "2": 2, "3": 3, "4": 4}, "tick_time": 1, "failure_probability": 0.1, "failure_status_min": 4, "failure_status_max": 6, "failure_duration_min": 30, "failure_duration_max": 120}' > config.json; \
    fi

EXPOSE 19033

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:19033/status || exit 1

CMD ["python", "app.py"]