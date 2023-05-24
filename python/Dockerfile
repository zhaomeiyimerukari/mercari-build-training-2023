FROM python:3.8-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

COPY main.py main.py

COPY db/mercari.sqlite3 /app/db/mercari.sqlite3

RUN pip install -r requirements.txt

VOLUME /db

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]


