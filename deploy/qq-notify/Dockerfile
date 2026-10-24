FROM python:3.12-slim
WORKDIR /app
COPY tests/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY scripts/notify-dev.py /app/notify-dev.py
COPY scripts/dev-report-gate.py /app/dev-report-gate.py
ENTRYPOINT ["python", "/app/notify-dev.py"]
