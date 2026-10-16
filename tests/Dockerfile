FROM debian:13.6-slim

RUN apt-get update && \
    apt-get install python3 python3-pip python3-venv python3-dev \
    php php-mysql \
    mariadb-client-compat postgresql-client default-libmysqlclient-dev \
    nano bash curl build-essential pkg-config gpg \
    -y --allow-unauthenticated --no-install-recommends

RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --batch --yes --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    curl -fsSL https://packages.microsoft.com/config/ubuntu/24.04/prod.list | tee /etc/apt/sources.list.d/mssql-release.list

RUN apt update && \
    ACCEPT_EULA=Y \
    apt install mssql-tools18 unixodbc-dev \
    -y --allow-unauthenticated --no-install-recommends && \
    echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc


RUN mkdir -p /app/sql
WORKDIR /app

COPY tests/requirements.txt .

RUN python3 -m venv .venv && \
    . .venv/bin/activate && \
    pip install -r requirements.txt

COPY tests/entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

COPY tests/src/ .

CMD ["/app/entrypoint.sh"]