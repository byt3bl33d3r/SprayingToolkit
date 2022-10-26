FROM python:3.8.0-alpine3.10

RUN mkdir /spraying && \
    apk add cmake make libtool gcc musl-dev libffi-dev g++ libxml2 libxml2-dev libxslt libxslt-dev openssl openssl-dev

COPY . /spraying

RUN pip install -r /spraying/requirements.txt
