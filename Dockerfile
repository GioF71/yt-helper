FROM python:3.9-slim

RUN apt-get update && \
    apt-get -y install --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

ENV PUID ""
ENV PGID ""

ENV PLAYLIST_LIST ""
ENV CHANNEL_NAME_LIST ""
ENV MAX_RESOLUTION "1080"
ENV SUBTYPE "mp4"
ENV OUTPUT_PATH "/downloads"
ENV FILE_NAME_TEMPLATE "%(uploader)s - %(upload_date>%Y-%m-%d)s - %(title)s.%(ext)s"
ENV ENABLE_LOOP "1"
ENV LOOP_WAIT_SEC "300"
ENV OUTPUT_FORMAT "mp4"
ENV SLUGIFY "0"
ENV PRINTABLE "1"
ENV DIRECTORY_PER_CHANNEL "0"

ENV PYTHONUNBUFFERED=1

VOLUME /db
VOLUME /downloads

RUN mkdir /app/code
COPY yt-helper/*.py /app/code/

RUN mkdir /app/bin
COPY bin/run.sh /app/bin
RUN chmod 755 /app/bin/run.sh

ENTRYPOINT [ "/app/bin/run.sh" ]
