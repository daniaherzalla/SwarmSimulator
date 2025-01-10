FROM python:3.6-buster
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -qy xorg --no-install-recommends --no-install-suggests && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
WORKDIR /tmp
COPY requirements.txt .
RUN pip install -r requirements.txt
WORKDIR /app
COPY swarm /app/

ENTRYPOINT ["python"]
CMD ["-m", "main"]
