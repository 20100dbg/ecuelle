FROM debian:13.6-slim

RUN apt-get update && \
    apt-get install nano nginx python3 python3-pip python3-venv \
    -y --allow-unauthenticated --no-install-recommends

RUN mkdir -p /app/src
WORKDIR /app
COPY conf/gunicorn.conf /etc/nginx/sites-available/gunicorn
COPY conf/entrypoint.sh .
COPY ./requirements.txt .

RUN python3 -m venv .venv && \
    . .venv/bin/activate && \
    pip install -r requirements.txt

RUN ln -s /etc/nginx/sites-available/gunicorn /etc/nginx/sites-enabled

COPY ./src /app/src
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]