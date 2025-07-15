FROM python:3.11-slim

WORKDIR /app

COPY run.sh /app/run.sh
COPY nslookup_monitor.py /app/nslookup_monitor.py
COPY urls.txt /app/urls.txt
COPY ip_store.json /app/ip_store.json

RUN RUN pip install requests && chmod +x /app/run.sh

CMD ["python3", "/app/nslookup_monitor.py"]
