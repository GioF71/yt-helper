FROM python:3.9-slim

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install wheel
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get update && \
    apt-get -y install --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

ENV PUID ""
ENV PGID ""

ENV PYTHONUNBUFFERED "1"

ENV OUTPUT_PATH "/downloads"

ENV PLAYLIST_LIST ""
ENV CHANNEL_NAME_LIST ""
ENV MAX_RESOLUTION ""
ENV FILE_NAME_TEMPLATE ""
ENV ENABLE_LOOP ""
ENV LOOP_WAIT_SEC ""
ENV OUTPUT_FORMAT ""
ENV SLUGIFY ""
ENV PRINTABLE ""
ENV DIRECTORY_PER_CHANNEL ""

VOLUME /db
VOLUME /downloads

RUN mkdir /app/code
COPY yt-helper/*.py /app/code/

RUN mkdir /app/bin
COPY bin/run.sh /app/bin
RUN chmod 755 /app/bin/run.sh

ENTRYPOINT [ "/app/bin/run.sh" ]
