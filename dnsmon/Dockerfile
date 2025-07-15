FROM python:3.11-slim

WORKDIR /app

COPY nslookup_monitor.py /app/nslookup_monitor.py
COPY ip_store.json /app/ip_store.json

RUN pip install requests

CMD ["python3", "/app/nslookup_monitor.py"]
