FROM debian:13.0-slim

RUN apt-get update && \
    apt-get install nano nginx python3 python3-pip python3-venv \
    -y --allow-unauthenticated

RUN mkdir -p /app/src
COPY ./src /app/src
COPY ./conf /app
WORKDIR /app

RUN python3 -m venv .venv && \
    . .venv/bin/activate && \
    pip install -r requirements.txt

RUN mv "/app/gunicorn.conf" /etc/nginx/sites-available/gunicorn && \
    ln -s /etc/nginx/sites-available/gunicorn /etc/nginx/sites-enabled && \
    chmod +x "/app/gunicorn.sh"

EXPOSE 80

CMD service nginx start && /app/gunicorn.sh