FROM python:2.7.13-alpine3.6

MAINTAINER Ravi Shankar <wafflespeanut@gmail.com>

WORKDIR /usr/src/app
COPY requirements.txt ./

RUN apk update
RUN apk add build-base python-dev py-pip jpeg-dev zlib-dev
ENV LIBRARY_PATH=/lib:/usr/lib
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

ENV PORT 5000
ENTRYPOINT ["python", "./app.py"]
