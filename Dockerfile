FROM python:3.10

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client rsync\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000
ENTRYPOINT ["./docker/entrypoint.sh"]
