FROM python:slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

RUN mkdir /code
COPY yt-helper/*.py /code/

VOLUME /config

WORKDIR /code

ENTRYPOINT [ "python3", "yt-helper.py" ]
