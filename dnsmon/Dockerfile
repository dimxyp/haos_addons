FROM python:3.11-slim

WORKDIR /app

COPY run.sh /app/run.sh
COPY requirements.txt /app/requirements.txt
COPY urls.txt /app/urls.txt
COPY ip_store.json /app/ip_store.json

RUN pip install -r requirements.txt && chmod +x /app/run.sh

CMD ["/app/run.sh"]
