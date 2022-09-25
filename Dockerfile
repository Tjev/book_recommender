
# syntax=docker/dockerfile:1

FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY book_rec ./book_rec

COPY main.py main.py

CMD ["streamlit", "run", "main.py"]

EXPOSE 8501