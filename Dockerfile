FROM python:3.9-slim
ARG APT_PROXY

RUN echo $APT_PROXY

RUN if [ -n "${APT_PROXY}" ]; then \
        echo "Builind using apt proxy"; \
        echo "Acquire::http::proxy \"${APT_PROXY}\";" >> /etc/apt/apt.conf.d/01-apt-proxy; \
        echo "Acquire::https::proxy \"DIRECT\";" >> /etc/apt/apt.conf.d/01-apt-proxy; \
        cat /etc/apt/apt.conf.d/01-apt-proxy; \
    else \
        echo "Building without apt proxy"; \
    fi

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN apt-get update && \
    apt-get -y install --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

RUN if [ -n "${APT_PROXY}" = "Y" ]; then \
        rm /etc/apt/apt.conf.d/01-apt-proxy; \
    fi

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
