FROM alpine:3.19


RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    sudo

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

ENV PYTHONPATH=/app/src/:$PYTHONPATH

RUN adduser -D appuser && \
    echo "appuser:appuser" | chpasswd && \
    echo "appuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app


USER appuser

ENV SHELL=/bin/bash
ENV TERM=xterm-256color


CMD ["/bin/bash", "-l"]
