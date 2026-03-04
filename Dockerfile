FROM python:3.11

RUN useradd -ms /bin/bash user
USER user
WORKDIR /home/user

COPY src .

ENTRYPOINT ["python", "proxy.py"]