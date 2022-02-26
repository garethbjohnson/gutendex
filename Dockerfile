FROM python:3.10

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client rsync\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .
RUN mv wait-for /bin/wait-for
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
