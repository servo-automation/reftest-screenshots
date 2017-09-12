FROM python:2.7.13-jessie

MAINTAINER Ravi Shankar <wafflespeanut@gmail.com>

WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y xvfb chromedriver && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

ENV PATH=$PATH:/usr/lib/chromium
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

ENV PORT 5000
EXPOSE 5000

ENTRYPOINT ["python", "app.py"]
